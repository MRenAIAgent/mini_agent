"""
TDD Tests for Memory Sidecar System

Following Test-Driven Development:
1. Write failing tests first (RED)
2. Implement minimal code to pass (GREEN)
3. Refactor while keeping tests green (REFACTOR)
"""

import pytest
import asyncio
import time
from typing import Dict, List, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor


# ============================================================================
# TEST SUITE 1: Core Sidecar Interface (RED phase - these will fail initially)
# ============================================================================

class TestMemorySidecarInterface:
    """Test the core sidecar interface"""

    @pytest.fixture
    def sidecar(self):
        """Create a sidecar instance for testing"""
        from memory_sidecar import MemorySidecar
        return MemorySidecar(backend="mock")

    def test_sidecar_initialization(self, sidecar):
        """Test that sidecar initializes correctly"""
        assert sidecar is not None
        assert sidecar.is_running() is True

    def test_sidecar_health_check(self, sidecar):
        """Test health check returns True when healthy"""
        assert sidecar.health_check() is True

    def test_sidecar_shutdown(self, sidecar):
        """Test graceful shutdown"""
        sidecar.shutdown()
        assert sidecar.is_running() is False


class TestMemoryFuture:
    """Test the Future/Promise pattern for async operations"""

    @pytest.fixture
    def sidecar(self):
        from memory_sidecar import MemorySidecar
        return MemorySidecar(backend="mock")

    @pytest.mark.asyncio
    async def test_store_returns_future(self, sidecar):
        """Test that store() returns a MemoryFuture immediately"""
        from memory_sidecar import MemoryFuture

        future = await sidecar.store("test content", metadata={"key": "value"})

        assert isinstance(future, MemoryFuture)
        assert future is not None

    @pytest.mark.asyncio
    async def test_future_is_ready_eventually(self, sidecar):
        """Test that future becomes ready after operation completes"""
        future = await sidecar.store("test content")

        # Should not be ready immediately (non-blocking!)
        # But should become ready within reasonable time
        await asyncio.sleep(0.1)  # Give it time to complete

        assert future.is_ready() is True

    @pytest.mark.asyncio
    async def test_future_result_blocks_until_ready(self, sidecar):
        """Test that result() blocks until operation completes"""
        future = await sidecar.store("test content")

        start_time = time.time()
        result = await future.result(timeout=2.0)
        elapsed = time.time() - start_time

        assert result is not None
        assert elapsed < 2.0  # Should complete quickly

    @pytest.mark.asyncio
    async def test_future_timeout(self, sidecar):
        """Test that result() raises TimeoutError if operation takes too long"""
        from memory_sidecar import MemoryFuture, TimeoutError

        # Create a slow operation
        future = await sidecar.store("slow operation", metadata={"delay": 5.0})

        with pytest.raises(TimeoutError):
            await future.result(timeout=0.5)

    @pytest.mark.asyncio
    async def test_future_callback(self, sidecar):
        """Test that callbacks are called when operation completes"""
        callback_called = asyncio.Event()
        callback_result = None

        def callback(result):
            nonlocal callback_result
            callback_result = result
            callback_called.set()

        future = await sidecar.store("test content")
        future.add_callback(callback)

        # Wait for callback
        await asyncio.wait_for(callback_called.wait(), timeout=2.0)

        assert callback_result is not None


# ============================================================================
# TEST SUITE 2: Async Memory Operations (RED phase)
# ============================================================================

class TestAsyncMemoryOperations:
    """Test async store and retrieve operations"""

    @pytest.fixture
    def sidecar(self):
        from memory_sidecar import MemorySidecar
        return MemorySidecar(backend="mock")

    @pytest.mark.asyncio
    async def test_async_store_returns_memory_id(self, sidecar):
        """Test that store operation returns a memory ID"""
        future = await sidecar.store("test content")
        memory_id = await future.result()

        assert memory_id is not None
        assert isinstance(memory_id, str)
        assert len(memory_id) > 0

    @pytest.mark.asyncio
    async def test_async_retrieve_returns_results(self, sidecar):
        """Test that retrieve operation returns results"""
        # Store first
        store_future = await sidecar.store("Python is a programming language")
        await store_future.result()

        # Then retrieve
        retrieve_future = await sidecar.retrieve("programming", k=5)
        results = await retrieve_future.result()

        assert isinstance(results, list)
        assert len(results) > 0
        assert "content" in results[0]

    @pytest.mark.asyncio
    async def test_multiple_concurrent_operations(self, sidecar):
        """Test handling multiple concurrent operations"""
        # Start multiple operations concurrently
        futures = []
        for i in range(10):
            future = await sidecar.store(f"content {i}")
            futures.append(future)

        # All should complete successfully
        results = await asyncio.gather(*[f.result() for f in futures])

        assert len(results) == 10
        assert all(r is not None for r in results)

    @pytest.mark.asyncio
    async def test_priority_operations(self, sidecar):
        """Test that high-priority operations are processed first"""
        # Create low priority operation
        low_priority = await sidecar.store("low priority", priority=0)

        # Create high priority operation (should jump queue)
        high_priority = await sidecar.store("high priority", priority=10)

        # High priority should complete first or at least very quickly
        start = time.time()
        await high_priority.result(timeout=1.0)
        high_time = time.time() - start

        assert high_time < 0.5  # Should be very fast


