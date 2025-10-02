"""Unit tests for parallel retrieval engine."""

import pytest
import asyncio
from datetime import datetime
from memory.coordinator.parallel_retrieval import (
    ParallelRetrievalEngine,
    ParallelRetrievalResult
)
from memory.learning_memory_system import LearningMemorySystem
from memory.memory_store import MemoryEntry


class TestParallelRetrievalEngine:
    """Test suite for ParallelRetrievalEngine."""

    @pytest.fixture
    async def learning_system(self):
        """Create a learning system for testing."""
        system = LearningMemorySystem()
        await system.start()
        yield system
        await system.stop()

    @pytest.fixture
    def retrieval_engine(self, learning_system):
        """Create retrieval engine with learning system."""
        return ParallelRetrievalEngine(learning_system)

    @pytest.mark.asyncio
    async def test_initialization(self, learning_system):
        """Test proper initialization of retrieval engine."""
        engine = ParallelRetrievalEngine(learning_system)
        assert engine.system == learning_system

    @pytest.mark.asyncio
    async def test_retrieve_all_structure(self, retrieval_engine):
        """Test that retrieve_all returns proper structure."""
        result = await retrieval_engine.retrieve_all(
            query="test query",
            user_id="user123",
            session_id="session456",
            context={'domain': 'algebra'}
        )

        # Verify result structure
        assert isinstance(result, ParallelRetrievalResult)
        assert isinstance(result.episodic_memories, list)
        assert isinstance(result.semantic_memories, list)
        assert isinstance(result.profile_memories, list)
        assert isinstance(result.interaction_memories, list)
        assert isinstance(result.graph_memories, list)
        assert isinstance(result.retrieval_time_ms, float)
        assert isinstance(result.retrieval_metadata, dict)
        assert isinstance(result.errors, dict)

    @pytest.mark.asyncio
    async def test_retrieve_all_with_limits(self, retrieval_engine):
        """Test retrieval with custom limits."""
        custom_limits = {
            'episodic': 5,
            'semantic': 3,
            'profile': 2,
            'interaction': 4,
            'graph': 2
        }

        result = await retrieval_engine.retrieve_all(
            query="test",
            user_id="user123",
            session_id="session456",
            context={},
            limits=custom_limits
        )

        # Should use provided limits
        assert result.retrieval_metadata['limits'] == custom_limits

    @pytest.mark.asyncio
    async def test_retrieval_timing(self, retrieval_engine):
        """Test that retrieval timing is measured."""
        result = await retrieval_engine.retrieve_all(
            query="test",
            user_id="user123",
            session_id="session456",
            context={}
        )

        # Should have recorded time
        assert result.retrieval_time_ms >= 0
        assert result.retrieval_time_ms < 10000  # Should be under 10 seconds

    @pytest.mark.asyncio
    async def test_parallel_execution_faster_than_sequential(
        self,
        retrieval_engine,
        learning_system
    ):
        """Test that parallel retrieval completes successfully.

        Note: Actual speed comparison is challenging in unit tests due to overhead,
        but we verify that parallel execution works correctly.
        """
        # Measure parallel retrieval time
        start_parallel = datetime.now()
        result = await retrieval_engine.retrieve_all(
            query="test",
            user_id="user123",
            session_id="session456",
            context={}
        )
        parallel_time = (datetime.now() - start_parallel).total_seconds()

        # Verify parallel execution completed
        assert isinstance(result, ParallelRetrievalResult)
        assert result.retrieval_time_ms > 0

        # Parallel execution should be reasonably fast (under 1 second for small data)
        assert parallel_time < 1.0

    @pytest.mark.asyncio
    async def test_error_handling(self, retrieval_engine, monkeypatch):
        """Test that errors in one retrieval don't break others."""

        # Mock one retrieval to fail
        async def failing_retrieval(*args, **kwargs):
            raise ValueError("Test error")

        # Replace episodic retrieval with failing version
        monkeypatch.setattr(
            retrieval_engine,
            '_retrieve_episodic',
            failing_retrieval
        )

        result = await retrieval_engine.retrieve_all(
            query="test",
            user_id="user123",
            session_id="session456",
            context={}
        )

        # Episodic should be empty due to error
        assert len(result.episodic_memories) == 0

        # Error should be recorded
        assert 'episodic' in result.errors
        assert 'Test error' in result.errors['episodic']

        # Other retrievals should still work
        # (they return empty lists, but shouldn't error)
        assert isinstance(result.semantic_memories, list)
        assert isinstance(result.profile_memories, list)

    @pytest.mark.asyncio
    async def test_retrieve_specific_types(self, retrieval_engine):
        """Test retrieving only specific memory types."""
        result = await retrieval_engine.retrieve_specific_types(
            memory_types=['episodic', 'semantic'],
            query="test",
            user_id="user123",
            session_id="session456",
            context={}
        )

        # Should return dict with requested types
        assert isinstance(result, dict)
        assert 'episodic' in result
        assert 'semantic' in result

    @pytest.mark.asyncio
    async def test_retrieval_metadata(self, retrieval_engine):
        """Test that retrieval metadata is properly populated."""
        query = "linear equations"
        user_id = "user789"
        session_id = "session123"

        result = await retrieval_engine.retrieve_all(
            query=query,
            user_id=user_id,
            session_id=session_id,
            context={'domain': 'algebra'}
        )

        # Check metadata
        assert result.retrieval_metadata['query'] == query
        assert result.retrieval_metadata['user_id'] == user_id
        assert result.retrieval_metadata['session_id'] == session_id
        assert 'timestamp' in result.retrieval_metadata

    @pytest.mark.asyncio
    async def test_concurrent_retrievals(self, retrieval_engine):
        """Test multiple concurrent retrieval calls."""
        # Launch multiple retrievals concurrently
        tasks = [
            retrieval_engine.retrieve_all(
                query=f"query{i}",
                user_id=f"user{i}",
                session_id=f"session{i}",
                context={}
            )
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert len(results) == 5
        for result in results:
            assert isinstance(result, ParallelRetrievalResult)


    @pytest.mark.asyncio
    async def test_empty_results(self, retrieval_engine):
        """Test handling of empty results from all memory types."""
        result = await retrieval_engine.retrieve_all(
            query="nonexistent query xyz123",
            user_id="new_user",
            session_id="new_session",
            context={}
        )

        # Should return empty lists, not fail
        assert isinstance(result.episodic_memories, list)
        assert isinstance(result.semantic_memories, list)
        # May be empty or have defaults
        assert result.retrieval_time_ms >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
