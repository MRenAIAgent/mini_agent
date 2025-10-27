"""
Tests for Sidecar System

Tests the sidecar pattern implementation including:
- Base sidecar functionality
- Sidecar executor
- Sidecar registry
- Agent integration
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from sidecars import (
    Sidecar,
    SidecarExecutor,
    SidecarRegistry,
    SidecarContext,
    MemoryStoreSidecar,
    AnalyticsSidecar,
    LoggingSidecar,
)


# Test sidecars
class SimpleSidecar(Sidecar):
    """Simple test sidecar"""
    name = "simple_sidecar"
    description = "Simple sidecar for testing"

    def __init__(self, name: str = "simple_sidecar"):
        self.name = name  # Allow custom name for testing
        self.executed = False
        self.context_received = None
        self.execution_count = 0

    async def execute(self, context: Dict[str, Any]):
        self.executed = True
        self.context_received = context
        self.execution_count += 1
        return {"status": "success"}


class SlowSidecar(Sidecar):
    """Sidecar that takes time to execute"""
    name = "slow_sidecar"
    timeout = 2

    async def execute(self, context: Dict[str, Any]):
        await asyncio.sleep(0.5)  # Simulate slow operation
        return {"status": "completed"}


class FailingSidecar(Sidecar):
    """Sidecar that fails"""
    name = "failing_sidecar"

    def __init__(self):
        self.error_callback_called = False

    async def execute(self, context: Dict[str, Any]):
        raise ValueError("Intentional failure")

    async def on_error(self, error: Exception):
        self.error_callback_called = True


# ============================================================================
# Base Sidecar Tests
# ============================================================================

class TestSidecarBase:
    """Test base sidecar functionality"""

    def test_sidecar_initialization(self):
        """Test sidecar initializes with correct attributes"""
        sidecar = SimpleSidecar()
        assert sidecar.name == "simple_sidecar"
        assert sidecar.enabled is True
        assert sidecar.timeout > 0

    @pytest.mark.asyncio
    async def test_sidecar_execute(self):
        """Test sidecar execute method"""
        sidecar = SimpleSidecar()
        context = {"session_id": "test", "data": "value"}

        result = await sidecar.execute(context)

        assert sidecar.executed is True
        assert sidecar.context_received == context
        assert result["status"] == "success"

    def test_sidecar_should_execute(self):
        """Test should_execute logic"""
        sidecar = SimpleSidecar()

        # Enabled by default
        assert sidecar.should_execute({}) is True

        # Disabled
        sidecar.enabled = False
        assert sidecar.should_execute({}) is False


# ============================================================================
# SidecarContext Tests
# ============================================================================

class TestSidecarContext:
    """Test SidecarContext"""

    def test_context_creation(self):
        """Test creating sidecar context"""
        ctx = SidecarContext(
            session_id="test-123",
            user_input="Hello",
            response="Hi there",
            execution_result={},
            timestamp=datetime.now(),
            agent_state={}
        )

        assert ctx.session_id == "test-123"
        assert ctx.user_input == "Hello"
        assert ctx.response == "Hi there"

    def test_context_to_dict(self):
        """Test converting context to dict"""
        timestamp = datetime.now()
        ctx = SidecarContext(
            session_id="test",
            user_input="input",
            response="response",
            execution_result={},
            timestamp=timestamp,
            agent_state={}
        )

        data = ctx.to_dict()

        assert data["session_id"] == "test"
        assert data["user_input"] == "input"
        assert isinstance(data["timestamp"], str)

    def test_context_from_dict(self):
        """Test creating context from dict"""
        data = {
            "session_id": "test",
            "user_input": "input",
            "response": "response",
            "execution_result": {},
            "timestamp": datetime.now().isoformat(),
            "agent_state": {}
        }

        ctx = SidecarContext.from_dict(data)

        assert ctx.session_id == "test"
        assert ctx.user_input == "input"


# ============================================================================
# SidecarRegistry Tests
# ============================================================================

class TestSidecarRegistry:
    """Test sidecar registry"""

    def test_registry_register(self):
        """Test registering sidecars"""
        registry = SidecarRegistry()
        sidecar = SimpleSidecar()

        registry.register(sidecar)

        assert len(registry) == 1
        assert "simple_sidecar" in registry
        assert registry.get("simple_sidecar") == sidecar

    def test_registry_unregister(self):
        """Test unregistering sidecars"""
        registry = SidecarRegistry()
        sidecar = SimpleSidecar()

        registry.register(sidecar)
        registry.unregister("simple_sidecar")

        assert len(registry) == 0
        assert "simple_sidecar" not in registry

    def test_registry_get_all(self):
        """Test getting all sidecars"""
        registry = SidecarRegistry()
        sidecar1 = SimpleSidecar("sidecar1")
        sidecar2 = SlowSidecar()

        registry.register(sidecar1)
        registry.register(sidecar2)

        all_sidecars = registry.get_all()
        assert len(all_sidecars) == 2

    def test_registry_get_enabled(self):
        """Test getting only enabled sidecars"""
        registry = SidecarRegistry()
        sidecar1 = SimpleSidecar("sidecar1")
        sidecar2 = SimpleSidecar("sidecar2")
        sidecar2.enabled = False

        registry.register(sidecar1)
        registry.register(sidecar2)

        enabled = registry.get_enabled()
        assert len(enabled) == 1


# ============================================================================
# SidecarExecutor Tests
# ============================================================================

class TestSidecarExecutor:
    """Test sidecar executor"""

    @pytest.mark.asyncio
    async def test_executor_execute_one(self):
        """Test executing a single sidecar"""
        executor = SidecarExecutor()
        sidecar = SimpleSidecar()
        context = {"session_id": "test", "data": "value"}

        task = executor.execute_one(sidecar, context)
        assert task is not None

        # Wait for completion
        await executor.wait_all(timeout=1.0)

        assert sidecar.executed is True
        assert sidecar.execution_count == 1

    @pytest.mark.asyncio
    async def test_executor_execute_all(self):
        """Test executing multiple sidecars"""
        executor = SidecarExecutor()
        sidecar1 = SimpleSidecar("sidecar1")
        sidecar2 = SimpleSidecar("sidecar2")
        sidecars = [sidecar1, sidecar2]

        context = {"session_id": "test"}

        count = executor.execute_all(sidecars, context)
        assert count == 2

        await executor.wait_all(timeout=1.0)

        assert sidecar1.executed is True
        assert sidecar2.executed is True

    @pytest.mark.asyncio
    async def test_executor_error_handling(self):
        """Test executor handles errors gracefully"""
        executor = SidecarExecutor()
        failing_sidecar = FailingSidecar()

        context = {"session_id": "test"}

        executor.execute_one(failing_sidecar, context)
        await executor.wait_all(timeout=1.0)

        # Error callback should be called
        assert failing_sidecar.error_callback_called is True

        # Check stats
        stats = executor.get_stats()
        assert stats["total_failed"] > 0

    @pytest.mark.asyncio
    async def test_executor_timeout(self):
        """Test executor handles timeouts"""
        executor = SidecarExecutor(default_timeout=0.1)

        class TimeoutSidecar(Sidecar):
            name = "timeout_sidecar"
            timeout = 0.1

            async def execute(self, context):
                await asyncio.sleep(1.0)  # Longer than timeout

        sidecar = TimeoutSidecar()
        executor.execute_one(sidecar, {"test": "data"})

        await executor.wait_all(timeout=1.0)

        stats = executor.get_stats()
        assert stats["total_timeout"] > 0

    @pytest.mark.asyncio
    async def test_executor_concurrent_limit(self):
        """Test executor respects concurrent limit"""
        executor = SidecarExecutor(max_concurrent=2)

        sidecars = [SlowSidecar() for _ in range(5)]
        context = {"session_id": "test"}

        # Try to execute more than max_concurrent
        for sidecar in sidecars[:3]:
            executor.execute_one(sidecar, context)

        # Should only have 2 active at most
        assert executor.active_count <= 2

        await executor.wait_all(timeout=5.0)

    @pytest.mark.asyncio
    async def test_executor_stats(self):
        """Test executor statistics"""
        executor = SidecarExecutor()
        sidecar = SimpleSidecar()

        executor.execute_one(sidecar, {"test": "data"})
        await executor.wait_all(timeout=1.0)

        stats = executor.get_stats()

        assert stats["total_started"] == 1
        assert stats["total_completed"] == 1
        assert "simple_sidecar" in stats["by_sidecar"]


# ============================================================================
# Implementation Tests
# ============================================================================

class TestMemoryStoreSidecar:
    """Test memory storage sidecar"""

    @pytest.mark.asyncio
    async def test_memory_store_sidecar(self):
        """Test memory store sidecar execution"""
        # Mock memory manager
        class MockMemoryManager:
            def __init__(self):
                self.stored = False

            async def add_conversation_turn(self, **kwargs):
                self.stored = True

        memory_manager = MockMemoryManager()
        sidecar = MemoryStoreSidecar(memory_manager)

        context = {
            "session_id": "test",
            "user_input": "Hello",
            "response": "Hi",
            "execution_result": {}
        }

        result = await sidecar.execute(context)

        assert memory_manager.stored is True
        assert result["status"] == "stored"


class TestAnalyticsSidecar:
    """Test analytics sidecar"""

    @pytest.mark.asyncio
    async def test_analytics_sidecar(self):
        """Test analytics sidecar execution"""
        sidecar = AnalyticsSidecar()

        context = {
            "session_id": "test",
            "user_input": "Hello world",
            "response": "Hi there",
            "execution_result": {
                "iterations_used": 3,
                "success": True
            },
            "timestamp": datetime.now()
        }

        result = await sidecar.execute(context)

        assert "event" in result
        assert result["event"] == "agent_response"
        assert "metrics" in result


# ============================================================================
# Integration Tests (requires full agent)
# ============================================================================

@pytest.mark.asyncio
async def test_sidecar_non_blocking():
    """
    Test that sidecars don't block execution.

    This is the key property of sidecars!
    """
    executor = SidecarExecutor()

    # Create a slow sidecar
    slow_sidecar = SlowSidecar()

    context = {"test": "data"}

    # Start time
    import time
    start = time.time()

    # Execute sidecar (should NOT block)
    executor.execute_one(slow_sidecar, context)

    # This should return immediately
    elapsed = time.time() - start

    # Should be < 100ms (not the 500ms the sidecar takes)
    assert elapsed < 0.1, f"Sidecar blocked for {elapsed}s!"

    # Wait for sidecar to complete
    await executor.wait_all(timeout=2.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
