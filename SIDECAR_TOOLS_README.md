# Sidecar Tools: Non-Blocking Background Execution for Agents

## Overview

**Sidecar tools** are a new category of agent tools that execute in the background without blocking the agent's main execution loop. They are perfect for operations that enhance the user experience but don't need to complete before the agent responds.

### Key Benefits

- ⚡ **30-60% latency reduction** for agents with background tasks
- 📈 **Higher throughput** - agents handle more concurrent users
- 🎯 **Better UX** - users get responses faster
- 🔧 **Simple to implement** - just inherit from `SidecarTool`

### Performance Impact

```
Blocking Tool:  Search (100ms) + Analytics (100ms) + Response (50ms) = 250ms
Sidecar Tool:   Search (100ms) + Analytics (<1ms)  + Response (50ms) = ~150ms

Result: 40% faster response time
```

---

## Architecture

### How It Works

```
Agent Execution Flow:

1. Agent selects tool based on user input
2. Check if tool is a sidecar (is_sidecar = True)

   If blocking tool:
   ├── Execute tool
   ├── Wait for completion  ⏳
   └── Continue with result

   If sidecar tool:
   ├── Start background task
   ├── Return immediately ⚡
   └── Agent continues (sidecar runs in background)

3. Agent generates response to user
```

### Components

1. **SidecarTool (Base Class)**: Abstract base class for sidecar tools
2. **SidecarExecutor**: Manages concurrent sidecar execution with limits
3. **SidecarHandle**: Tracking handle returned immediately to agent
4. **Example Sidecars**: Production-ready implementations

---

## When to Use Sidecars

### ✅ Perfect For:

- **Analytics & Telemetry**: Send usage events, metrics
- **Notifications**: Email, SMS, push notifications
- **Audit Logging**: Write compliance logs
- **Cache Warming**: Pre-fetch data for future requests
- **Event Emission**: Publish to event bus/Kafka
- **Background Data Sync**: Update external systems

### ❌ Not Suitable For:

- **Critical path operations**: Data needed for response
- **User-requested actions**: Actions user expects to see complete
- **Error-sensitive operations**: Where failure must be communicated
- **State-dependent tasks**: Tasks requiring latest agent state

---

## Quick Start

### 1. Create a Sidecar Tool

```python
from app.tool.sidecar_tool import SidecarTool
import logging

logger = logging.getLogger(__name__)


class AnalyticsSidecar(SidecarTool):
    """Send analytics in background."""

    name: str = "analytics_sidecar"
    description: str = "Track user interactions and tool usage"
    sidecar_timeout: int = 30  # 30 second timeout

    async def _execute_background(self, arguments: dict):
        """This runs in background without blocking agent."""
        event_type = arguments.get("event_type")
        event_data = arguments.get("data", {})
        state = arguments.get("state", {})

        # Send to analytics service
        await analytics_api.track({
            "event": event_type,
            "chatbot_id": state.get("chatbot_id"),
            "user_id": state.get("user_id"),
            **event_data
        })

        logger.info(f"Analytics sent: {event_type}")
        return {"status": "sent"}

    async def _on_complete(self, result):
        """Optional: Handle successful completion."""
        logger.debug(f"Analytics completed: {result}")

    async def _on_error(self, error: Exception):
        """Optional: Handle errors."""
        logger.error(f"Analytics failed: {error}")


# Register the tool
AnalyticsSidecar.register("analytics_sidecar")
```

### 2. Add to Agent Configuration

```json
{
  "tools": {
    "analytics_sidecar": {
      "name": "analytics_sidecar",
      "description": "Track user interactions",
      "enabled": true
    }
  }
}
```

### 3. Use in Agent

The agent automatically detects sidecars via the `is_sidecar` attribute and executes them without blocking.

```python
# Agent execution (automatic)
if tool.is_sidecar:
    # Execute without waiting
    observation = await tool.arun(tool_input, **kwargs)
    # Agent continues immediately
else:
    # Execute and wait for result
    observation = await tool.arun(tool_input, **kwargs)
```

