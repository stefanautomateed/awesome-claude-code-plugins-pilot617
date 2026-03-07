# CloudWatch Insights Query Library

> **Adapt all parse patterns based on what Phase 1 Reconnaissance reveals about your log format.**

Pre-built query templates for production log investigation. Substitute `{filter_pattern}` with whatever scoping filter is relevant (e.g., a service name, request path, error keyword). Strategy templates use generic placeholders like `{operation_field}`, `{duration_field}`, `{trace_id}`, `{entity_id}` — replace these with the actual field names discovered during reconnaissance.

---

## Phase 1 — Reconnaissance

These queries are universal and work with any log format. Run them first to understand the shape of your logs before picking a strategy.

### Sample raw logs
```
fields @timestamp, @message
| filter @message like /{filter_pattern}/
| sort @timestamp desc
| limit 25
```

### Log volume over time
```
filter @message like /{filter_pattern}/
| stats count(*) as cnt by bin(1h)
| sort bin asc
```

### Field discovery (JSON)
```
fields @timestamp, @message
| filter @message like /{filter_pattern}/
| parse @message '"*":' as field_name
| stats count(*) by field_name
| sort count(*) desc
```

### Message type distribution
```
fields @timestamp, @message
| filter @message like /{filter_pattern}/
| stats count(*) by @message
| sort count(*) desc
| limit 50
```

---

## Phase 2 — Strategy Templates

Pick a strategy based on what you learned in Phase 1. Replace `{operation_field}`, `{duration_field}`, and other placeholders with the actual field names found in your logs.

---

### Error Analysis

#### Error count by type
```
fields @timestamp, @message
| filter @message like /{filter_pattern}/ and (@message like /error/i or @message like /exception/i or @message like /traceback/i)
| stats count(*) as cnt by @message
| sort cnt desc
| limit 30
```

#### Error temporal distribution
```
fields @timestamp, @message
| filter @message like /{filter_pattern}/ and (@message like /error/i or @message like /exception/i)
| stats count(*) as error_count by bin(15m)
| sort bin asc
```

#### Stack traces
```
fields @timestamp, @message
| filter @message like /{filter_pattern}/ and (@message like /Traceback/ or @message like /stack/i)
| sort @timestamp desc
| limit 20
```

---

### Performance Analysis

> Note: Replace `{operation_field}` and `{duration_field}` with the actual field names discovered in Phase 1 (e.g., `endpoint`, `handler`, `response_time`, `latency`).

#### Operation stats with percentiles
```
fields @timestamp, @message
| filter @message like /{filter_pattern}/
| parse @message '"{operation_field}": "*"' as operation
| parse @message '"{duration_field}": *,' as duration
| stats count(*) as cnt,
    avg(duration) as avg_dur,
    pct(duration, 50) as p50,
    pct(duration, 90) as p90,
    pct(duration, 95) as p95,
    pct(duration, 99) as p99,
    max(duration) as max_dur
  by operation
| sort max_dur desc
```

#### Slow operations above threshold
```
fields @timestamp, @message
| filter @message like /{filter_pattern}/
| parse @message '"{operation_field}": "*"' as operation
| parse @message '"{duration_field}": *,' as duration
| filter duration > {threshold}
| sort duration desc
| limit 50
```

---

### Deep Trace

> Note: Replace `{trace_id}` with the actual identifier field from your logs (e.g., `request_id`, `correlation_id`, `span_id`).

#### Full event lifecycle by trace ID
```
fields @timestamp, @message
| filter @message like /{trace_id}/
| sort @timestamp asc
| limit 200
```

#### Slow events with context
```
fields @timestamp, @message
| filter @message like /{filter_pattern}/
| parse @message '"{trace_id}": "*"' as trace_id
| parse @message '"{duration_field}": *,' as duration
| filter duration > {threshold}
| display @timestamp, trace_id, duration
| sort duration desc
| limit 20
```

---

### Entity Tracking

> Note: Replace `{entity_id}` with the actual identifier for the entity you are investigating (e.g., a user ID, order ID, device ID).

#### All activity for an entity over time
```
fields @timestamp, @message
| filter @message like /{filter_pattern}/ and @message like /{entity_id}/
| sort @timestamp asc
| limit 500
```

---

### Cross-Service

> Note: Use the `query_multi` method to run the same query across multiple log groups simultaneously.

#### Cross-service event search
```
fields @timestamp, @message
| filter @message like /{filter_pattern}/
| sort @timestamp desc
| limit 100
```

#### Cross-service error correlation
```
fields @timestamp, @message
| filter @message like /{filter_pattern}/ and (@message like /error/i or @message like /exception/i)
| stats count(*) as error_count by bin(15m)
| sort bin asc
```
