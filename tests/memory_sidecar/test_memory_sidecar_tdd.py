"""
TDD Tests for Memory Sidecar Implementation

RED → GREEN → REFACTOR cycle

Test Suite covers:
1. Core sidecar interface
2. Non-blocking store operations
3. Smart retrieve (async/sync modes)
4. Backend adapters
5. Agent integration
6. Performance characteristics
"""

import pytest
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, patch


# ============================================================================
# TEST SUITE 1: Core Memory Sidecar Interface (RED - These will fail initially)
# ============================================================================

class TestMemorySidecarBase:
    """Test the base memory sidecar interface"""

    @pytest.fixture
    def memory_sidecar(self):
        """Create memory sidecar instance for testing"""
        from memory_sidecar.memory_store_sidecar import MemoryStoreSidecar
        return MemoryStoreSidecar()

    def test_sidecar_initialization(self, memory_sidecar):
        """Test that memory sidecar initializes correctly"""
        assert memory_sidecar is not None
        assert memory_sidecar.is_sidecar is True
        assert hasattr(memory_sidecar, '_execute_background')

    def test_sidecar_has_correct_attributes(self, memory_sidecar):
        """Test sidecar has required attributes"""
        assert hasattr(memory_sidecar, 'name')
        assert hasattr(memory_sidecar, 'description')
        assert hasattr(memory_sidecar, 'sidecar_timeout')
        assert memory_sidecar.sidecar_timeout > 0


# ============================================================================
# TEST SUITE 2: Non-Blocking Store Operations (RED)
# ============================================================================

class TestMemoryStoreNonBlocking:
    """Test non-blocking memory store operations"""

    @pytest.fixture
    def store_sidecar(self):
        from memory_sidecar.memory_store_sidecar import MemoryStoreSidecar
        return MemoryStoreSidecar(backend="mock")

    @pytest.mark.asyncio
    async def test_store_returns_immediately(self, store_sidecar):
        """Test that store returns immediately (< 5ms)"""
        start_time = time.time()

        # This should return immediately, not wait for actual storage
        result = await store_sidecar._arun({
            "content": "User prefers Python",
            "metadata": {"type": "preference"}
        })

        elapsed = time.time() - start_time

        # Should return in less than 5ms (non-blocking)
        assert elapsed < 0.005
        assert result is not None
        assert "sidecar_id" in result.response

    @pytest.mark.asyncio
    async def test_store_executes_in_background(self, store_sidecar):
        """Test that actual storage happens in background"""
        # Store something
        result = await store_sidecar._arun({
            "content": "Background storage test"
        })

        sidecar_id = result.response["sidecar_id"]

        # Give background task time to complete
        await asyncio.sleep(0.2)

        # Check that it actually executed
        from memory_sidecar.executor import get_sidecar_executor
        executor = get_sidecar_executor()
        handle = executor.get_status(sidecar_id)

        assert handle is not None
        assert handle.status in ["completed", "running"]

    @pytest.mark.asyncio
    async def test_multiple_concurrent_stores(self, store_sidecar):
        """Test handling multiple concurrent store operations"""
        # Start many stores concurrently
        tasks = []
        for i in range(20):
            task = store_sidecar._arun({
                "content": f"Memory {i}",
                "metadata": {"index": i}
            })
            tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        # All should return quickly (non-blocking)
        assert elapsed < 0.1  # 100ms for 20 operations
        assert len(results) == 20
        assert all("sidecar_id" in r.response for r in results)

    @pytest.mark.asyncio
    async def test_store_with_different_backends(self, store_sidecar):
        """Test storing to different backend types"""
        backends = ["mock", "rag", "memgpt"]

        for backend in backends:
            result = await store_sidecar._arun({
                "content": f"Test {backend}",
                "backend": backend
            })

            assert result is not None
            assert "sidecar_id" in result.response


# ============================================================================
# TEST SUITE 3: Smart Retrieve Operations (RED)
# ============================================================================