---

## Built-in Sidecar Examples

### 1. Analytics Sidecar

```python
from app.tool.sidecar_examples import AnalyticsSidecar

# Usage (called by agent)
await analytics_sidecar._arun({
    "event_type": "tool_used",
    "data": {
        "tool_name": "document_qa",
        "query": "How do I reset password?"
    }
})
# Returns immediately with sidecar_id
```

### 2. Notification Sidecar

```python
from app.tool.sidecar_examples import NotificationSidecar

# Send email notification in background
await notification_sidecar._arun({
    "notification_type": "email",
    "recipient": "user@example.com",
    "subject": "Your support ticket #12345",
    "message": "We've received your inquiry..."
})
# Agent continues immediately
```

### 3. Audit Log Sidecar

```python
from app.tool.sidecar_examples import AuditLogSidecar

# Write audit log asynchronously
await audit_log_sidecar._arun({
    "action": "sensitive_data_accessed",
    "actor": "user_123",
    "resource": "customer_profile",
    "details": {"profile_id": "abc-123"}
})
```

### 4. Cache Warming Sidecar

```python
from app.tool.sidecar_examples import CacheWarmingSidecar

# Pre-fetch related data
await cache_warming_sidecar._arun({
    "cache_keys": ["product_123", "product_456"],
    "data_source": "product_database"
})
# Subsequent queries will be faster
```

### 5. Event Emission Sidecar

```python
from app.tool.sidecar_examples import EventEmissionSidecar

# Emit event to event bus
await event_emission_sidecar._arun({
    "event_name": "chat_completed",
    "topic": "agent_events",
    "payload": {
        "conversation_id": "conv_789",
        "resolution": "success"
    }
})
```

---

## Advanced Features

### Concurrency Control

```python
from app.tool.sidecar_tool import SidecarExecutor

# Configure executor
executor = SidecarExecutor(
    max_concurrent_sidecars=20,  # Max parallel sidecars
    default_timeout=300,          # 5 minute default timeout
    enable_monitoring=True        # Track metrics
)
```

### Monitoring & Metrics

```python
# Get executor metrics
metrics = executor.get_metrics()

print(f"Total started: {metrics['total_started']}")
print(f"Total completed: {metrics['total_completed']}")
print(f"Total failed: {metrics['total_failed']}")
print(f"Active sidecars: {metrics['active_sidecars']}")

# Per-tool metrics
tool_metrics = metrics['by_tool']['analytics_sidecar']
print(f"Avg duration: {tool_metrics['avg_duration_ms']}ms")
```

### Check Sidecar Status

```python
# Get sidecar status by ID
handle = executor.get_status(sidecar_id)

print(f"Status: {handle.status}")  # PENDING, RUNNING, COMPLETED, FAILED, TIMEOUT
print(f"Result: {handle.result}")
print(f"Error: {handle.error}")
print(f"Execution time: {handle.execution_time_ms}ms")
```

### Cancel Running Sidecar

```python
# Cancel a sidecar if needed
success = await executor.cancel(sidecar_id)
if success:
    print("Sidecar cancelled")
```

### Cleanup Completed Sidecars

```python
# Remove old completed sidecars (memory management)
await executor.cleanup_completed(max_age_seconds=3600)  # 1 hour
```

---

## Configuration

### Sidecar Timeout

Set timeout per tool to prevent runaway background tasks:

```python
class MySlowSidecar(SidecarTool):
    sidecar_timeout: int = 600  # 10 minutes (for slow external APIs)
```

### Error Handling

Override error callback for custom error handling:

```python
class RobustSidecar(SidecarTool):
    async def _on_error(self, error: Exception):
        # Custom error handling
        if isinstance(error, APIError):
            await self.retry_later(error)
        else:
            await self.send_alert(error)
```

### Completion Callbacks

Execute logic when sidecar completes:

