# RCA Report Template

Use this template to produce the final investigation report.

---

# RCA: {issue_title}

**Tenant**: {tenant}
**Date**: {date}
**Investigator**: Claude + {engineer}
**Log Group(s)**: {log_groups}
**Time Window**: {time_window}

---

## Issue Summary

Brief description of the reported problem: what was observed, who reported it, and when.

## Timeline

| Time | Event |
|------|-------|
| {time} | {event description} |

## Root Cause

Clear statement of what caused the issue. If inconclusive, list top hypotheses ranked by evidence strength.

## Evidence

### Phase 1 — Reconnaissance
- Log volume: {summary}
- Message type distribution: see `{csv_file}`
- Key observation: {finding}

### Phase 2 — Endpoint Performance
- Slowest endpoints: {list}
- Latency percentiles: see `{csv_file}`
- Key observation: {finding}

### Phase 3 — Error Analysis
- Error rate: {summary}
- Error types: {list}
- Temporal pattern: {description}
- See `{csv_file}`

### Phase 4 — Deep Trace
- Request ID: `{request_id}`
- Total duration: {duration}
- Bottleneck: {description}
- See `{csv_file}`

### Phase 5 — Session Timeline
- User activity pattern: {description}
- See `{csv_file}`

### Phase 6 — Cross-Service
- Related services checked: {list}
- Findings: {description}
- See `{csv_file}`

## Impact

- **Users affected**: {count or description}
- **Duration**: {how long the issue lasted}
- **Severity**: {P1/P2/P3/P4}

## Data Files

All investigation data saved in `investigations/`:

| File | Description |
|------|-------------|
| `{filename}` | {description} |

## Recommendations

1. **Immediate**: {action}
2. **Short-term**: {action}
3. **Long-term**: {action}