class TestMemoryRetrieveSmart:
    """Test smart retrieve with async/sync modes"""

    @pytest.fixture
    def retrieve_sidecar(self):
        from memory_sidecar.memory_retrieve_sidecar import MemoryRetrieveSidecar
        return MemoryRetrieveSidecar(backend="mock")

    @pytest.mark.asyncio
    async def test_async_retrieve_returns_immediately(self, retrieve_sidecar):
        """Test async retrieve returns immediately"""
        start_time = time.time()

        result = await retrieve_sidecar._arun({
            "query": "test query",
            "k": 5
        })

        elapsed = time.time() - start_time

        # Should return quickly in async mode
        assert elapsed < 0.01
        assert result is not None

    @pytest.mark.asyncio
    async def test_sync_retrieve_waits_for_results(self, retrieve_sidecar):
        """Test sync mode retrieves actually waits and returns results"""
        result = await retrieve_sidecar._arun({
            "query": "important query",
            "k": 3,
            "force_sync": True  # Force synchronous retrieval
        })

        # Should have actual results
        assert "results" in result.response
        assert isinstance(result.response["results"], list)

    @pytest.mark.asyncio
    async def test_retrieve_with_cache(self, retrieve_sidecar):
        """Test that caching works for repeated queries"""
        query = "cached query"

        # First call - cache miss
        start1 = time.time()
        result1 = await retrieve_sidecar._arun({
            "query": query,
            "k": 5,
            "force_sync": True,
            "cache_enabled": True
        })
        time1 = time.time() - start1

        # Second call - should hit cache
        start2 = time.time()
        result2 = await retrieve_sidecar._arun({
            "query": query,
            "k": 5,
            "force_sync": True,
            "cache_enabled": True
        })
        time2 = time.time() - start2

        # Cache hit should be faster
        assert time2 < time1
        assert result2.response["results"] == result1.response["results"]

    @pytest.mark.asyncio
    async def test_retrieve_respects_k_parameter(self, retrieve_sidecar):
        """Test that k parameter limits results"""
        for k in [1, 3, 5, 10]:
            result = await retrieve_sidecar._arun({
                "query": "test",
                "k": k,
                "force_sync": True
            })

            results = result.response["results"]
            assert len(results) <= k


# ============================================================================
# TEST SUITE 4: Backend Adapters (RED)
# ============================================================================

class TestMemoryBackendAdapters:
    """Test memory backend adapters"""

    def test_backend_interface(self):
        """Test that backend interface is properly defined"""
        from memory_sidecar.backends.base import MemoryBackend

        # Check interface methods exist
        assert hasattr(MemoryBackend, 'store')
        assert hasattr(MemoryBackend, 'retrieve')
        assert hasattr(MemoryBackend, 'delete')

    @pytest.mark.asyncio
    async def test_mock_backend_store(self):
        """Test mock backend store operation"""
        from memory_sidecar.backends.mock_backend import MockMemoryBackend

        backend = MockMemoryBackend()

        memory_id = await backend.store(
            content="test content",
            metadata={"key": "value"}
        )

        assert memory_id is not None
        assert isinstance(memory_id, str)

    @pytest.mark.asyncio
    async def test_mock_backend_retrieve(self):
        """Test mock backend retrieve operation"""
        from memory_sidecar.backends.mock_backend import MockMemoryBackend

        backend = MockMemoryBackend()

        # Store first
        await backend.store("Python is great", {"type": "fact"})

        # Retrieve
        results = await backend.retrieve("Python", k=5)

        assert isinstance(results, list)
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_rag_backend_integration(self):
        """Test RAG backend adapter"""
        from memory_sidecar.backends.rag_backend import RAGMemoryBackend

        backend = RAGMemoryBackend(
            embedding_model="all-MiniLM-L6-v2"
        )

        # Store
        memory_id = await backend.store(
            content="Machine learning is a subset of AI",
            metadata={"domain": "AI"}
        )

        assert memory_id is not None

        # Retrieve
        results = await backend.retrieve("AI", k=3)
        assert len(results) <= 3


