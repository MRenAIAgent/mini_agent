# Sidecar System Guide

## Overview

The **Sidecar System** enables non-blocking background operations for your agent, similar to Kubernetes sidecar containers. Sidecars run alongside the main agent execution without blocking the response to the user.

### Key Benefits

- **⚡ Faster Responses**: 30-50% reduction in response time
- **🔄 Non-Blocking**: Operations run in background
- **🛡️ Error Isolation**: Sidecar failures don't crash agent
- **📊 Built-in Analytics**: Automatic tracking and metrics

## How It Works

```
Traditional Agent Flow:
User Input → Execute → Store Memory (150ms) → Analytics (50ms) → Return Response
Total: ~200ms+ blocking

With Sidecars:
User Input → Execute → Trigger Sidecars (<1ms) → Return Response ⚡
                              ↓ (background)
                         Store Memory (150ms)
                         Analytics (50ms)
Total: ~1ms blocking, ~150ms saved!
```

## Quick Start

### 1. Basic Usage (Automatic)

Sidecars are **enabled by default** and run automatically:

```python
from agent import CoreAgent

# Create agent (sidecars enabled by default)
agent = CoreAgent(
    llm_config={"provider": "openai", "model": "gpt-4"},
    enable_memory=True,
    enable_sidecars=True  # Default: True
)

# Run agent
response = await agent.run("Hello, how are you?")
# Response returns immediately!
# Memory storage & analytics happen in background
```

**Default Sidecars:**
- `MemoryStoreSidecar`: Stores conversation in memory (if memory enabled)
- `AnalyticsSidecar`: Tracks execution metrics

### 2. Custom Sidecars

Create your own sidecars for custom background tasks:

```python
from sidecars import Sidecar

class NotificationSidecar(Sidecar):
    """Send notifications after agent execution"""

    name = "notification"
    description = "Send email notifications"
    timeout = 30  # 30 second timeout

    async def execute(self, context: dict):
        """
        Runs in background after agent completes.

        Context contains:
        - session_id
        - user_input
        - response
        - execution_result
        - timestamp
        - agent_state
        """
        # Send notification (doesn't block response!)
        await send_email(
            to="admin@example.com",
            subject=f"Agent Response for {context['session_id']}",
            body=context['response']
        )

        return {"notification_sent": True}

    async def on_success(self, result):
        """Called when sidecar succeeds"""
        logger.info(f"Notification sent: {result}")

    async def on_error(self, error):
        """Called when sidecar fails"""
        logger.error(f"Notification failed: {error}")

# Register sidecar
agent.register_sidecar(NotificationSidecar())
```

### 3. Conditional Execution

Control when sidecars execute:

```python
class ErrorNotificationSidecar(Sidecar):
    name = "error_notification"

    async def execute(self, context: dict):
        # Only runs if there's an error
        if not context["execution_result"]["success"]:
            await send_alert(
                message=f"Agent failed: {context['execution_result']['error_message']}"
            )

    def should_execute(self, context: dict) -> bool:
        """Only execute on failures"""
        result = context.get("execution_result", {})
        return not result.get("success", True)
```

## Built-in Sidecars

### MemoryStoreSidecar

Stores conversation in memory without blocking:

```python
from sidecars import MemoryStoreSidecar

# Automatically registered if memory enabled
# Or register manually:
memory_sidecar = MemoryStoreSidecar(agent.memory_manager)
agent.register_sidecar(memory_sidecar)
```

**Savings**: ~50-150ms per conversation

### AnalyticsSidecar

Tracks execution metrics:

```python
from sidecars import AnalyticsSidecar

analytics = AnalyticsSidecar()
agent.register_sidecar(analytics)

# Automatically tracks:
# - Response time
# - Iterations used
# - Success/failure rates
# - Tools called
```

### LoggingSidecar

Logs conversations for debugging:

```python
from sidecars import LoggingSidecar

logger = LoggingSidecar(
    log_file="agent_conversations.jsonl"
)
agent.register_sidecar(logger)

# Logs each conversation as JSON
# Doesn't block response!
```

### MetricsSidecar

Collects performance metrics:

```python
from sidecars import MetricsSidecar

metrics = MetricsSidecar()
agent.register_sidecar(metrics)

# Get metrics
stats = metrics.get_metrics()
print(f"Total executions: {stats['total_executions']}")
print(f"Success rate: {stats['total_success'] / stats['total_executions']}")
```

## Advanced Usage

### Managing Sidecars

```python
# List all sidecars
sidecars = agent.get_sidecars()
for sidecar in sidecars:
    print(f"- {sidecar.name}: {sidecar.description}")

# Remove a sidecar
agent.unregister_sidecar("analytics")

# Get statistics
stats = agent.get_sidecar_stats()
print(f"Active sidecars: {stats['active_tasks']}")
print(f"Completed: {stats['total_completed']}")
print(f"Failed: {stats['total_failed']}")
```

