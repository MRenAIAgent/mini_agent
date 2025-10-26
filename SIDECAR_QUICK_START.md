# Sidecar Tools: Quick Start Guide

## What Are Sidecar Tools?

**Sidecar tools** run in the background without blocking your agent. Perfect for analytics, logging, notifications - anything that doesn't need to complete before responding to the user.

```
Regular Tool:  Agent waits ⏳ → Tool completes → Agent continues
Sidecar Tool:  Agent starts → Tool runs in background → Agent continues immediately ⚡
```

**Result**: 30-60% faster response times!

---

## 5-Minute Quick Start

### Step 1: Create Your Sidecar

```python
# app/tool/my_sidecar.py
from app.tool.sidecar_tool import SidecarTool
import logging

logger = logging.getLogger(__name__)


class MyAnalyticsSidecar(SidecarTool):
    """Send analytics without blocking the agent."""

    name: str = "analytics"
    description: str = "Track user interactions in background"
    sidecar_timeout: int = 30  # 30 second timeout

    async def _execute_background(self, arguments: dict):
        """This runs in the background - won't block the agent!"""

        # Your background logic here
        event_type = arguments.get("event_type")
        state = arguments.get("state", {})

        # Example: Send to analytics API
        await your_analytics_api.track({
            "event": event_type,
            "chatbot_id": state.get("chatbot_id"),
            "user_id": state.get("user_id")
        })

        logger.info(f"Analytics sent: {event_type}")
        return {"status": "success"}


# Register so agent can find it
MyAnalyticsSidecar.register("analytics")
```

### Step 2: Add to Agent Config

```json
{
  "agent_id": "my_agent",
  "tools": {
    "analytics": {
      "name": "analytics",
      "description": "Track user events",
      "enabled": true
    }
  }
}
```

### Step 3: That's It!

The agent automatically detects sidecars and runs them in the background. No additional code needed!

---

## Built-In Examples (Ready to Use)

### 1. Analytics Sidecar

```python
from app.tool.sidecar_examples import AnalyticsSidecar

# Already registered and ready to use!
# Just add to your agent config:
{
  "tools": {
    "analytics_sidecar": {"enabled": true}
  }
}
```

### 2. Notification Sidecar

```python
from app.tool.sidecar_examples import NotificationSidecar

# Send emails/SMS in background
# Add to config:
{
  "tools": {
    "notification_sidecar": {"enabled": true}
  }
}
```

### 3. Audit Log Sidecar

```python
from app.tool.sidecar_examples import AuditLogSidecar

# Write compliance logs async
{
  "tools": {
    "audit_log_sidecar": {"enabled": true}
  }
}
```

---

## When to Use Sidecars

### ✅ Perfect For:

- 📊 **Analytics/Telemetry** - Track events, metrics
- 📧 **Notifications** - Email, SMS, push notifications
- 📝 **Logging** - Audit logs, compliance records
- 🔥 **Cache Warming** - Pre-fetch data for next request
- 📡 **Events** - Publish to Kafka, event bus

### ❌ Don't Use For:

- ❌ Database queries needed for the response
- ❌ User-requested actions (e.g., "create ticket")
- ❌ Critical operations where failure matters

---

## Performance Impact

### Before (Blocking Analytics)
```
User asks question
  → Search docs (100ms)
  → Send analytics (100ms) ⏳ BLOCKING
  → Generate response (50ms)
  → Total: 250ms
```

### After (Sidecar Analytics)
```
User asks question
  → Search docs (100ms)
  → Send analytics (<1ms) ⚡ NON-BLOCKING
  → Generate response (50ms)
  → Total: 151ms (40% faster!)
```

---

## Monitoring & Debugging

### Check Sidecar Status

```python
from app.tool.sidecar_tool import get_sidecar_executor

executor = get_sidecar_executor()

# Get metrics
metrics = executor.get_metrics()
print(f"Sidecars started: {metrics['total_started']}")
print(f"Sidecars completed: {metrics['total_completed']}")
print(f"Sidecars failed: {metrics['total_failed']}")

# Per-tool stats
analytics_stats = metrics['by_tool']['analytics']
print(f"Avg duration: {analytics_stats['avg_duration_ms']}ms")
```

### Check Specific Sidecar

```python
# When sidecar starts, you get a handle
handle = await sidecar._arun({"data": "test"})
sidecar_id = handle.response["sidecar_id"]

# Check status later
status = executor.get_status(sidecar_id)
print(f"Status: {status.status}")  # PENDING, RUNNING, COMPLETED, FAILED
print(f"Result: {status.result}")
```