# ============================================================================
# TEST SUITE 5: Agent Integration (RED)
# ============================================================================

class TestAgentIntegration:
    """Test integration with agent"""

    @pytest.fixture
    def agent_with_memory_sidecar(self):
        """Create agent with memory sidecar enabled"""
        from agent import Agent  # Assuming simple agent
        from memory_sidecar.memory_store_sidecar import MemoryStoreSidecar
        from memory_sidecar.memory_retrieve_sidecar import MemoryRetrieveSidecar

        agent = Agent(name="test_agent")
        agent.memory_store = MemoryStoreSidecar()
        agent.memory_retrieve = MemoryRetrieveSidecar()

        return agent

    @pytest.mark.asyncio
    async def test_agent_can_store_memory(self, agent_with_memory_sidecar):
        """Test agent can store memories via sidecar"""
        agent = agent_with_memory_sidecar

        # Agent stores memory
        await agent.memory_store._arun({
            "content": "User asked about Python"
        })

        # Should not raise any errors
        assert True

    @pytest.mark.asyncio
    async def test_agent_can_retrieve_memory(self, agent_with_memory_sidecar):
        """Test agent can retrieve memories"""
        agent = agent_with_memory_sidecar

        # Store something first
        await agent.memory_store._arun({
            "content": "Python is a programming language"
        })

        await asyncio.sleep(0.1)  # Let it complete

        # Retrieve
        result = await agent.memory_retrieve._arun({
            "query": "Python",
            "force_sync": True
        })

        assert "results" in result.response
        assert len(result.response["results"]) > 0

    @pytest.mark.asyncio
    async def test_agent_response_not_blocked_by_memory(self, agent_with_memory_sidecar):
        """Test that agent responses aren't blocked by memory operations"""
        agent = agent_with_memory_sidecar

        start_time = time.time()

        # Agent stores memory (should not block)
        await agent.memory_store._arun({
            "content": "Some interaction data"
        })

        # Agent continues to generate response
        response = await agent.generate_response("Hello")

        elapsed = time.time() - start_time

        # Should be fast (not waiting for memory storage)
        assert elapsed < 0.5  # Reasonable time for response generation
        assert response is not None


# ============================================================================
# TEST SUITE 6: Performance Characteristics (RED)
# ============================================================================

class TestPerformanceCharacteristics:
    """Test performance requirements"""

    @pytest.mark.asyncio
    async def test_store_latency_under_5ms(self):
        """Test store operation returns in < 5ms"""
        from memory_sidecar.memory_store_sidecar import MemoryStoreSidecar

        sidecar = MemoryStoreSidecar(backend="mock")

        latencies = []
        for i in range(100):
            start = time.time()
            await sidecar._arun({"content": f"test {i}"})
            latency = (time.time() - start) * 1000  # Convert to ms
            latencies.append(latency)

        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[94]  # 95th percentile

        assert avg_latency < 5.0  # Average under 5ms
        assert p95_latency < 10.0  # P95 under 10ms

    @pytest.mark.asyncio
    async def test_throughput_under_load(self):
        """Test throughput with many concurrent operations"""
        from memory_sidecar.memory_store_sidecar import MemoryStoreSidecar

        sidecar = MemoryStoreSidecar(backend="mock")

        num_operations = 100
        start_time = time.time()

        # Fire off many operations
        tasks = []
        for i in range(num_operations):
            task = sidecar._arun({"content": f"content {i}"})
            tasks.append(task)

        await asyncio.gather(*tasks)

        elapsed = time.time() - start_time
        throughput = num_operations / elapsed

        # Should handle at least 500 ops/sec
        assert throughput > 500

    @pytest.mark.asyncio
    async def test_memory_not_leaked(self):
        """Test that memory is properly cleaned up"""
        from memory_sidecar.memory_store_sidecar import MemoryStoreSidecar
        from memory_sidecar.executor import get_sidecar_executor

        sidecar = MemoryStoreSidecar(backend="mock")
        executor = get_sidecar_executor()

        initial_count = len(executor._sidecars)

        # Create many sidecars
        for i in range(50):
            await sidecar._arun({"content": f"test {i}"})

        await asyncio.sleep(0.3)  # Let them complete

        # Cleanup
        await executor.cleanup_completed(max_age_seconds=0)

        final_count = len(executor._sidecars)

        # Should have cleaned up completed ones
        assert final_count < initial_count + 10


