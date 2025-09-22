"""
Comprehensive unit tests for RedisBackend class.

These tests validate Redis-specific memory operations including
TTL management, search indexing, and Redis-specific features.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any
from datetime import datetime
import json

# Import the classes we want to test
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from memory.backends.redis_backend import RedisBackend


@pytest.fixture
def initialized_backend():
    """Redis backend with mocked client - module-level fixture."""
    backend = RedisBackend({"url": "redis://localhost:6379"})
    backend.redis_client = AsyncMock()
    backend._initialized = True
    return backend


class TestRedisBackendInitialization:
    """Test RedisBackend initialization."""

    @pytest.fixture
    def valid_config(self):
        """Valid Redis configuration."""
        return {
            "url": "redis://localhost:6379",
            "db": 0,
            "password": "test-password",
            "default_ttl": 7200
        }

    def test_initialization_with_config(self, valid_config):
        """Test Redis backend initialization with configuration."""
        backend = RedisBackend(valid_config)

        assert backend.config == valid_config
        assert backend.url == "redis://localhost:6379"
        assert backend.db == 0
        assert backend.password == "test-password"
        assert backend.default_ttl == 7200
        assert backend._initialized is False

    def test_initialization_with_defaults(self):
        """Test Redis backend initialization with default values."""
        config = {"url": "redis://localhost:6379"}
        backend = RedisBackend(config)

        assert backend.db == 0
        assert backend.password is None
        assert backend.default_ttl == 3600

    def test_initialization_without_redis_package(self):
        """Test initialization fails gracefully without redis package."""
        with patch('memory.backends.redis_backend.redis', None):
            with pytest.raises(ImportError, match="redis package not installed"):
                RedisBackend({"url": "redis://localhost:6379"})


class TestRedisBackendConnection:
    """Test Redis connection management."""

    @pytest.fixture
    def backend_with_config(self):
        """Redis backend with test configuration."""
        config = {
            "url": "redis://localhost:6379",
            "db": 1,
            "password": "test-pass"
        }
        return RedisBackend(config)

    @pytest.mark.asyncio
    async def test_initialize_connection_success(self, backend_with_config):
        """Test successful connection initialization."""
        backend = backend_with_config

        with patch('memory.backends.redis_backend.redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.from_url.return_value = mock_client
            mock_client.ping.return_value = True

            await backend.initialize()

            assert backend._initialized is True
            assert backend.redis_client == mock_client
            mock_redis.from_url.assert_called_once_with(
                "redis://localhost:6379",
                db=1,
                password="test-pass",
                decode_responses=True
            )
            mock_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_connection_failure(self, backend_with_config):
        """Test connection initialization failure."""
        backend = backend_with_config

        with patch('memory.backends.redis_backend.redis') as mock_redis:
            mock_redis.from_url.side_effect = Exception("Connection failed")

            with pytest.raises(ConnectionError, match="Failed to connect to Redis"):
                await backend.initialize()

            assert backend._initialized is False

    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self, backend_with_config):
        """Test initialization when already initialized."""
        backend = backend_with_config
        backend._initialized = True

        await backend.initialize()

        # Should return early without attempting connection

    @pytest.mark.asyncio
    async def test_close_connection(self, backend_with_config):
        """Test closing Redis connection."""
        backend = backend_with_config
        mock_client = AsyncMock()
        backend.redis_client = mock_client
        backend._initialized = True

        await backend.close()

        mock_client.close.assert_called_once()
        assert backend._initialized is False


class TestRedisBackendMemoryOperations:
    """Test basic memory operations."""


    @pytest.mark.asyncio
    async def test_store_memory_success(self, initialized_backend):
        """Test successful memory storage."""
        backend = initialized_backend

        memory_entry = {
            "entry_id": "test_123",
            "content": "Test memory content",
            "entry_type": "conversation",
            "importance_score": 0.8,
            "created_at": "2023-01-01T10:00:00Z",
            "metadata": {"source": "test"}
        }

        # Mock Redis operations
        backend.redis_client.setex = AsyncMock()
        backend._add_to_search_index = AsyncMock()

        result = await backend.store_memory(memory_entry)

        assert result["entry_id"] == "test_123"
        assert result["status"] == "stored"
        assert result["backend"] == "redis"
        assert "ttl" in result

        # Verify Redis call
        backend.redis_client.setex.assert_called_once()
        call_args = backend.redis_client.setex.call_args[0]
        assert call_args[0] == "memory:test_123"
        assert call_args[1] > 0  # TTL should be positive

        # Verify search index update
        backend._add_to_search_index.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_memory_with_importance_based_ttl(self, initialized_backend):
        """Test memory storage with TTL based on importance."""
        backend = initialized_backend
        backend.default_ttl = 1000

        memory_entry = {
            "entry_id": "test_123",
            "content": "High importance memory",
            "importance_score": 1.0
        }

        backend.redis_client.setex = AsyncMock()
        backend._add_to_search_index = AsyncMock()

        result = await backend.store_memory(memory_entry)

        # High importance should get longer TTL
        assert result["ttl"] == int(1000 * (0.5 + 1.0))  # 1500

        call_args = backend.redis_client.setex.call_args[0]
        assert call_args[1] == 1500

    @pytest.mark.asyncio
    async def test_store_memory_failure(self, initialized_backend):
        """Test memory storage failure."""
        backend = initialized_backend

        memory_entry = {"entry_id": "test_123", "content": "Test"}
        backend.redis_client.setex = AsyncMock(side_effect=Exception("Redis error"))

        with pytest.raises(RuntimeError, match="Failed to store memory in Redis"):
            await backend.store_memory(memory_entry)

    @pytest.mark.asyncio
    async def test_retrieve_memory_success(self, initialized_backend):
        """Test successful memory retrieval."""
        backend = initialized_backend

        stored_data = {
            "entry_id": "test_123",
            "content": "Retrieved content",
            "importance_score": 0.7
        }

        backend.redis_client.get = AsyncMock(return_value=json.dumps(stored_data))

        result = await backend.retrieve_memory("test_123")

        assert result == stored_data
        backend.redis_client.get.assert_called_once_with("memory:test_123")

    @pytest.mark.asyncio
    async def test_retrieve_memory_not_found(self, initialized_backend):
        """Test retrieving non-existent memory."""
        backend = initialized_backend
        backend.redis_client.get = AsyncMock(return_value=None)

        result = await backend.retrieve_memory("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_retrieve_memory_failure(self, initialized_backend):
        """Test memory retrieval failure."""
        backend = initialized_backend
        backend.redis_client.get = AsyncMock(side_effect=Exception("Redis error"))

        with pytest.raises(RuntimeError, match="Failed to retrieve memory from Redis"):
            await backend.retrieve_memory("test_123")

    @pytest.mark.asyncio
    async def test_delete_memory_success(self, initialized_backend):
        """Test successful memory deletion."""
        backend = initialized_backend

        backend.redis_client.delete = AsyncMock(return_value=1)
        backend._remove_from_search_index = AsyncMock()

        result = await backend.delete_memory("test_123")

        assert result is True
        backend.redis_client.delete.assert_called_once_with("memory:test_123")
        backend._remove_from_search_index.assert_called_once_with("test_123")

    @pytest.mark.asyncio
    async def test_delete_memory_not_found(self, initialized_backend):
        """Test deleting non-existent memory."""
        backend = initialized_backend
        backend.redis_client.delete = AsyncMock(return_value=0)
        backend._remove_from_search_index = AsyncMock()

        result = await backend.delete_memory("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_clear_all_memories(self, initialized_backend):
        """Test clearing all memories."""
        backend = initialized_backend

        backend.redis_client.keys = AsyncMock(return_value=["memory:1", "memory:2"])
        backend.redis_client.delete = AsyncMock()

        await backend.clear_all()

        backend.redis_client.keys.assert_called_once_with("memory:*")
        # Check that delete was called for memory keys - may be called multiple times for search indexes too
        assert backend.redis_client.delete.call_count >= 1
        # Verify memory keys were deleted
        delete_calls = backend.redis_client.delete.call_args_list
        memory_delete_call = delete_calls[0]
        assert memory_delete_call[0] == ("memory:1", "memory:2")


class TestRedisBackendSearch:
    """Test search functionality."""

    @pytest.fixture
    def backend_with_search_data(self):
        """Backend with mocked search data."""
        backend = RedisBackend({"url": "redis://localhost:6379"})
        backend.redis_client = AsyncMock()
        backend._initialized = True

        # Mock memory data
        memories = [
            {
                "entry_id": "mem1",
                "content": "Python programming language",
                "importance_score": 0.8
            },
            {
                "entry_id": "mem2",
                "content": "JavaScript programming tutorial",
                "importance_score": 0.6
            },
            {
                "entry_id": "mem3",
                "content": "Database design principles",
                "importance_score": 0.9
            }
        ]

        backend.redis_client.keys = AsyncMock(return_value=["memory:mem1", "memory:mem2", "memory:mem3"])
        backend.redis_client.get = AsyncMock(side_effect=[json.dumps(mem) for mem in memories])

        return backend

    @pytest.mark.asyncio
    async def test_search_memory_with_matches(self, backend_with_search_data):
        """Test searching memories with matching results."""
        backend = backend_with_search_data

        results = await backend.search_memory("programming", limit=5)

        assert len(results) == 2  # Should match first two memories
        assert all("programming" in result["content"] for result in results)
        assert all("relevance_score" in result for result in results)

        # Results should be sorted by relevance
        assert results[0]["relevance_score"] >= results[1]["relevance_score"]

    @pytest.mark.asyncio
    async def test_search_memory_no_matches(self, backend_with_search_data):
        """Test searching with no matching results."""
        backend = backend_with_search_data

        results = await backend.search_memory("nonexistent", limit=5)

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_memory_with_limit(self, backend_with_search_data):
        """Test search respects limit parameter."""
        backend = backend_with_search_data

        results = await backend.search_memory("programming", limit=1)

        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_memory_empty_database(self, initialized_backend):
        """Test search with empty database."""
        backend = initialized_backend
        backend.redis_client.keys = AsyncMock(return_value=[])

        results = await backend.search_memory("any query")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_memory_failure(self, initialized_backend):
        """Test search failure handling."""
        backend = initialized_backend
        backend.redis_client.keys = AsyncMock(side_effect=Exception("Redis error"))

        with pytest.raises(RuntimeError, match="Failed to search memories in Redis"):
            await backend.search_memory("test query")


class TestRedisBackendTTLManagement:
    """Test TTL (Time To Live) management functionality."""

    @pytest.fixture
    def backend_for_ttl(self):
        """Backend set up for TTL testing."""
        backend = RedisBackend({"url": "redis://localhost:6379"})
        backend.redis_client = AsyncMock()
        backend._initialized = True
        return backend

    @pytest.mark.asyncio
    async def test_set_ttl_success(self, backend_for_ttl):
        """Test setting TTL for memory entry."""
        backend = backend_for_ttl
        backend.redis_client.expire = AsyncMock(return_value=True)

        result = await backend.set_ttl("test_123", 7200)

        assert result is True
        backend.redis_client.expire.assert_called_once_with("memory:test_123", 7200)

    @pytest.mark.asyncio
    async def test_set_ttl_failure(self, backend_for_ttl):
        """Test TTL setting failure."""
        backend = backend_for_ttl
        backend.redis_client.expire = AsyncMock(side_effect=Exception("Redis error"))

        with pytest.raises(RuntimeError, match="Failed to set TTL for memory"):
            await backend.set_ttl("test_123", 7200)

    @pytest.mark.asyncio
    async def test_get_ttl_existing_key(self, backend_for_ttl):
        """Test getting TTL for existing key."""
        backend = backend_for_ttl
        backend.redis_client.ttl = AsyncMock(return_value=3600)

        result = await backend.get_ttl("test_123")

        assert result == 3600
        backend.redis_client.ttl.assert_called_once_with("memory:test_123")

    @pytest.mark.asyncio
    async def test_get_ttl_nonexistent_key(self, backend_for_ttl):
        """Test getting TTL for non-existent key."""
        backend = backend_for_ttl
        backend.redis_client.ttl = AsyncMock(return_value=-2)  # Key doesn't exist

        result = await backend.get_ttl("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_ttl_no_expiration(self, backend_for_ttl):
        """Test getting TTL for key with no expiration."""
        backend = backend_for_ttl
        backend.redis_client.ttl = AsyncMock(return_value=-1)  # No expiration

        result = await backend.get_ttl("test_123")

        assert result == -1

    @pytest.mark.asyncio
    async def test_extend_ttl_success(self, backend_for_ttl):
        """Test extending TTL for memory entry."""
        backend = backend_for_ttl

        # Mock current TTL
        backend.get_ttl = AsyncMock(return_value=1800)
        backend.set_ttl = AsyncMock(return_value=True)

        result = await backend.extend_ttl("test_123", 3600)

        assert result is True
        backend.set_ttl.assert_called_once_with("test_123", 5400)  # 1800 + 3600

    @pytest.mark.asyncio
    async def test_extend_ttl_nonexistent_key(self, backend_for_ttl):
        """Test extending TTL for non-existent key."""
        backend = backend_for_ttl
        backend.get_ttl = AsyncMock(return_value=None)

        result = await backend.extend_ttl("nonexistent", 3600)

        assert result is False

    @pytest.mark.asyncio
    async def test_extend_ttl_zero_current_ttl(self, backend_for_ttl):
        """Test extending TTL when current TTL is zero or negative."""
        backend = backend_for_ttl

        backend.get_ttl = AsyncMock(return_value=-10)
        backend.set_ttl = AsyncMock(return_value=True)

        result = await backend.extend_ttl("test_123", 3600)

        assert result is True
        backend.set_ttl.assert_called_once_with("test_123", 3600)  # max(0, -10) + 3600


class TestRedisBackendStatistics:
    """Test statistics and monitoring functionality."""

    @pytest.fixture
    def backend_with_stats_data(self):
        """Backend with mocked statistics data."""
        backend = RedisBackend({"url": "redis://localhost:6379"})
        backend.redis_client = AsyncMock()
        backend._initialized = True

        # Mock memory data for statistics
        memory_keys = ["memory:1", "memory:2", "memory:3"]
        memories = [
            {
                "entry_id": "1",
                "content": "First memory",
                "entry_type": "conversation",
                "importance_score": 0.8
            },
            {
                "entry_id": "2",
                "content": "Second memory",
                "entry_type": "fact",
                "importance_score": 0.6
            },
            {
                "entry_id": "3",
                "content": "Third memory",
                "entry_type": "conversation",
                "importance_score": 0.9
            }
        ]

        backend.redis_client.keys = AsyncMock(return_value=memory_keys)
        backend.redis_client.get = AsyncMock(side_effect=[json.dumps(mem) for mem in memories])

        return backend

    @pytest.mark.asyncio
    async def test_get_memory_stats(self, backend_with_stats_data):
        """Test getting memory statistics."""
        backend = backend_with_stats_data

        stats = await backend.get_memory_stats()

        assert stats["total_memories"] == 3
        assert stats["backend"] == "redis"
        assert "average_size_bytes" in stats
        assert "average_importance" in stats
        assert "type_distribution" in stats

        # Check type distribution
        assert stats["type_distribution"]["conversation"] == 2
        assert stats["type_distribution"]["fact"] == 1

        # Check average importance
        expected_avg_importance = (0.8 + 0.6 + 0.9) / 3
        assert abs(stats["average_importance"] - expected_avg_importance) < 0.01

    @pytest.mark.asyncio
    async def test_get_memory_stats_empty_database(self, initialized_backend):
        """Test statistics with empty database."""
        backend = initialized_backend
        backend.redis_client.keys = AsyncMock(return_value=[])

        stats = await backend.get_memory_stats()

        assert stats["total_memories"] == 0
        assert stats["average_size_bytes"] == 0
        assert stats["average_importance"] == 0
        assert stats["type_distribution"] == {}

    @pytest.mark.asyncio
    async def test_get_memory_stats_with_corrupted_data(self, initialized_backend):
        """Test statistics with some corrupted data."""
        backend = initialized_backend

        backend.redis_client.keys = AsyncMock(return_value=["memory:1", "memory:2"])
        backend.redis_client.get = AsyncMock(side_effect=[
            json.dumps({"entry_id": "1", "content": "Valid", "importance_score": 0.5}),
            "invalid json"  # Corrupted data
        ])

        stats = await backend.get_memory_stats()

        # Should handle corrupted data gracefully
        assert stats["total_memories"] == 2
        assert stats["backend"] == "redis"


class TestRedisBackendSearchIndexing:
    """Test search indexing functionality."""

    @pytest.fixture
    def backend_for_indexing(self):
        """Backend set up for indexing tests."""
        backend = RedisBackend({"url": "redis://localhost:6379"})
        backend.redis_client = AsyncMock()
        backend._initialized = True
        return backend

    @pytest.mark.asyncio
    async def test_add_to_search_index(self, backend_for_indexing):
        """Test adding entry to search index."""
        backend = backend_for_indexing

        backend.redis_client.sadd = AsyncMock()
        backend.redis_client.expire = AsyncMock()

        await backend._add_to_search_index("entry_123", "python programming tutorial", "educational")

        # Should create index entries for significant words
        assert backend.redis_client.sadd.call_count > 0
        assert backend.redis_client.expire.call_count > 0

        # Check that short words are skipped
        calls = [call[0][0] for call in backend.redis_client.sadd.call_args_list]
        index_keys = [key for key in calls if key.startswith("search_index:")]

        # Should not index very short words
        assert "search_index:a" not in index_keys
        assert "search_index:an" not in index_keys

    @pytest.mark.asyncio
    async def test_add_to_search_index_long_content(self, backend_for_indexing):
        """Test indexing limits to first 50 words."""
        backend = backend_for_indexing

        # Create content with more than 50 words
        content = " ".join([f"word{i}" for i in range(100)])

        backend.redis_client.sadd = AsyncMock()
        backend.redis_client.expire = AsyncMock()

        await backend._add_to_search_index("entry_123", content, "test")

        # Should limit to first 50 words
        assert backend.redis_client.sadd.call_count <= 50

    @pytest.mark.asyncio
    async def test_remove_from_search_index(self, backend_for_indexing):
        """Test removing entry from search index."""
        backend = backend_for_indexing

        # Mock existing index keys
        backend.redis_client.keys = AsyncMock(return_value=[
            "search_index:python",
            "search_index:programming",
            "search_index:tutorial"
        ])
        backend.redis_client.srem = AsyncMock()

        await backend._remove_from_search_index("entry_123")

        # Should remove from all index sets
        assert backend.redis_client.srem.call_count == 3
        for call in backend.redis_client.srem.call_args_list:
            assert call[0][1] == "entry_123"  # Entry ID should be removed from each set

    @pytest.mark.asyncio
    async def test_search_index_operations_with_errors(self, backend_for_indexing):
        """Test that index operations don't fail main operations."""
        backend = backend_for_indexing

        # Make indexing operations fail
        backend.redis_client.sadd = AsyncMock(side_effect=Exception("Index error"))
        backend.redis_client.srem = AsyncMock(side_effect=Exception("Index error"))

        # Should not raise exceptions (non-critical operations)
        await backend._add_to_search_index("entry_123", "test content", "test")
        await backend._remove_from_search_index("entry_123")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])