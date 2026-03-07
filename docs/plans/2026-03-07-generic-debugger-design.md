# Generic CloudWatch Debugger — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor the debug-prod plugin from a tenant-specific web-app debugger into a generic CloudWatch log investigation skill that works with any service, any log format, and any issue type.

**Architecture:** Adaptive 3-phase methodology — mandatory reconnaissance, then skill picks from a menu of investigation strategies based on what it discovers, then prints a summary to stdout. No file writes unless user asks.

**Tech Stack:** CloudWatch Logs Insights via cw.py (boto3), Claude Code skill (SKILL.md)

---

## Design

### Invocation

```
/debug-prod <log_group> <filter_pattern> <hours_back> <region> "<issue_description>"
```

- `log_group` — primary CloudWatch log group
- `filter_pattern` — any string to filter logs (tenant ID, user ID, request ID, service name, error code)
- `hours_back` — time window
- `region` — AWS region
- `issue_description` — free-text description of the problem (bug, perf issue, unexpected behavior, etc.)

## Investigation Methodology

### Phase 1 — Reconnaissance (always runs)

- Sample raw logs to discover format (JSON, key-value, plain text)
- Identify available fields and parse patterns
- Check log volume over time for anomalies
- Classify issue type based on logs + issue description: performance, error/bug, data/behavioral, or unknown

### Phase 2 — Adaptive Investigation

Based on Phase 1 findings and the issue description, the skill selects 2-4 strategies from:

| Strategy | When to use | What it does |
|---|---|---|
| Error Analysis | Errors/exceptions found, or issue describes a bug | Count errors by type, temporal distribution, stack traces |
| Performance Analysis | Slow responses or latency mentioned | Parse response times, compute percentiles, find slowest operations |
| Deep Trace | Need to understand a specific request/event lifecycle | Trace by request ID or correlation ID through full lifecycle |
| Code Correlation | Bug or unexpected behavior | Read local codebase to find code paths that correspond to log patterns, identify potential root cause in source |
| Entity Tracking | Need to understand a specific user/session/entity's experience | Trace all activity for a given identifier over time |
| Cross-Service | Evidence suggests issue spans services | Fan out to other log groups using query_multi, correlate timestamps |

The skill explains why it chose each strategy.

### Phase 3 — Summary

- Print investigation summary to stdout (no file writes by default)
- Root cause or top hypotheses ranked by evidence
- Supporting evidence from each strategy used
- Actionable recommendations
- Only write to file if user explicitly asks

## Query Library

- Section 1: Reconnaissance — universal queries (raw sampling, volume, field discovery)
- Section 2: Strategy templates — grouped by strategy with multiple parse variants (JSON, key-value, plain text)
- All queries use `{filter_pattern}` instead of `{tenant}`
- No stack-specific queries

## RCA Template

- Generic headers (Filter instead of Tenant)
- Dynamic evidence sections based on strategies used
- Kept: Issue Summary, Timeline, Root Cause, Impact, Recommendations

## Files Changed

| File | Change |
|---|---|
| SKILL.md | Full rewrite — new args, adaptive methodology, code correlation, stdout-first output |
| query_library.md | Rewrite — format-adaptive templates, generic filters |
| rca_template.md | Simplify — generic headers, dynamic evidence sections |
| cw.py | No changes (already generic) |
| plugin.json | Update description |
| marketplace.json | Update description |

---

## Implementation Tasks

### Task 1: Rewrite SKILL.md

**Files:**
- Modify: `plugins/debug-prod/skills/debug-prod/SKILL.md` (full rewrite)

**Step 1: Rewrite the skill file**

Replace the entire SKILL.md with the new generic version. Key changes:

1. **Arguments**: Replace `<tenant> <log_group> <hours_back> <region> "<issue_description>"` with `<log_group> <filter_pattern> <hours_back> <region> "<issue_description>"`
2. **Setup**: Keep cw.py references with `${CLAUDE_PLUGIN_ROOT}`, update inline examples to use `{filter_pattern}` instead of `{tenant}`
3. **Rules**: Remove "Save everything" rule. Add: "Do not write files unless user asks." Add: "Read the local codebase to correlate findings with source code."
4. **Phase 1 — Reconnaissance**: Keep raw log sampling, volume checks. Remove tenant-specific filter examples. Add: classify issue type (performance / error-bug / data-behavioral / unknown). All query filters use `{filter_pattern}`.
5. **Phase 2 — Adaptive Investigation**: Replace rigid Phases 2-6 with a strategy menu table:
   - Error Analysis: when errors/exceptions found or issue describes a bug
   - Performance Analysis: when slow responses or latency mentioned
   - Deep Trace: when need to trace a specific request/event lifecycle
   - Code Correlation: when bug or unexpected behavior — read local codebase to find code paths matching log patterns
   - Entity Tracking: when need to understand a user/session/entity experience
   - Cross-Service: when evidence suggests issue spans services, fan out to other log groups
   - Skill picks 2-4 strategies and explains why it chose each one.
