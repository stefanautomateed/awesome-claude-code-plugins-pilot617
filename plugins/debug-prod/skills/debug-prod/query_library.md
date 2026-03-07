# CloudWatch Insights Query Library

Pre-built query templates for production log investigation. Substitute `{tenant}`, `{request_id}`, `{threshold}`, `{user_id}`, `{endpoint}` as needed.

---

## Reconnaissance

### Message distribution
```
fields @timestamp, @message
| filter @message like /{tenant}/
| stats count(*) by msg
| sort count(*) desc
| limit 50
```

### Log volume over time
```
filter @message like /{tenant}/
| stats count(*) as cnt by bin(1h)
| sort bin asc
```

### Sample raw logs
```
fields @timestamp, @message
| filter @message like /{tenant}/
| sort @timestamp desc
| limit 25
```

### Unique log fields discovery
```
fields @timestamp, @message
| filter @message like /{tenant}/
| parse @message '"msg": "*"' as msg_type
| stats count(*) by msg_type
| sort count(*) desc
```

---

## Performance

### Endpoint stats with percentiles
```
fields @timestamp, @message
| filter @message like /{tenant}/
| parse @message '"endpoint": "*"' as endpoint
| parse @message '"response_time": *,' as response_time
| stats count(*) as cnt,
    avg(response_time) as avg_rt,
    pct(response_time, 50) as p50,
    pct(response_time, 90) as p90,
    pct(response_time, 95) as p95,
    pct(response_time, 99) as p99,
    max(response_time) as max_rt
  by endpoint
| sort max_rt desc
```

### Slow requests above threshold
```
fields @timestamp, @message
| filter @message like /{tenant}/
| parse @message '"endpoint": "*"' as endpoint
| parse @message '"response_time": *,' as response_time
| filter response_time > {threshold}
| sort response_time desc
| limit 50
```

### Response time over time (for a specific endpoint)
```
fields @timestamp, @message
| filter @message like /{tenant}/ and @message like /{endpoint}/
| parse @message '"response_time": *,' as response_time
| stats avg(response_time) as avg_rt, max(response_time) as max_rt, count(*) as cnt by bin(15m)
| sort bin asc
```

---

## Error Analysis

### Error count by type
```
fields @timestamp, @message
| filter @message like /{tenant}/ and (@message like /error/i or @message like /exception/i or @message like /traceback/i)
| parse @message '"msg": "*"' as error_msg
| stats count(*) as cnt by error_msg
| sort cnt desc
| limit 30
```

### Error temporal distribution
```
fields @timestamp, @message
| filter @message like /{tenant}/ and (@message like /error/i or @message like /exception/i)
| stats count(*) as error_count by bin(15m)
| sort bin asc
```

### HTTP status code distribution
```
fields @timestamp, @message
| filter @message like /{tenant}/
| parse @message '"status_code": *,' as status_code
| stats count(*) as cnt by status_code
| sort cnt desc
```

### Stack traces
```
fields @timestamp, @message
| filter @message like /{tenant}/ and @message like /Traceback/
| sort @timestamp desc
| limit 20
```

---

## Tracing

### Full request lifecycle
```
fields @timestamp, @message
| filter @message like /{request_id}/
| sort @timestamp asc
| limit 200
```

### Slow requests with full context
```
fields @timestamp, @message
| filter @message like /{tenant}/
| parse @message '"request_id": "*"' as request_id
| parse @message '"response_time": *,' as response_time
| filter response_time > {threshold}
| display @timestamp, request_id, response_time
| sort response_time desc
| limit 20
```

### User/session timeline
```
fields @timestamp, @message
| filter @message like /{tenant}/ and @message like /{user_id}/
| sort @timestamp asc
| limit 500
```

---

## Cross-Service

### Worker task duration
```
fields @timestamp, @message
| filter @message like /{tenant}/ and @message like /task/
| parse @message '"task_name": "*"' as task_name
| parse @message '"duration": *,' as duration
| stats count(*) as cnt, avg(duration) as avg_dur, max(duration) as max_dur by task_name
| sort max_dur desc
```

### Queue backlog indicator
```
fields @timestamp, @message
| filter @message like /{tenant}/ and @message like /celery/
| parse @message '"queue_time": *,' as queue_time
| stats avg(queue_time) as avg_queue, max(queue_time) as max_queue by bin(15m)
| sort bin asc
```