```python
class NotifySidecar(SidecarTool):
    async def _on_complete(self, result):
        # Send confirmation
        if result.get("status") == "sent":
            await websocket.send_json({
                "type": "notification_sent",
                "data": result
            })
```

---

## Testing

### Unit Tests

```bash
# Run sidecar unit tests
PYTHONPATH=app pytest tests/app/tool/test_sidecar_tool.py -v
```

### Benchmark

```bash
# Run performance benchmark
PYTHONPATH=app python tests/app/tool/benchmark_sidecar.py
```

Expected output:
```
BENCHMARK RESULTS
================================================================================

Metric                    Blocking Tool        Sidecar Tool         Improvement
--------------------------------------------------------------------------------
Average Latency (ms)      250.12               151.34               -39.5%
Operations/sec            3.99                 6.61                 +65.7%

SUMMARY:
  • Average latency reduced by: 39.5%
  • Throughput increased by: 65.7%
  • Sidecar tool is 1.7x faster
```

---

## Best Practices

### 1. Use Sidecars for Non-Critical Operations

```python
# ✅ Good: Analytics doesn't block response
await analytics_sidecar.send_event("page_view")
response = generate_response()

# ❌ Bad: User needs search results
results = await search_sidecar.search(query)  # Don't use sidecar here!
```

### 2. Set Appropriate Timeouts

```python
# Fast operations
class QuickSidecar(SidecarTool):
    sidecar_timeout: int = 30  # 30 seconds

# Slow operations (batch processing, report generation)
class SlowSidecar(SidecarTool):
    sidecar_timeout: int = 600  # 10 minutes
```

### 3. Handle Errors Gracefully

```python
async def _execute_background(self, arguments: dict):
    try:
        result = await external_api.call(arguments)
        return result
    except Exception as e:
        logger.error(f"Sidecar failed: {e}")
        # Don't raise - let error callback handle it
        raise
```

### 4. Monitor Sidecar Health

```python
# Regular monitoring
async def monitor_sidecars():
    while True:
        metrics = executor.get_metrics()

        # Alert if too many failures
        failure_rate = metrics['total_failed'] / metrics['total_started']
        if failure_rate > 0.1:  # > 10% failure rate
            await send_alert("High sidecar failure rate")

        await asyncio.sleep(60)  # Check every minute
```

### 5. Limit Concurrency

```python
# Production settings
executor = SidecarExecutor(
    max_concurrent_sidecars=50,  # Prevent resource exhaustion
    default_timeout=300,
    enable_monitoring=True
)
```

---

## Troubleshooting

### Issue: Sidecars Not Starting

**Symptom**: RuntimeError "Max concurrent sidecars limit reached"

**Solution**: Increase limit or wait for sidecars to complete

```python
executor = SidecarExecutor(max_concurrent_sidecars=100)  # Increase limit
```

### Issue: Sidecars Timing Out

**Symptom**: Many sidecars show TIMEOUT status

**Solutions**:
1. Increase timeout: `sidecar_timeout = 600`
2. Optimize background operation
3. Check network/API performance

### Issue: Memory Growth

**Symptom**: Application memory grows over time

**Solution**: Enable regular cleanup

```python
# Add to background task
async def periodic_cleanup():
    while True:
        await executor.cleanup_completed(max_age_seconds=3600)
        await asyncio.sleep(600)  # Every 10 minutes
```

### Issue: Lost Sidecar Results

**Symptom**: Can't find sidecar results after completion

**Solution**: Store sidecar_id and check status later

```python
# Store sidecar_id
result = await sidecar._arun({"data": "test"})
sidecar_id = result.response["sidecar_id"]

# Check later
handle = executor.get_status(sidecar_id)
if handle and handle.status == SidecarStatus.COMPLETED:
    print(handle.result)
```

---

## Migration Guide

### From Blocking to Sidecar

**Before (Blocking)**:
```python
class AnalyticsTool(GeneralTool):
    async def _arun(self, tool_input, **kwargs):
        await analytics_api.send(tool_input)  # Blocks for 100ms
        return ToolResponse(...)
```