### Custom Timeouts

```python
class SlowOperationSidecar(Sidecar):
    name = "slow_operation"
    timeout = 300  # 5 minutes

    async def execute(self, context: dict):
        # Can take up to 5 minutes
        await slow_background_task()
```

### Error Handling

```python
class RobustSidecar(Sidecar):
    name = "robust"

    async def execute(self, context: dict):
        try:
            await risky_operation()
        except Exception as e:
            # Handle error locally
            logger.error(f"Operation failed: {e}")
            # Return partial result
            return {"status": "partial_failure", "error": str(e)}

    async def on_error(self, error: Exception):
        """Called if execute() raises unhandled exception"""
        await send_alert(f"Sidecar error: {error}")
```

### Access Agent State

```python
class SmartSidecar(Sidecar):
    name = "smart"

    async def execute(self, context: dict):
        # Access agent state
        agent_state = context["agent_state"]

        if agent_state["memory_enabled"]:
            # Do something with memory
            pass

        if agent_state["tools_available"] > 10:
            # Many tools available
            pass
```

## Configuration

### Sidecar Executor Settings

```python
from sidecars import SidecarExecutor, set_default_executor

# Create custom executor
executor = SidecarExecutor(
    max_concurrent=100,  # More concurrent sidecars
    default_timeout=120,  # 2 minute default
    track_tasks=True     # Track for debugging
)

# Set as default
set_default_executor(executor)
```

### Disable Sidecars

```python
# Disable all sidecars
agent = CoreAgent(
    llm_config=config,
    enable_sidecars=False  # No sidecars
)
```

### Disable Specific Sidecar

```python
# Disable without removing
sidecar.enabled = False

# Or remove completely
agent.unregister_sidecar("analytics")
```

## Best Practices

### ✅ Do's

1. **Use for non-critical operations**
   ```python
   # ✅ Good: Analytics, logging, notifications
   await analytics_sidecar.execute(context)
   ```

2. **Set appropriate timeouts**
   ```python
   # ✅ Fast operations: 5-30s
   timeout = 15

   # ✅ Slow operations: 1-5min
   timeout = 300
   ```

3. **Handle errors gracefully**
   ```python
   # ✅ Always implement error handling
   async def on_error(self, error):
       logger.error(f"Sidecar failed: {error}")
   ```

4. **Keep execution fast**
   ```python
   # ✅ Sidecars should complete quickly
   # Even though non-blocking, don't waste resources
   ```

### ❌ Don'ts

1. **Don't use for critical operations**
   ```python
   # ❌ Bad: User needs this data!
   # Don't use sidecar for data retrieval needed in response
   ```

2. **Don't block in sidecars**
   ```python
   # ❌ Bad: Blocking operation
   result = requests.get(url)  # Synchronous!

   # ✅ Good: Async operation
   result = await aiohttp.get(url)
   ```

3. **Don't rely on order**
   ```python
   # ❌ Bad: Sidecars run concurrently, order not guaranteed
   # Don't assume sidecar A completes before B
   ```

4. **Don't ignore errors silently**
   ```python
   # ❌ Bad: Silent failure
   async def execute(self, context):
       try:
           await operation()
       except:
           pass  # Lost!

   # ✅ Good: Log errors
   async def execute(self, context):
       try:
           await operation()
       except Exception as e:
           logger.error(f"Failed: {e}")
           raise
   ```

## Performance Impact

### Before Sidecars
```
User Input → Execute (200ms) → Store Memory (150ms) → Return
Total: 350ms to user
```

### After Sidecars
```
User Input → Execute (200ms) → Trigger Sidecars (<1ms) → Return
Total: 201ms to user (42% faster!)

Background:
  → Store Memory (150ms) [user doesn't wait]
  → Analytics (50ms)     [user doesn't wait]
```

### Real-World Impact

At 1000 requests/hour:
- **Time saved**: ~150ms × 1000 = 2.5 minutes/hour
- **Capacity increase**: ~42% more requests with same latency
- **User experience**: Faster responses

## Monitoring

### Check Sidecar Health

```python
# Get executor statistics
stats = agent.get_sidecar_stats()

print(f"Active: {stats['active_tasks']}")
print(f"Completed: {stats['total_completed']}")
print(f"Failed: {stats['total_failed']}")
print(f"Timeout: {stats['total_timeout']}")

# Per-sidecar stats
for name, sidecar_stats in stats['by_sidecar'].items():
    print(f"\n{name}:")
    print(f"  Started: {sidecar_stats['started']}")
    print(f"  Completed: {sidecar_stats['completed']}")
    print(f"  Failed: {sidecar_stats['failed']}")
    print(f"  Avg Time: {sidecar_stats['total_time'] / max(1, sidecar_stats['completed'])}s")
```

