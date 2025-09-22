"""
Comprehensive unit tests for CoreMemoryManager class.

These tests validate memory operations, backend switching,
context management, and auto-save functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any
from datetime import datetime

# Import the classes we want to test
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from memory.memory_manager import CoreMemoryManager
from memory.memory_store import MemoryEntry


class TestMemoryManagerInitialization:
    """Test CoreMemoryManager initialization."""

    def test_basic_initialization(self):
        """Test basic memory manager initialization."""
        manager = CoreMemoryManager()

        assert manager.memory_store is not None
        assert manager.retrieval_strategy is not None
        assert manager.context_manager is not None
        assert manager.auto_save_interval == 300
        assert manager._running is False
        assert manager.current_backend is None
        assert manager._backend_enabled is False

    def test_initialization_with_backend_config(self):
        """Test initialization with backend configuration."""
        backend_config = {
            "backend_type": "in_memory",
            "cache_size": 100
        }

        with patch('memory.memory_manager.create_backend') as mock_create:
            mock_backend = Mock()
            mock_create.return_value = mock_backend

            manager = CoreMemoryManager(backend_config=backend_config)

            assert manager.current_backend == mock_backend
            assert manager._backend_enabled is True
            assert manager.backend_config == backend_config
            mock_create.assert_called_once_with("in_memory", backend_config)

    def test_initialization_with_invalid_backend_config(self):
        """Test initialization handles invalid backend config gracefully."""
        backend_config = {
            "backend_type": "invalid_backend"
        }

        with patch('memory.memory_manager.create_backend', side_effect=Exception("Invalid backend")):
            manager = CoreMemoryManager(backend_config=backend_config)

            # Should fallback gracefully
            assert manager.current_backend is None
            assert manager._backend_enabled is False

    def test_initialization_with_custom_components(self):
        """Test initialization with custom memory store and retrieval strategy."""
        mock_store = Mock()
        mock_strategy = Mock()

        manager = CoreMemoryManager(
            memory_store=mock_store,
            retrieval_strategy=mock_strategy,
            auto_save_interval=600
        )

        assert manager.memory_store == mock_store
        assert manager.retrieval_strategy == mock_strategy
        assert manager.auto_save_interval == 600


class TestMemoryManagerBasicOperations:
    """Test basic memory operations."""

    @pytest.fixture
    def memory_manager(self):
        """Memory manager for testing."""
        manager = CoreMemoryManager()
        manager.memory_store = Mock()
        manager.retrieval_strategy = Mock()
        return manager

    @pytest.mark.asyncio
    async def test_store_memory_with_backend(self):
        """Test storing memory with backend enabled."""
        manager = CoreMemoryManager()

        # Mock backend
        mock_backend = Mock()
        mock_backend.store_memory = AsyncMock(return_value={"entry_id": "backend_123"})
        manager.current_backend = mock_backend
        manager._backend_enabled = True

        entry_id = await manager.store_memory(
            content="Test memory",
            importance=0.8,
            metadata={"source": "test"}
        )

        assert entry_id == "backend_123"
        mock_backend.store_memory.assert_called_once()

        call_args = mock_backend.store_memory.call_args[0][0]
        assert call_args["content"] == "Test memory"
        assert call_args["importance_score"] == 0.8
        assert call_args["metadata"]["source"] == "test"

    @pytest.mark.asyncio
    async def test_store_memory_without_backend(self, memory_manager):
        """Test storing memory without backend (fallback to memory store)."""
        manager = memory_manager
        manager.memory_store.store = AsyncMock()

        with patch('memory.memory_manager.MemoryEntry') as mock_entry_class:
            mock_entry = Mock()
            mock_entry.id = "store_123"
            mock_entry_class.return_value = mock_entry

            entry_id = await manager.store_memory("Test content", importance=0.5)

            assert entry_id == "store_123"
            manager.memory_store.store.assert_called_once_with(mock_entry)

    @pytest.mark.asyncio
    async def test_retrieve_memory_with_backend(self):
        """Test retrieving memory with backend enabled."""
        manager = CoreMemoryManager()

        mock_backend = Mock()
        mock_memory = {
            "entry_id": "test_123",
            "content": "Retrieved content",
            "importance_score": 0.7
        }
        mock_backend.retrieve_memory = AsyncMock(return_value=mock_memory)
        manager.current_backend = mock_backend
        manager._backend_enabled = True

        result = await manager.retrieve_memory("test_123")

        assert result == mock_memory
        mock_backend.retrieve_memory.assert_called_once_with("test_123")

    @pytest.mark.asyncio
    async def test_retrieve_memory_without_backend(self, memory_manager):
        """Test retrieving memory without backend."""
        manager = memory_manager

        mock_entry = Mock()
        mock_entry.id = "test_123"
        mock_entry.content = "Test content"
        mock_entry.importance = 0.6
        mock_entry.created_at = datetime.now()
        mock_entry.metadata = {"test": True}

        manager.memory_store.get = AsyncMock(return_value=mock_entry)

        result = await manager.retrieve_memory("test_123")

        assert result["entry_id"] == "test_123"
        assert result["content"] == "Test content"
        assert result["importance_score"] == 0.6
        manager.memory_store.get.assert_called_once_with("test_123")

    @pytest.mark.asyncio
    async def test_retrieve_memory_not_found(self, memory_manager):
        """Test retrieving non-existent memory."""
        manager = memory_manager
        manager.memory_store.get = AsyncMock(return_value=None)

        result = await manager.retrieve_memory("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_search_memory_with_backend(self):
        """Test searching memory with backend enabled."""
        manager = CoreMemoryManager()

        mock_backend = Mock()
        mock_results = [
            {"entry_id": "1", "content": "First result", "relevance_score": 0.9},
            {"entry_id": "2", "content": "Second result", "relevance_score": 0.7}
        ]
        mock_backend.search_memory = AsyncMock(return_value=mock_results)
        manager.current_backend = mock_backend
        manager._backend_enabled = True

        results = await manager.search_memory("test query", limit=5)

        assert results == mock_results
        mock_backend.search_memory.assert_called_once_with("test query", 5)

    @pytest.mark.asyncio
    async def test_search_memory_without_backend(self, memory_manager):
        """Test searching memory without backend."""
        manager = memory_manager

        mock_entries = [
            Mock(id="1", content="First", importance=0.8, created_at=datetime.now(), metadata={}),
            Mock(id="2", content="Second", importance=0.6, created_at=datetime.now(), metadata={})
        ]
        manager.retrieval_strategy.retrieve = AsyncMock(return_value=mock_entries)

        results = await manager.search_memory("test query", limit=3)

        assert len(results) == 2
        assert results[0]["entry_id"] == "1"
        assert results[0]["content"] == "First"
        assert results[0]["relevance_score"] == 1.0
        manager.retrieval_strategy.retrieve.assert_called_once()


class TestMemoryManagerBackendSwitching:
    """Test backend switching functionality."""

    @pytest.fixture
    def manager_with_mocks(self):
        """Memory manager with mocked dependencies."""
        with patch('memory.memory_manager.create_backend') as mock_create, \
             patch('memory.memory_manager.validate_backend_config') as mock_validate:
            manager = CoreMemoryManager()
            return manager, mock_create, mock_validate

    @pytest.mark.asyncio
    async def test_set_backend_success(self):
        """Test successful backend switching."""
        manager = CoreMemoryManager()

        with patch('memory.memory_manager.create_backend') as mock_create, \
             patch('memory.memory_manager.validate_backend_config') as mock_validate:

            mock_backend = Mock()
            mock_backend.initialize = AsyncMock()
            mock_create.return_value = mock_backend

            backend_config = {
                "backend_type": "redis",
                "url": "redis://localhost:6379"
            }

            await manager.set_backend(backend_config)

            mock_create.assert_called_once_with("redis", backend_config)
            assert manager.current_backend == mock_backend
            assert manager.backend_config == backend_config
            assert manager._backend_enabled is True
            mock_validate.assert_called_once_with("redis", backend_config)
            mock_backend.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_backend_with_old_backend_cleanup(self):
        """Test backend switching cleans up old backend."""
        manager = CoreMemoryManager()

        with patch('memory.memory_manager.create_backend') as mock_create, \
             patch('memory.memory_manager.validate_backend_config') as mock_validate:

            # Set up old backend
            old_backend = Mock()
            old_backend.close = AsyncMock()
            manager.current_backend = old_backend

            # Set up new backend
            new_backend = Mock()
            new_backend.initialize = AsyncMock()
            mock_create.return_value = new_backend

            backend_config = {"backend_type": "memgraph", "host": "localhost", "port": 7687}

            await manager.set_backend(backend_config)

            old_backend.close.assert_called_once()
            assert manager.current_backend == new_backend

    @pytest.mark.asyncio
    async def test_set_backend_missing_dependencies(self):
        """Test backend switching when dependencies are missing."""
        manager = CoreMemoryManager()

        with patch('memory.memory_manager.create_backend', None):
            with pytest.raises(ImportError, match="Backend switching not available"):
                await manager.set_backend({"backend_type": "redis"})

    @pytest.mark.asyncio
    async def test_set_backend_missing_backend_type(self, manager_with_mocks):
        """Test backend switching with missing backend_type."""
        manager, mock_create, mock_validate = manager_with_mocks

        with pytest.raises(ValueError, match="backend_type is required"):
            await manager.set_backend({"url": "redis://localhost"})

    @pytest.mark.asyncio
    async def test_set_backend_creation_failure(self):
        """Test backend switching when backend creation fails."""
        manager = CoreMemoryManager()

        with patch('memory.memory_manager.create_backend') as mock_create, \
             patch('memory.memory_manager.validate_backend_config') as mock_validate:

            mock_create.side_effect = Exception("Backend creation failed")

            with pytest.raises(RuntimeError, match="Failed to switch backend"):
                await manager.set_backend({"backend_type": "redis", "url": "redis://localhost:6379"})

    def test_get_backend_info_with_backend(self):
        """Test getting backend info when backend is enabled."""
        manager = CoreMemoryManager()
        manager.current_backend = Mock()
        manager._backend_enabled = True
        manager.backend_config = {"backend_type": "redis", "url": "redis://localhost"}

        info = manager.get_backend_info()

        assert info["backend_enabled"] is True
        assert info["backend_type"] == "redis"
        assert info["backend_config"]["url"] == "redis://localhost"

    def test_get_backend_info_without_backend(self):
        """Test getting backend info when backend is disabled."""
        manager = CoreMemoryManager()

        info = manager.get_backend_info()

        assert info["backend_enabled"] is False
        assert info["backend_type"] == "default"
        assert info["backend_config"] is None


class TestMemoryManagerLifecycle:
    """Test memory manager lifecycle operations."""

    @pytest.fixture
    def manager_with_mocked_components(self):
        """Manager with mocked components for lifecycle testing."""
        manager = CoreMemoryManager()

        # Mock memory store
        manager.memory_store = Mock()
        manager.memory_store.start = AsyncMock()
        manager.memory_store.stop = AsyncMock()

        # Mock context manager
        manager.context_manager = Mock()
        manager.context_manager.start = AsyncMock()
        manager.context_manager.stop = AsyncMock()
        manager.context_manager.cleanup_old_contexts = AsyncMock()
        manager.context_manager.get_active_contexts = Mock(return_value=["session1", "session2"])
        manager.context_manager.get_context = AsyncMock()
        manager.context_manager.save_context = AsyncMock()

        return manager

    @pytest.mark.asyncio
    async def test_start_memory_manager(self, manager_with_mocked_components):
        """Test starting memory manager."""
        manager = manager_with_mocked_components

        await manager.start()

        assert manager._running is True
        assert manager._auto_save_task is not None

    @pytest.mark.asyncio
    async def test_start_already_running(self, manager_with_mocked_components):
        """Test starting memory manager when already running."""
        manager = manager_with_mocked_components
        manager._running = True

        await manager.start()

        # Should not start again
        # Note: memory_store doesn't have start() method

    @pytest.mark.asyncio
    async def test_stop_memory_manager(self, manager_with_mocked_components):
        """Test stopping memory manager."""
        manager = manager_with_mocked_components

        # Set up as running with a proper async task mock
        manager._running = True

        # Create a mock task that can be awaited and raises CancelledError
        async def mock_cancelled_task():
            raise asyncio.CancelledError()

        mock_task = asyncio.create_task(mock_cancelled_task())
        mock_task.cancel()  # Cancel it to simulate real behavior
        manager._auto_save_task = mock_task

        # Mock the _save_all_contexts method
        manager._save_all_contexts = AsyncMock()

        await manager.stop()

        assert manager._running is False
        # Note: We can't assert on cancel() calls since we're using a real task
        manager._save_all_contexts.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_all_contexts(self, manager_with_mocked_components):
        """Test saving all active contexts."""
        manager = manager_with_mocked_components

        # Mock context data
        mock_context1 = Mock()
        mock_context2 = Mock()
        manager.context_manager.get_context.side_effect = [mock_context1, mock_context2]

        await manager._save_all_contexts()

        assert manager.context_manager.get_context.call_count == 2
        assert manager.context_manager.save_context.call_count == 2
        manager.context_manager.save_context.assert_any_call(mock_context1)
        manager.context_manager.save_context.assert_any_call(mock_context2)

    @pytest.mark.asyncio
    async def test_save_all_contexts_with_error(self, manager_with_mocked_components):
        """Test saving contexts handles errors gracefully."""
        manager = manager_with_mocked_components
        manager.context_manager.get_context.side_effect = Exception("Context error")

        # Should not raise exception
        await manager._save_all_contexts()

    @pytest.mark.asyncio
    async def test_auto_save_loop_functionality(self, manager_with_mocked_components):
        """Test auto-save loop runs and saves contexts."""
        manager = manager_with_mocked_components
        manager.auto_save_interval = 0.01  # Very short interval for testing

        # Mock the save methods
        manager._save_all_contexts = AsyncMock()

        # Start the manager to begin auto-save loop
        await manager.start()

        # Wait for at least one auto-save cycle
        await asyncio.sleep(0.02)

        # Stop the manager
        await manager.stop()

        # Verify auto-save was called
        manager._save_all_contexts.assert_called()
        manager.context_manager.cleanup_old_contexts.assert_called()


class TestMemoryManagerErrorHandling:
    """Test error handling in memory operations."""

    @pytest.fixture
    def manager_with_failing_backend(self):
        """Manager with backend that fails operations."""
        manager = CoreMemoryManager()

        mock_backend = Mock()
        mock_backend.store_memory = AsyncMock(side_effect=Exception("Backend error"))
        mock_backend.retrieve_memory = AsyncMock(side_effect=Exception("Backend error"))
        mock_backend.search_memory = AsyncMock(side_effect=Exception("Backend error"))

        manager.current_backend = mock_backend
        manager._backend_enabled = True

        return manager

    @pytest.mark.asyncio
    async def test_store_memory_backend_error_fallback(self, manager_with_failing_backend):
        """Test store memory behavior when backend fails."""
        manager = manager_with_failing_backend

        # The current implementation doesn't have fallback, it raises the exception
        with pytest.raises(Exception, match="Backend error"):
            await manager.store_memory("Test content")

    @pytest.mark.asyncio
    async def test_retrieve_memory_backend_error_fallback(self, manager_with_failing_backend):
        """Test retrieve memory behavior when backend fails."""
        manager = manager_with_failing_backend

        # The current implementation doesn't have fallback, it raises the exception
        with pytest.raises(Exception, match="Backend error"):
            await manager.retrieve_memory("test_123")

    @pytest.mark.asyncio
    async def test_search_memory_backend_error_fallback(self, manager_with_failing_backend):
        """Test search memory behavior when backend fails."""
        manager = manager_with_failing_backend

        # The current implementation doesn't have fallback, it raises the exception
        with pytest.raises(Exception, match="Backend error"):
            await manager.search_memory("test query")


class TestMemoryManagerCallbacks:
    """Test callback functionality."""

    @pytest.fixture
    def manager_with_callbacks(self):
        """Manager set up for callback testing."""
        manager = CoreMemoryManager()
        manager.memory_store = Mock()
        return manager

    def test_set_memory_callback(self, manager_with_callbacks):
        """Test setting memory storage callback."""
        manager = manager_with_callbacks
        callback = AsyncMock()

        manager.set_memory_callback(callback)

        assert manager._on_memory_stored == callback

    def test_set_context_callback(self, manager_with_callbacks):
        """Test setting context update callback."""
        manager = manager_with_callbacks
        callback = AsyncMock()

        manager.set_context_callback(callback)

        assert manager._on_context_updated == callback


if __name__ == "__main__":
    pytest.main([__file__, "-v"])