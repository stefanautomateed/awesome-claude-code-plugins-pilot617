> **Note**: This template is only used when the user explicitly asks for a written report.

# RCA: {issue_title}

**Filter**: {filter_pattern}
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

For each investigation strategy used, include a subsection:

### [Strategy Name]
- What was found
- Key data points
- How it supports or refutes the root cause hypothesis

## Impact

- **Users affected**: {count or description}
- **Duration**: {how long the issue lasted}
- **Severity**: {P1/P2/P3/P4}

## Recommendations

1. **Immediate**: {action}
2. **Short-term**: {action}
3. **Long-term**: {action}