# ============================================================================
# TEST SUITE 3: Synchronous Fallback Operations (RED phase)
# ============================================================================

class TestSyncOperations:
    """Test synchronous/blocking operations for critical paths"""

    @pytest.fixture
    def sidecar(self):
        from memory_sidecar import MemorySidecar
        return MemorySidecar(backend="mock")

    def test_sync_store(self, sidecar):
        """Test synchronous store operation"""
        memory_id = sidecar.store_sync("critical content", metadata={"critical": True})

        assert memory_id is not None
        assert isinstance(memory_id, str)

    def test_sync_retrieve(self, sidecar):
        """Test synchronous retrieve operation"""
        # Store first
        sidecar.store_sync("test content about Python")

        # Retrieve synchronously
        results = sidecar.retrieve_sync("Python", k=5)

        assert isinstance(results, list)
        assert len(results) > 0

    def test_sync_operations_block_until_complete(self, sidecar):
        """Test that sync operations actually block"""
        start_time = time.time()
        sidecar.store_sync("blocking content")
        elapsed = time.time() - start_time

        # Should take some time (not return immediately)
        assert elapsed > 0.01  # At least some processing time


# ============================================================================
# TEST SUITE 4: Non-Blocking Behavior (RED phase)
# ============================================================================

class TestNonBlockingBehavior:
    """Test that async operations truly don't block"""

    @pytest.fixture
    def sidecar(self):
        from memory_sidecar import MemorySidecar
        return MemorySidecar(backend="mock")

    @pytest.mark.asyncio
    async def test_store_returns_immediately(self, sidecar):
        """Test that async store returns immediately (< 10ms)"""
        start_time = time.time()
        future = await sidecar.store("test content")
        elapsed = time.time() - start_time

        # Should return immediately, definitely under 10ms
        assert elapsed < 0.01
        assert future is not None

    @pytest.mark.asyncio
    async def test_retrieve_returns_immediately(self, sidecar):
        """Test that async retrieve returns immediately"""
        start_time = time.time()
        future = await sidecar.retrieve("test query")
        elapsed = time.time() - start_time

        # Should return immediately
        assert elapsed < 0.01
        assert future is not None

    @pytest.mark.asyncio
    async def test_agent_can_continue_while_memory_processes(self, sidecar):
        """Test that agent can do other work while memory operations complete"""
        # Start a memory operation
        memory_future = await sidecar.store("background operation")

        # Agent should be able to do other work
        agent_work_done = False
        for i in range(100):
            # Simulate agent work
            _ = i * i
            agent_work_done = True

        # Agent work completed while memory still processing
        assert agent_work_done is True

        # Memory operation should also complete
        result = await memory_future.result(timeout=2.0)
        assert result is not None


# ============================================================================
# TEST SUITE 5: Agent Integration (RED phase)
# ============================================================================

class TestAgentIntegration:
    """Test integration of sidecar with agent"""

    @pytest.fixture
    def agent_with_sidecar(self):
        from memory_sidecar import MemorySidecar
        from simple_agent import Agent  # Assuming we have a simple agent

        sidecar = MemorySidecar(backend="mock")
        agent = Agent(memory_sidecar=sidecar)
        return agent

    @pytest.mark.asyncio
    async def test_agent_can_store_memory(self, agent_with_sidecar):
        """Test that agent can store memories through sidecar"""
        agent = agent_with_sidecar

        await agent.remember("User prefers Python")

        # Should not raise any errors
        assert True

    @pytest.mark.asyncio
    async def test_agent_can_retrieve_memory(self, agent_with_sidecar):
        """Test that agent can retrieve memories"""
        agent = agent_with_sidecar

        # Store something
        await agent.remember("User loves machine learning")

        # Retrieve it
        memories = await agent.recall("machine learning")

        assert len(memories) > 0

    @pytest.mark.asyncio
    async def test_agent_transparently_uses_sidecar(self, agent_with_sidecar):
        """Test that agent code doesn't need to know about sidecar details"""
        agent = agent_with_sidecar

        # Agent should just call remember/recall without worrying about async
        await agent.remember("Test memory")
        results = await agent.recall("Test")

        assert results is not None