# ============================================================================
# TEST SUITE 7: Error Handling (RED)
# ============================================================================

class TestErrorHandling:
    """Test error scenarios"""

    @pytest.mark.asyncio
    async def test_backend_failure_handled_gracefully(self):
        """Test that backend failures don't crash the system"""
        from memory_sidecar.memory_store_sidecar import MemoryStoreSidecar

        sidecar = MemoryStoreSidecar(backend="mock")

        # Simulate backend failure
        result = await sidecar._arun({
            "content": "test",
            "should_fail": True  # Signal to mock to fail
        })

        # Should still return a handle (non-blocking)
        assert "sidecar_id" in result.response

        # Check if error was recorded
        await asyncio.sleep(0.1)

        from memory_sidecar.executor import get_sidecar_executor
        executor = get_sidecar_executor()
        handle = executor.get_status(result.response["sidecar_id"])

        # Should have error recorded
        assert handle.status in ["failed", "error"]

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test that timeouts are handled properly"""
        from memory_sidecar.memory_store_sidecar import MemoryStoreSidecar

        sidecar = MemoryStoreSidecar(backend="mock")
        sidecar.sidecar_timeout = 1  # 1 second timeout

        # Submit slow operation
        result = await sidecar._arun({
            "content": "slow operation",
            "delay_seconds": 5  # Longer than timeout
        })

        await asyncio.sleep(1.5)  # Wait for timeout

        from memory_sidecar.executor import get_sidecar_executor
        executor = get_sidecar_executor()
        handle = executor.get_status(result.response["sidecar_id"])

        assert handle.status == "timeout"

    @pytest.mark.asyncio
    async def test_retry_on_transient_failure(self):
        """Test retry mechanism for transient failures"""
        from memory_sidecar.memory_store_sidecar import MemoryStoreSidecar

        sidecar = MemoryStoreSidecar(backend="mock")

        result = await sidecar._arun({
            "content": "test",
            "transient_failures": 2  # Fail twice, then succeed
        })

        await asyncio.sleep(0.5)  # Let retries complete

        from memory_sidecar.executor import get_sidecar_executor
        executor = get_sidecar_executor()
        handle = executor.get_status(result.response["sidecar_id"])

        # Should eventually succeed after retries
        assert handle.status == "completed"


# ============================================================================
# TEST SUITE 8: Configuration (RED)
# ============================================================================

class TestConfiguration:
    """Test configuration options"""

    def test_sidecar_config_from_dict(self):
        """Test creating sidecar from config"""
        from memory_sidecar.memory_store_sidecar import MemoryStoreSidecar

        config = {
            "backend": "rag",
            "timeout": 60,
            "batch_enabled": True,
            "batch_size": 10
        }

        sidecar = MemoryStoreSidecar.from_config(config)

        assert sidecar.backend == "rag"
        assert sidecar.sidecar_timeout == 60

    def test_backend_switching(self):
        """Test switching backends at runtime"""
        from memory_sidecar.memory_store_sidecar import MemoryStoreSidecar

        sidecar = MemoryStoreSidecar(backend="mock")
        assert sidecar.backend == "mock"

        # Switch backend
        sidecar.set_backend("rag")
        assert sidecar.backend == "rag"

    def test_cache_configuration(self):
        """Test cache configuration"""
        from memory_sidecar.memory_retrieve_sidecar import MemoryRetrieveSidecar

        sidecar = MemoryRetrieveSidecar(
            backend="mock",
            cache_enabled=True,
            cache_ttl=300,
            cache_max_size=1000
        )

        assert sidecar.cache_enabled is True
        assert sidecar.cache_ttl == 300


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short", "-x"])