6. **Phase 3 — Summary**: Print investigation summary to stdout. Root cause or hypotheses ranked by evidence. Supporting evidence. Recommendations. Only write to file if user explicitly asks.
7. **Output section**: Remove file-write-by-default behavior. Remove reference to rca_template. State: "Print a concise investigation summary to stdout. If the user asks for a file, use the RCA template at `${CLAUDE_PLUGIN_ROOT}/skills/debug-prod/rca_template.md`."

**Step 2: Review the rewrite**

Read the file back and verify:
- No mention of `tenant` anywhere
- All filters use `{filter_pattern}`
- No stack-specific examples (celery, nginx, etc.)
- No mandatory file writes
- Code Correlation strategy references reading local codebase

**Step 3: Commit**

```bash
git add plugins/debug-prod/skills/debug-prod/SKILL.md
git commit -m "refactor: rewrite SKILL.md as generic adaptive debugger

Replace tenant-specific args with generic filter_pattern.
Replace rigid 6-phase methodology with adaptive strategy menu.
Add Code Correlation strategy for local codebase investigation.
Remove mandatory file writes — stdout-first output."
```

---

### Task 2: Rewrite query_library.md

**Files:**
- Modify: `plugins/debug-prod/skills/debug-prod/query_library.md` (full rewrite)

**Step 1: Rewrite the query library**

Restructure into two sections:

**Section 1 — Reconnaissance (universal, works with any log format):**
- Sample raw logs: `fields @timestamp, @message | filter @message like /{filter_pattern}/ | sort @timestamp desc | limit 25`
- Log volume over time: `filter @message like /{filter_pattern}/ | stats count(*) as cnt by bin(1h) | sort bin asc`
- Field discovery (JSON): `fields @timestamp, @message | filter @message like /{filter_pattern}/ | parse @message '"*":' as field_name | stats count(*) by field_name | sort count(*) desc`
- Message type distribution: `fields @timestamp, @message | filter @message like /{filter_pattern}/ | stats count(*) by @message | sort count(*) desc | limit 50`

**Section 2 — Strategy Templates (grouped by strategy):**

Each strategy gets 2-3 query templates. Use `{filter_pattern}` everywhere. Provide parse variant notes (JSON vs key-value vs plain text) as comments, not hardcoded patterns — the skill adapts parse patterns from Phase 1.

- **Error Analysis**: error count by type, error temporal distribution, stack traces
- **Performance Analysis**: operation stats with percentiles (generic field placeholders `{operation_field}`, `{duration_field}`), slow operations above threshold
- **Deep Trace**: full event lifecycle by correlation ID `{trace_id}`, slow events with context
- **Entity Tracking**: all activity for `{entity_id}` over time
- **Cross-Service**: same query across multiple log groups (note: use `query_multi`)

Remove all celery/queue/nginx-specific queries.

**Step 2: Review the rewrite**

Verify: no `{tenant}`, no stack-specific queries, all use `{filter_pattern}`, parse patterns are noted as adaptable.

**Step 3: Commit**

```bash
git add plugins/debug-prod/skills/debug-prod/query_library.md
git commit -m "refactor: rewrite query library with generic filter and strategy grouping

Replace tenant filters with filter_pattern.
Remove stack-specific queries (celery, nginx).
Group by investigation strategy with format-adaptive notes."
```

---

### Task 3: Simplify rca_template.md

**Files:**
- Modify: `plugins/debug-prod/skills/debug-prod/rca_template.md`

**Step 1: Rewrite the template**

Key changes:
- Replace `{tenant}` with `{filter_pattern}` in header
- Replace rigid Phase 1-6 evidence sections with a dynamic structure:
  ```
  ## Evidence

  For each investigation strategy used, include:
  ### [Strategy Name]
  - What was found
  - Key data points
  - How it supports or refutes the root cause hypothesis
  ```
- Keep: Issue Summary, Timeline, Root Cause, Impact, Recommendations
- Remove CSV file references (no mandatory file writes)
- Add note: "This template is only used when the user explicitly asks for a written report."

**Step 2: Commit**

```bash
git add plugins/debug-prod/skills/debug-prod/rca_template.md
git commit -m "refactor: simplify RCA template with generic headers and dynamic sections"
```

---

### Task 4: Update plugin.json and marketplace.json

**Files:**
- Modify: `plugins/debug-prod/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Step 1: Update plugin.json**

Change description to: `"Generic CloudWatch log investigation skill with adaptive debugging methodology"`

**Step 2: Update marketplace.json**

Change the debug-prod plugin's description to match. Update keywords to: `["debugging", "cloudwatch", "aws", "production", "logs", "investigation"]`

**Step 3: Commit**

```bash
git add plugins/debug-prod/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "refactor: update plugin metadata for generic debugger"
```
