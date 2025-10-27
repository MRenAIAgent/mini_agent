"""
Sidecar System Example

Demonstrates how to use sidecars for non-blocking background operations.
"""

import asyncio
import time
from typing import Dict, Any

# Mock LLM for testing
async def mock_llm(prompt: str) -> str:
    """Mock LLM that returns immediately"""
    await asyncio.sleep(0.1)  # Simulate quick LLM call
    return "This is a mock response to demonstrate sidecars!"


async def main():
    print("=" * 70)
    print("SIDECAR SYSTEM DEMONSTRATION")
    print("=" * 70)

    # Import agent
    try:
        from agent import CoreAgent
        from sidecars import Sidecar, LoggingSidecar
    except ImportError:
        import sys
        sys.path.insert(0, '..')
        from agent import CoreAgent
        from sidecars import Sidecar, LoggingSidecar

    # ========================================================================
    # Example 1: Basic Usage with Default Sidecars
    # ========================================================================
    print("\n📋 Example 1: Basic Usage with Default Sidecars\n")

    # Create agent (sidecars enabled by default)
    agent = CoreAgent(
        llm_function=mock_llm,
        enable_memory=True,
        enable_sidecars=True
    )

    await agent.start()

    print("Registered sidecars:")
    for sidecar in agent.get_sidecars():
        print(f"  - {sidecar.name}: {sidecar.description}")

    print("\nRunning agent...")
    start_time = time.time()

    response = await agent.run("Hello, what can you do?")

    elapsed = time.time() - start_time

    print(f"\n✅ Response received in {elapsed:.3f}s")
    print(f"📝 Response: {response[:100]}...")
    print("\n⚙️  Sidecars are running in background!")

    # Wait a bit to let sidecars complete
    await asyncio.sleep(0.5)

    # Check stats
    stats = agent.get_sidecar_stats()
    print(f"\n📊 Sidecar Statistics:")
    print(f"  Total started: {stats['total_started']}")
    print(f"  Total completed: {stats['total_completed']}")
    print(f"  Total failed: {stats['total_failed']}")

    # ========================================================================
    # Example 2: Custom Sidecar
    # ========================================================================
    print("\n" + "=" * 70)
    print("📋 Example 2: Custom Sidecar\n")

    class TimingSidecar(Sidecar):
        """Track timing metrics"""
        name = "timing"
        description = "Track response times"

        def __init__(self):
            self.timings = []

        async def execute(self, context: Dict[str, Any]):
            # Simulate slow operation (doesn't block response!)
            await asyncio.sleep(0.2)

            # Calculate timing
            result = context["execution_result"]
            if "start_time" in result and "end_time" in result:
                duration = (result["end_time"] - result["start_time"]).total_seconds()
                self.timings.append(duration)

            return {"timing_recorded": True}

        async def on_success(self, result):
            print(f"    ⏱️  Timing recorded: {result}")

    # Register custom sidecar
    timing_sidecar = TimingSidecar()
    agent.register_sidecar(timing_sidecar)

    print("Running agent with custom sidecar...")
    start_time = time.time()

    response = await agent.run("Tell me about sidecars")

    elapsed = time.time() - start_time

    print(f"✅ Response received in {elapsed:.3f}s (sidecar running in background)")

    # Wait for sidecar
    await asyncio.sleep(0.5)

    print(f"✅ All timings: {timing_sidecar.timings}")

    # ========================================================================
    # Example 3: Conditional Execution
    # ========================================================================
    print("\n" + "=" * 70)
    print("📋 Example 3: Conditional Execution\n")

    class ErrorAlertSidecar(Sidecar):
        """Alert on errors only"""
        name = "error_alert"
        description = "Send alerts on errors"

        def __init__(self):
            self.alerts_sent = 0

        async def execute(self, context: Dict[str, Any]):
            # This only runs on failures
            print(f"    🚨 ALERT: Agent execution failed!")
            print(f"       Error: {context['execution_result']['error_message']}")
            self.alerts_sent += 1

        def should_execute(self, context: Dict[str, Any]) -> bool:
            """Only execute on failures"""
            result = context.get("execution_result", {})
            return not result.get("success", True)

    # Register alert sidecar
    alert_sidecar = ErrorAlertSidecar()
    agent.register_sidecar(alert_sidecar)

    # Run with success (alert should NOT trigger)
    print("Running agent (should succeed)...")
    response = await agent.run("Hello")
    await asyncio.sleep(0.2)
    print(f"  Alerts sent: {alert_sidecar.alerts_sent} (expected: 0)")

    # Trigger failure scenario would look like:
    # response = await agent.run("trigger_error")
    # Alert sidecar would execute

    # ========================================================================
    # Example 4: Performance Comparison
    # ========================================================================
    print("\n" + "=" * 70)
    print("📋 Example 4: Performance Impact\n")

    # Simulate slow sidecar
    class SlowAnalyticsSidecar(Sidecar):
        name = "slow_analytics"
        description = "Slow analytics (simulated)"

        async def execute(self, context: Dict[str, Any]):
            # Simulate slow operation (150ms)
            await asyncio.sleep(0.15)
            return {"analytics_sent": True}

    # Create agent WITH sidecars
    agent_with_sidecars = CoreAgent(
        llm_function=mock_llm,
        enable_memory=True,
        enable_sidecars=True
    )
    agent_with_sidecars.register_sidecar(SlowAnalyticsSidecar())
    await agent_with_sidecars.start()

    # Measure time WITH sidecars
    start = time.time()
    response = await agent_with_sidecars.run("Test with sidecars")
    time_with_sidecars = time.time() - start

    print(f"⚡ With sidecars (non-blocking): {time_with_sidecars:.3f}s")

    # Simulate WITHOUT sidecars (blocking)
    async def simulate_blocking():
        start = time.time()
        # Execute
        await asyncio.sleep(0.1)  # LLM
        # Block on analytics
        await asyncio.sleep(0.15)  # Analytics (blocking!)
        return time.time() - start

    time_without_sidecars = await simulate_blocking()
    print(f"🐌 Without sidecars (blocking):  {time_without_sidecars:.3f}s")

    savings = time_without_sidecars - time_with_sidecars
    percent = (savings / time_without_sidecars) * 100
    print(f"\n💰 Time saved: {savings:.3f}s ({percent:.1f}% faster!)")

    # ========================================================================
    # Example 5: Multiple Concurrent Sidecars
    # ========================================================================
    print("\n" + "=" * 70)
    print("📋 Example 5: Multiple Concurrent Sidecars\n")

    # Register multiple sidecars
    sidecars = [
        ("sidecar_1", 0.1),
        ("sidecar_2", 0.2),
        ("sidecar_3", 0.15),
    ]

    for name, delay in sidecars:
        class DynamicSidecar(Sidecar):
            def __init__(self, sidecar_name, sidecar_delay):
                self.name = sidecar_name
                self.description = f"Sidecar {sidecar_name}"
                self.delay = sidecar_delay

            async def execute(self, context):
                await asyncio.sleep(self.delay)
                return {"name": self.name, "completed": True}

            async def on_success(self, result):
                print(f"    ✓ {result['name']} completed")

        agent_with_sidecars.register_sidecar(DynamicSidecar(name, delay))

    print("Running agent with 3 concurrent sidecars...")
    start = time.time()

    response = await agent_with_sidecars.run("Test concurrent")

    elapsed = time.time() - start
    print(f"\n✅ Response in {elapsed:.3f}s (all 3 sidecars running in background)")

    # Wait for all sidecars
    await asyncio.sleep(0.3)
    print("✅ All sidecars completed!")

    # ========================================================================
    # Final Stats
    # ========================================================================
    print("\n" + "=" * 70)
    print("📊 Final Statistics\n")

    stats = agent_with_sidecars.get_sidecar_stats()
    print(f"Total executions: {stats['total_started']}")
    print(f"Completed: {stats['total_completed']}")
    print(f"Failed: {stats['total_failed']}")
    print(f"Active: {stats['active_tasks']}")

    print("\nPer-sidecar stats:")
    for name, sidecar_stats in stats['by_sidecar'].items():
        if sidecar_stats['started'] > 0:
            print(f"  {name}:")
            print(f"    Started: {sidecar_stats['started']}")
            print(f"    Completed: {sidecar_stats['completed']}")

    # Cleanup
    await agent.stop()
    await agent_with_sidecars.stop()

    print("\n" + "=" * 70)
    print("✨ DEMONSTRATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