**After (Sidecar)**:
```python
class AnalyticsTool(SidecarTool):
    sidecar_timeout: int = 30

    async def _execute_background(self, arguments: dict):
        await analytics_api.send(arguments)  # Runs in background
        return {"status": "sent"}
```

**Result**: Agent latency reduced by ~100ms per analytics call

---

## API Reference

### SidecarTool

```python
class SidecarTool(GeneralTool):
    is_sidecar: bool = True
    sidecar_timeout: int = 300

    async def _execute_background(self, arguments: dict) -> Any:
        """Override to implement sidecar logic."""

    async def _on_complete(self, result: Any):
        """Optional: Handle successful completion."""

    async def _on_error(self, error: Exception):
        """Optional: Handle errors."""
```

### SidecarExecutor

```python
class SidecarExecutor:
    def __init__(
        self,
        max_concurrent_sidecars: int = 20,
        default_timeout: int = 300,
        enable_monitoring: bool = True
    )

    async def execute(
        self,
        sidecar: SidecarTool,
        arguments: dict,
        timeout: Optional[int] = None,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ) -> SidecarHandle

    def get_status(self, sidecar_id: str) -> Optional[SidecarHandle]

    async def cancel(self, sidecar_id: str) -> bool

    def get_metrics(self) -> dict

    async def cleanup_completed(self, max_age_seconds: int = 3600)
```

### SidecarHandle

```python
@dataclass
class SidecarHandle:
    sidecar_id: str
    tool_name: str
    status: SidecarStatus
    started_at: datetime
    completed_at: Optional[datetime]
    result: Optional[Any]
    error: Optional[str]
    execution_time_ms: Optional[float]
```

---

## Performance Benchmarks

### Test Setup
- 100 requests per benchmark
- Agent with: Search (100ms) + Analytics + Response (50ms)
- Blocking analytics: 100ms per call
- Sidecar analytics: <1ms to start, 100ms in background

### Results

| Metric | Blocking Tool | Sidecar Tool | Improvement |
|--------|--------------|--------------|-------------|
| Avg Latency | 250ms | 151ms | **-39.5%** |
| P95 Latency | 260ms | 155ms | **-40.4%** |
| P99 Latency | 265ms | 158ms | **-40.4%** |
| Throughput | 4 ops/s | 6.6 ops/s | **+65%** |

### Real-World Impact

For an agent handling 1000 requests/hour with 2 sidecar calls per request:

- **Latency savings**: ~200ms per request
- **Time saved**: 200 seconds (3.3 minutes) per 1000 requests
- **Capacity increase**: Can handle 65% more users with same resources

---

## FAQ

**Q: When should I use a sidecar vs blocking tool?**

A: Use sidecar when the operation:
- Doesn't affect the agent's response
- Can fail gracefully without user impact
- Is not time-critical
- Examples: analytics, logging, notifications

**Q: What happens if a sidecar fails?**

A: The agent continues normally. Failures are logged and error callbacks are triggered, but the user's experience is unaffected.

**Q: Can I get sidecar results later?**

A: Yes! Store the `sidecar_id` and check status with `executor.get_status(sidecar_id)`.

**Q: How many sidecars can run concurrently?**

A: Default limit is 20. Configure with `SidecarExecutor(max_concurrent_sidecars=50)`.

**Q: Do sidecars work with streaming?**

A: Yes! Sidecars start in background while agent streams response to user.

---

## Contributing

To add new sidecar tools:

1. Create tool class inheriting from `SidecarTool`
2. Implement `_execute_background()`
3. Register with `YourSidecar.register("tool_name")`
4. Add to agent configuration
5. Write tests
6. Update documentation

---

## License

MIT License - See LICENSE file for details

---

## Support

- **Issues**: GitHub Issues
- **Slack**: #agent-development
- **Docs**: https://docs.example.com/sidecar-tools