---

## Advanced Features

### Custom Callbacks

```python
class MyNotificationSidecar(SidecarTool):
    async def _on_complete(self, result):
        """Called when sidecar succeeds."""
        logger.info(f"Notification sent: {result}")
        await send_webhook("notification_sent", result)

    async def _on_error(self, error):
        """Called when sidecar fails."""
        logger.error(f"Notification failed: {error}")
        await alert_team("sidecar_failure", str(error))
```

### Custom Timeout

```python
class SlowSidecar(SidecarTool):
    name: str = "slow_operation"
    sidecar_timeout: int = 600  # 10 minutes for slow operations
```

### Concurrency Control

```python
from app.tool.sidecar_tool import SidecarExecutor

# Custom executor with higher limits
executor = SidecarExecutor(
    max_concurrent_sidecars=100,  # Allow 100 parallel sidecars
    default_timeout=300,
    enable_monitoring=True
)
```

---

## Testing Your Sidecar

```python
# tests/test_my_sidecar.py
import pytest
from app.tool.my_sidecar import MyAnalyticsSidecar

@pytest.mark.asyncio
async def test_analytics_sidecar():
    sidecar = MyAnalyticsSidecar()

    # Mock the get_state method
    def mock_state():
        return {"chatbot_id": "test", "conversation_id": "123"}

    sidecar.get_state = mock_state

    # Execute sidecar
    result = await sidecar._arun({
        "event_type": "test_event",
        "data": {"key": "value"}
    })

    # Should return immediately with handle
    assert "sidecar_id" in result.response
    assert result.response["status"] in ["pending", "running"]
```

---

## Troubleshooting

### Issue: "Max concurrent sidecars limit reached"

**Solution**: Increase the limit or wait for sidecars to complete

```python
executor = SidecarExecutor(max_concurrent_sidecars=50)
```

### Issue: Sidecars timing out

**Solutions**:
1. Increase timeout: `sidecar_timeout = 600`
2. Optimize your background operation
3. Check API/network performance

### Issue: Can't find sidecar results

**Solution**: Store the sidecar_id and check later

```python
result = await sidecar._arun({"data": "test"})
sidecar_id = result.response["sidecar_id"]

# Check later
handle = executor.get_status(sidecar_id)
```

---

## Best Practices

1. **✅ Use for non-critical operations only**
   ```python
   # Good: Analytics doesn't affect response
   await analytics_sidecar.track("page_view")

   # Bad: User needs search results!
   results = await search_tool.search(query)  # Don't use sidecar here
   ```

2. **✅ Set appropriate timeouts**
   ```python
   # Fast operations (analytics, events)
   sidecar_timeout: int = 30

   # Slow operations (batch jobs)
   sidecar_timeout: int = 600
   ```

3. **✅ Handle errors gracefully**
   ```python
   async def _execute_background(self, arguments):
       try:
           await external_api.call(arguments)
       except Exception as e:
           logger.error(f"Sidecar failed: {e}")
           raise  # Let error callback handle it
   ```

4. **✅ Monitor sidecar health**
   ```python
   metrics = executor.get_metrics()
   failure_rate = metrics['total_failed'] / metrics['total_started']

   if failure_rate > 0.1:  # >10% failing
       await alert_team("High sidecar failure rate")
   ```

---

## Next Steps

1. **Read Full Docs**: See `SIDECAR_TOOLS_README.md` for complete guide
2. **View Examples**: Check `app/tool/sidecar_examples.py` for more examples
3. **Run Benchmark**: `python tests/app/tool/benchmark_sidecar.py`
4. **Review Research**: See `RESEARCH_LLM_AGENT_EXECUTION_PATTERNS.md` for theory

---

## Quick Reference

### Create Sidecar
```python
class MySidecar(SidecarTool):
    name: str = "my_sidecar"
    sidecar_timeout: int = 30

    async def _execute_background(self, arguments):
        # Your code here
        return {"status": "done"}

MySidecar.register("my_sidecar")
```

### Add to Config
```json
{"tools": {"my_sidecar": {"enabled": true}}}
```

### Monitor
```python
from app.tool.sidecar_tool import get_sidecar_executor
metrics = get_sidecar_executor().get_metrics()
```

---

**That's it!** Your agent now has non-blocking background execution. 🚀

**Questions?** Check `SIDECAR_TOOLS_README.md` or ask the team!
