# cw-debug

A generic CloudWatch log investigation skill for Claude Code. It adaptively debugs production issues — bugs, performance problems, unexpected behavior — using CloudWatch Logs Insights.

## Installation

```shell
/plugin marketplace add <owner>/awesome-claude-code-plugins
/plugin install cw-debug@awesome-claude-code-plugins
```

## Prerequisites

- AWS credentials configured (via `aws configure`, environment variables, or IAM role)
- Python 3 with `boto3` installed (the skill uses `.venv/bin/python` by default)

## Usage

```
/cw-debug <log_group> <filter_pattern> <hours_back> <region> "<issue_description>"
```

### Arguments

| Argument | Description | Example |
|---|---|---|
| `log_group` | CloudWatch log group path | `/aws/ecs/my-service` |
| `filter_pattern` | Any string to filter logs — user ID, request ID, error code, service name | `user-42`, `req-abc123`, `TimeoutError` |
| `hours_back` | How many hours of logs to search | `24`, `168` (7 days) |
| `region` | AWS region | `us-east-1`, `eu-west-1` |
| `issue_description` | Free-text description of the problem | `"Users getting 500 errors on checkout"` |

### Examples

**Investigating a bug:**
```
/cw-debug /aws/ecs/payment-service "NullPointerException" 24 us-east-1 "Payments failing intermittently since yesterday"
```

**Debugging a performance issue:**
```
/cw-debug /aws/lambda/api-handler "slow" 48 eu-west-1 "API response times spiked above 5s"
```

**Tracing a specific user's experience:**
```
/cw-debug /aws/ecs/web-app "user-12345" 12 us-west-2 "User reports pages not loading"
```

**Investigating an error spike:**
```
/cw-debug /aws/ecs/order-service "OrderProcessor" 168 ap-southeast-1 "Order processing failures increased 10x this week"
```

## How It Works

The skill follows a 3-phase adaptive methodology:

### Phase 1 — Reconnaissance (always runs)
- Samples raw logs to discover the format (JSON, key-value, plain text)
- Identifies available fields and parse patterns
- Checks log volume over time for anomalies
- Classifies the issue type: error/bug, performance, data/behavioral, or unknown

### Phase 2 — Adaptive Investigation
Based on what Phase 1 reveals, the skill picks 2-4 strategies:

| Strategy | When it's used |
|---|---|
| **Error Analysis** | Errors or exceptions found in logs |
| **Performance Analysis** | Slow responses or latency issues |
| **Deep Trace** | Need to trace a specific request's full lifecycle |
| **Code Correlation** | Bug suspected — searches local codebase for matching code paths |
| **Entity Tracking** | Need to understand one user/session/entity's experience |
| **Cross-Service** | Issue spans multiple services — queries multiple log groups |

### Phase 3 — Summary
Prints a concise investigation summary to stdout:
- Root cause or ranked hypotheses
- Supporting evidence
- Actionable recommendations

Reports are only written to file if you explicitly ask.

## Included Components

| File | Purpose |
|---|---|
| `skills/cw-debug/SKILL.md` | The skill definition and methodology |
| `skills/cw-debug/scripts/cw.py` | Self-contained CloudWatch Logs Insights client (CLI + Python API) |
| `skills/cw-debug/query_library.md` | Pre-built query templates for each investigation strategy |
| `skills/cw-debug/rca_template.md` | RCA report template (used only when you ask for a written report) |