### Graceful Shutdown

```python
# Wait for sidecars before shutdown
await agent.stop()  # Waits up to 5s for sidecars

# Or force cancel
if agent.sidecar_executor:
    agent.sidecar_executor.cancel_all()
```

## Examples

### Example 1: Custom Analytics

```python
class CustomAnalyticsSidecar(Sidecar):
    name = "custom_analytics"

    def __init__(self, analytics_api):
        self.analytics_api = analytics_api

    async def execute(self, context: dict):
        # Track custom events
        await self.analytics_api.track({
            "event": "agent_response",
            "properties": {
                "session_id": context["session_id"],
                "response_length": len(context["response"]),
                "success": context["execution_result"]["success"]
            }
        })

# Register
analytics_sidecar = CustomAnalyticsSidecar(my_analytics_api)
agent.register_sidecar(analytics_sidecar)
```

### Example 2: Slack Notifications

```python
from slack_sdk.webhook.async_client import AsyncWebhookClient

class SlackNotificationSidecar(Sidecar):
    name = "slack_notification"
    timeout = 10

    def __init__(self, webhook_url: str):
        self.webhook = AsyncWebhookClient(webhook_url)

    async def execute(self, context: dict):
        # Notify on failures
        if not context["execution_result"]["success"]:
            await self.webhook.send(
                text=f"🚨 Agent Failed\n"
                     f"Session: {context['session_id']}\n"
                     f"Error: {context['execution_result']['error_message']}"
            )

    def should_execute(self, context: dict) -> bool:
        # Only on failures
        return not context["execution_result"].get("success", True)

# Register
slack_sidecar = SlackNotificationSidecar(
    webhook_url="https://hooks.slack.com/..."
)
agent.register_sidecar(slack_sidecar)
```

### Example 3: Database Logger

```python
class DatabaseLoggerSidecar(Sidecar):
    name = "database_logger"
    timeout = 30

    def __init__(self, db_connection):
        self.db = db_connection

    async def execute(self, context: dict):
        # Log to database
        await self.db.execute("""
            INSERT INTO agent_logs (
                session_id, user_input, response,
                success, timestamp
            ) VALUES ($1, $2, $3, $4, $5)
        """,
            context["session_id"],
            context["user_input"],
            context["response"],
            context["execution_result"]["success"],
            context["timestamp"]
        )

# Register
db_logger = DatabaseLoggerSidecar(db)
agent.register_sidecar(db_logger)
```

## Troubleshooting

### Sidecars Not Running

```python
# Check if sidecars enabled
print(f"Sidecars enabled: {agent.enable_sidecars}")

# List registered sidecars
print(f"Registered: {[s.name for s in agent.get_sidecars()]}")

# Check executor
if agent.sidecar_executor:
    print(f"Executor active: {agent.sidecar_executor.active_count}")
```

### High Failure Rate

```python
stats = agent.get_sidecar_stats()
failure_rate = stats['total_failed'] / stats['total_started']

if failure_rate > 0.1:  # >10% failing
    print("High failure rate!")
    # Check per-sidecar stats
    for name, s_stats in stats['by_sidecar'].items():
        s_rate = s_stats['failed'] / s_stats['started']
        if s_rate > 0.1:
            print(f"  Problem sidecar: {name}")
```

### Memory Leaks

```python
# Sidecars cleanup automatically
# But check for accumulation:
print(f"Active tasks: {agent.sidecar_executor.active_count}")

# Force cleanup if needed
await agent.sidecar_executor.wait_all(timeout=10)
```

## API Reference

See [sidecars/README.md](../sidecars/README.md) for complete API documentation.

## FAQ

**Q: Do sidecars delay the response?**
A: No! Sidecars start in background and return immediately (<1ms).

**Q: What happens if a sidecar fails?**
A: Error is logged, on_error() callback is called, but agent continues normally.

**Q: Can sidecars access agent state?**
A: Yes, through the `context["agent_state"]` parameter.

**Q: How many sidecars can run concurrently?**
A: Default is 50. Configure with `SidecarExecutor(max_concurrent=100)`.

**Q: Can I wait for a sidecar to complete?**
A: Generally no (defeats the purpose), but you can wait during shutdown with `agent.stop()`.

**Q: Are sidecars thread-safe?**
A: Sidecars use asyncio, not threads. They're async-safe.

## Learn More

- [Sidecar Implementation Details](./SIDECAR_IMPLEMENTATION.md)
- [Example Sidecars](../sidecars/implementations.py)
- [Tests](../tests/test_sidecars.py)
