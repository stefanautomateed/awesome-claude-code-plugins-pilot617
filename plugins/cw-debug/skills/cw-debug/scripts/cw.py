"""
Self-contained CloudWatch Logs Insights utility for /debug-prod investigations.

Usage from investigation scripts:

    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".claude/skills/debug-prod/scripts"))
    from cw import CWClient

    cw = CWClient(region="ca-central-1")
    results = cw.query(query_string, hours_back=168, log_group="/aws/...")
    cw.save(results, "01_recon_raw_logs")

Or via CLI:

    .venv/bin/python .claude/skills/debug-prod/scripts/cw.py \\
        --region ca-central-1 \\
        --log-group /aws/containerinsights/.../voice-flask-backend \\
        --hours 168 \\
        --query "fields @timestamp, @message | limit 25" \\
        --save 01_recon_raw_logs
"""

import argparse
import csv
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

import boto3

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_REGION = "us-east-2"
DEFAULT_LIMIT = 1000
POLL_INTERVAL_SECONDS = 2
INVESTIGATIONS_DIR = "investigations"


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class CWClient:
    """Stateful CloudWatch Logs Insights client."""

    def __init__(self, region=DEFAULT_REGION, client=None):
        self.region = region
        self._client = client or boto3.client("logs", region_name=region)

    # ----- core query -----

    def query(
        self,
        query_string,
        hours_back,
        log_group,
        end_hours_back=None,
        limit=DEFAULT_LIMIT,
        timeout_seconds=300,
    ):
        """Run a CloudWatch Logs Insights query and return parsed results.

        Args:
            query_string: CW Logs Insights query.
            hours_back: How many hours ago to start the window.
            log_group: Log group name.
            end_hours_back: How many hours ago to end (None = now).
            limit: Max results.
            timeout_seconds: Polling deadline.

        Returns:
            List[dict] on success, None on failure/timeout.
        """
        now_ms = int(time.time() * 1000)
        start_ms = int((time.time() - hours_back * 3600) * 1000)
        end_ms = (
            int((time.time() - end_hours_back * 3600) * 1000)
            if end_hours_back is not None
            else now_ms
        )

        resp = self._client.start_query(
            logGroupName=log_group,
            startTime=start_ms,
            endTime=end_ms,
            queryString=query_string,
            limit=limit,
        )
        qid = resp["queryId"]
        print(f"  Query started (id: {qid})")

        deadline = time.time() + timeout_seconds
        poll_count = 0
        while True:
            status_resp = self._client.get_query_results(queryId=qid)
            status = status_resp["status"]
            if status in ("Complete", "Failed", "Cancelled"):
                break
            poll_count += 1
            remaining = int(deadline - time.time())
            if remaining <= 0:
                print(f"  TIMEOUT after {timeout_seconds}s — cancelling query")
                try:
                    self._client.stop_query(queryId=qid)
                except Exception:
                    pass
                return None
            if poll_count % 5 == 0:
                print(f"  ...polling ({remaining}s remaining)")
            time.sleep(POLL_INTERVAL_SECONDS)

        if status != "Complete":
            print(f"  Query ended with status: {status}")
            return None

        results = [
            {field["field"]: field["value"] for field in row}
            for row in status_resp["results"]
        ]
        print(f"  Done — {len(results)} result(s)")
        return results

    # ----- multi-group query -----

    def query_multi(
        self,
        query_string,
        hours_back,
        log_groups,
        end_hours_back=None,
        limit=DEFAULT_LIMIT,
        timeout_seconds=300,
    ):
        """Run the same query across multiple log groups, merge results.

        Each row gets an extra ``_log_group`` field.
        """
        all_results = []
        for lg in log_groups:
            print(f"\n--- Querying: {lg} ---")
            results = self.query(
                query_string=query_string,
                hours_back=hours_back,
                log_group=lg,
                end_hours_back=end_hours_back,
                limit=limit,
                timeout_seconds=timeout_seconds,
            )
            if results:
                for row in results:
                    row["_log_group"] = lg
                all_results.extend(results)

        all_results.sort(key=lambda r: r.get("@timestamp", ""))
        print(
            f"\nMerged total: {len(all_results)} result(s) "
            f"from {len(log_groups)} log group(s)"
        )
        return all_results

    # ----- display helpers -----

    @staticmethod
    def _fields(results, include_ptr=False):
        if not results:
            return []
        fields = list(results[0].keys())
        if not include_ptr:
            fields = [f for f in fields if f != "@ptr"]
        return fields

    @staticmethod
    def print_table(results, fields=None, max_col_width=80, include_ptr=False):
        """Print results as an ASCII table."""
        if not results:
            print("(no results)")
            return
        fields = fields or CWClient._fields(results, include_ptr=include_ptr)
        col_w = {}
        for f in fields:
            vals = [str(r.get(f, ""))[:max_col_width] for r in results]
            col_w[f] = max(len(f), max((len(v) for v in vals), default=0))
        print(" | ".join(f.ljust(col_w[f]) for f in fields))
        print("-+-".join("-" * col_w[f] for f in fields))
        for row in results:
            print(
                " | ".join(
                    str(row.get(f, ""))[:max_col_width].ljust(col_w[f])
                    for f in fields
                )
            )
        print(f"\n({len(results)} row(s))")

    @staticmethod
    def print_json(results, include_ptr=False):
        if not results:
            print("[]")
            return
        if not include_ptr:
            results = [{k: v for k, v in r.items() if k != "@ptr"} for r in results]
        print(json.dumps(results, indent=2, default=str))

    # ----- export helpers -----

    @staticmethod
    def to_csv_file(results, filepath, include_ptr=False):
        """Write results to a CSV file."""
        if not results:
            print("No results to write.")
            return
        fields = CWClient._fields(results, include_ptr=include_ptr)
        with open(filepath, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(results)
        print(f"Wrote {len(results)} row(s) to {filepath}")

    @staticmethod
    def save(results, name, output_dir=INVESTIGATIONS_DIR):
        """Save results to investigations/<name>.csv. Returns filepath or None."""
        if not results:
            print(f"No results to save for '{name}'.")
            return None
        os.makedirs(output_dir, exist_ok=True)
        fname = name if name.endswith(".csv") else f"{name}.csv"
        fpath = os.path.join(output_dir, fname)
        CWClient.to_csv_file(results, fpath)
        return fpath

    # ----- analysis helpers -----

    @staticmethod
    def summarize_stats(results, value_field, group_field=None):
        """Compute count/avg/min/p50/p90/p95/p99/max from fetched results.

        Args:
            results: List of dicts.
            value_field: Field with numeric values.
            group_field: Optional grouping field.

        Returns:
            List of stat dicts.
        """

        def _pct(vs, p):
            idx = int(p / 100 * (len(vs) - 1))
            return vs[idx]

        def _stats(values):
            values = sorted(values)
            n = len(values)
            if n == 0:
                return {}
            return {
                "count": n,
                "avg": round(sum(values) / n, 4),
                "min": values[0],
                "p50": _pct(values, 50),
                "p90": _pct(values, 90),
                "p95": _pct(values, 95),
                "p99": _pct(values, 99),
                "max": values[-1],
            }

        def _float(v):
            try:
                return float(v)
            except (TypeError, ValueError):
                return None

        if group_field:
            groups = defaultdict(list)
            for row in results:
                v = _float(row.get(value_field))
                if v is not None:
                    groups[row.get(group_field, "unknown")].append(v)
            out = []
            for grp, vals in sorted(groups.items(), key=lambda x: -len(x[1])):
                s = _stats(vals)
                s["group"] = grp
                out.append(s)
            return out
        else:
            vals = [v for v in (_float(r.get(value_field)) for r in results) if v is not None]
            s = _stats(vals)
            return [s] if s else []

    @staticmethod
    def time_bucket_counts(results, timestamp_field="@timestamp", bucket_minutes=15):
        """Group results into time buckets for spike detection.

        Returns:
            List of dicts with ``bucket`` and ``count``, sorted chronologically.
        """
        buckets = defaultdict(int)
        bucket_secs = bucket_minutes * 60

        for row in results:
            ts_str = row.get(timestamp_field, "")
            if not ts_str:
                continue
            try:
                cleaned = ts_str.replace(" ", "T").replace("Z", "+00:00")
                if "+" not in cleaned and cleaned.count("-") <= 2:
                    cleaned += "+00:00"
                dt = datetime.fromisoformat(cleaned)
            except (ValueError, TypeError):
                continue

            epoch = dt.timestamp()
            bucket_epoch = int(epoch // bucket_secs) * bucket_secs
            bucket_dt = datetime.fromtimestamp(bucket_epoch, tz=timezone.utc)
            buckets[bucket_dt.strftime("%Y-%m-%d %H:%M")] += 1

        return [{"bucket": k, "count": v} for k, v in sorted(buckets.items())]


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Run a CloudWatch Logs Insights query from the command line."
    )
    parser.add_argument("--region", default=DEFAULT_REGION, help="AWS region")
    parser.add_argument("--log-group", required=True, help="Log group name")
    parser.add_argument(
        "--log-groups",
        nargs="*",
        help="Additional log groups (enables multi-group mode)",
    )
    parser.add_argument(
        "--hours", type=float, required=True, help="Hours back to query"
    )
    parser.add_argument("--end-hours", type=float, default=None, help="End hours back")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--query", required=True, help="Insights query string")
    parser.add_argument("--save", default=None, help="Save results as this name in investigations/")
    parser.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format",
    )

    args = parser.parse_args()
    cw = CWClient(region=args.region)

    all_groups = [args.log_group] + (args.log_groups or [])
    if len(all_groups) > 1:
        results = cw.query_multi(
            args.query, args.hours, all_groups, end_hours_back=args.end_hours, limit=args.limit
        )
    else:
        results = cw.query(
            args.query, args.hours, args.log_group, end_hours_back=args.end_hours, limit=args.limit
        )

    if not results:
        print("No results.")
        sys.exit(1)

    if args.format == "json":
        cw.print_json(results)
    elif args.format == "csv" and args.save:
        pass  # will be saved below
    else:
        cw.print_table(results)

    if args.save:
        cw.save(results, args.save)


if __name__ == "__main__":
    main()