# ============================================================================
# TEST SUITE 6: Error Handling and Fault Tolerance (RED phase)
# ============================================================================

class TestErrorHandling:
    """Test error handling and fault tolerance"""

    @pytest.fixture
    def sidecar(self):
        from memory_sidecar import MemorySidecar
        return MemorySidecar(backend="mock")

    @pytest.mark.asyncio
    async def test_backend_failure_returns_error(self, sidecar):
        """Test that backend failures are properly reported"""
        from memory_sidecar import MemoryError

        # Simulate backend failure
        future = await sidecar.store("fail this operation", metadata={"should_fail": True})

        with pytest.raises(MemoryError):
            await future.result()

    @pytest.mark.asyncio
    async def test_retry_on_transient_failure(self, sidecar):
        """Test automatic retry on transient failures"""
        # Store with transient failure (should retry and succeed)
        future = await sidecar.store("retry me", metadata={"transient_fail_count": 2})

        # Should eventually succeed after retries
        result = await future.result(timeout=5.0)
        assert result is not None

    def test_health_check_detects_unhealthy_backend(self, sidecar):
        """Test that health check detects backend issues"""
        # Simulate unhealthy backend
        sidecar._simulate_backend_failure()

        assert sidecar.health_check() is False

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self, sidecar):
        """Test circuit breaker pattern"""
        from memory_sidecar import CircuitBreakerOpen

        # Cause multiple failures
        for i in range(5):
            try:
                future = await sidecar.store(f"fail {i}", metadata={"should_fail": True})
                await future.result()
            except:
                pass

        # Circuit should now be open
        with pytest.raises(CircuitBreakerOpen):
            future = await sidecar.store("this should fail fast")
            await future.result()


# ============================================================================
# TEST SUITE 7: Performance and Stress Tests (RED phase)
# ============================================================================

class TestPerformance:
    """Test performance characteristics"""

    @pytest.fixture
    def sidecar(self):
        from memory_sidecar import MemorySidecar
        return MemorySidecar(backend="mock", workers=4)

    @pytest.mark.asyncio
    async def test_throughput_under_load(self, sidecar):
        """Test throughput with many concurrent operations"""
        num_operations = 1000
        start_time = time.time()

        # Create many operations
        futures = []
        for i in range(num_operations):
            future = await sidecar.store(f"content {i}")
            futures.append(future)

        # Wait for all to complete
        await asyncio.gather(*[f.result() for f in futures])

        elapsed = time.time() - start_time
        throughput = num_operations / elapsed

        # Should handle at least 100 ops/sec
        assert throughput > 100

    @pytest.mark.asyncio
    async def test_queue_backpressure(self, sidecar):
        """Test that queue handles backpressure correctly"""
        from memory_sidecar import QueueFullError

        # Fill up the queue
        futures = []
        for i in range(10000):  # Try to overflow
            try:
                future = await sidecar.store(f"content {i}")
                futures.append(future)
            except QueueFullError:
                # Expected - queue should reject when full
                break

        # Some operations should have been accepted
        assert len(futures) > 0

    @pytest.mark.asyncio
    async def test_memory_leak_prevention(self, sidecar):
        """Test that completed futures are cleaned up"""
        import sys

        initial_count = len(sidecar._futures)

        # Create and complete many operations
        for i in range(100):
            future = await sidecar.store(f"content {i}")
            await future.result()

        # Give GC a chance
        await asyncio.sleep(0.1)

        # Completed futures should be cleaned up
        final_count = len(sidecar._futures)
        assert final_count < initial_count + 10  # Allow some buffer


# ============================================================================
# TEST SUITE 8: Configuration and Backend Switching (RED phase)
# ============================================================================

class TestConfiguration:
    """Test configuration and backend management"""

    def test_configure_from_dict(self):
        """Test configuration from dictionary"""
        from memory_sidecar import MemorySidecar

        config = {
            "backend": "rag",
            "workers": 4,
            "queue_size": 5000,
            "cache_enabled": True
        }

        sidecar = MemorySidecar.from_config(config)

        assert sidecar is not None
        assert sidecar.config["backend"] == "rag"
        assert sidecar.config["workers"] == 4

    def test_hot_swap_backend(self):
        """Test switching backend without restart"""
        from memory_sidecar import MemorySidecar

        sidecar = MemorySidecar(backend="mock")

        # Switch to different backend
        sidecar.switch_backend("rag")

        assert sidecar.current_backend == "rag"

    @pytest.mark.asyncio
    async def test_multiple_backend_support(self):
        """Test using multiple backends simultaneously"""
        from memory_sidecar import MemorySidecar

        sidecar = MemorySidecar(backends=["mock", "rag"])

        # Store should work with routing
        future = await sidecar.store("content", backend="rag")
        result = await future.result()

        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
