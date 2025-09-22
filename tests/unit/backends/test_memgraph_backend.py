"""Unit tests for Memgraph backend implementation."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List, Optional
import pytest
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from memory.backends.memgraph_backend import MemgraphBackend
    from memory.memory_types import Memory, MemoryImportance
except ImportError as e:
    pytest.skip(f"Backend imports not available: {e}", allow_module_level=True)


class TestMemgraphBackend:
    """Test the MemgraphBackend class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "host": "localhost",
            "port": 7687,
            "username": "memgraph",
            "password": "test"
        }

    @patch('memory.backends.memgraph_backend.mgclient')
    def test_init_success(self, mock_mgclient):
        """Test successful backend initialization."""
        mock_connection = Mock()
        mock_mgclient.connect.return_value = mock_connection

        backend = MemgraphBackend(self.config)

        assert backend.config == self.config
        assert backend.connection == mock_connection
        assert backend.is_connected is True
        mock_mgclient.connect.assert_called_once_with(
            host="localhost",
            port=7687,
            username="memgraph",
            password="test"
        )

    @patch('memory.backends.memgraph_backend.mgclient')
    def test_init_connection_failure(self, mock_mgclient):
        """Test initialization with connection failure."""
        mock_mgclient.connect.side_effect = Exception("Connection failed")

        backend = MemgraphBackend(self.config)

        assert backend.connection is None
        assert backend.is_connected is False

    @patch('memory.backends.memgraph_backend.mgclient')
    @pytest.mark.asyncio
    async def test_store_memory_success(self, mock_mgclient):
        """Test successful memory storage."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_connection

        backend = MemgraphBackend(self.config)

        memory = Memory(
            id="test-id",
            content="Test memory content",
            importance=MemoryImportance.MEDIUM,
            metadata={"type": "test", "score": 0.8}
        )

        success = await backend.store_memory(memory)

        assert success is True
        mock_cursor.execute.assert_called()

        # Verify the query structure
        execute_calls = mock_cursor.execute.call_args_list
        assert len(execute_calls) >= 1

        # Check that memory properties were included
        query, params = execute_calls[0][0], execute_calls[0][1] if len(execute_calls[0]) > 1 else {}
        assert "CREATE" in query or "MERGE" in query
        assert "memory" in query.lower()

    @patch('memory.backends.memgraph_backend.mgclient')
    @pytest.mark.asyncio
    async def test_store_memory_connection_error(self, mock_mgclient):
        """Test memory storage with connection error."""
        backend = MemgraphBackend(self.config)
        backend.connection = None
        backend.is_connected = False

        memory = Memory(
            id="test-id",
            content="Test content",
            importance=MemoryImportance.HIGH
        )

        success = await backend.store_memory(memory)

        assert success is False

    @patch('memory.backends.memgraph_backend.mgclient')
    @pytest.mark.asyncio
    async def test_store_memory_execution_error(self, mock_mgclient):
        """Test memory storage with execution error."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("Query failed")
        mock_connection.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_connection

        backend = MemgraphBackend(self.config)

        memory = Memory(
            id="test-id",
            content="Test content",
            importance=MemoryImportance.LOW
        )

        success = await backend.store_memory(memory)

        assert success is False

    @patch('memory.backends.memgraph_backend.mgclient')
    @pytest.mark.asyncio
    async def test_retrieve_memory_success(self, mock_mgclient):
        """Test successful memory retrieval."""
        mock_connection = Mock()
        mock_cursor = Mock()

        # Mock query result
        mock_record = Mock()
        mock_record.values.return_value = [
            "test-id",
            "Retrieved content",
            "MEDIUM",
            '{"type": "test"}',
            datetime.now().isoformat()
        ]
        mock_cursor.fetchall.return_value = [mock_record]

        mock_connection.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_connection

        backend = MemgraphBackend(self.config)

        memory = await backend.retrieve_memory("test-id")

        assert memory is not None
        assert memory.id == "test-id"
        assert memory.content == "Retrieved content"
        assert memory.importance == MemoryImportance.MEDIUM

    @patch('memory.backends.memgraph_backend.mgclient')
    @pytest.mark.asyncio
    async def test_retrieve_memory_not_found(self, mock_mgclient):
        """Test memory retrieval when memory not found."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_connection

        backend = MemgraphBackend(self.config)

        memory = await backend.retrieve_memory("nonexistent-id")

        assert memory is None

    @patch('memory.backends.memgraph_backend.mgclient')
    @pytest.mark.asyncio
    async def test_search_memories_success(self, mock_mgclient):
        """Test successful memory search."""
        mock_connection = Mock()
        mock_cursor = Mock()

        # Mock search results
        mock_records = []
        for i in range(3):
            mock_record = Mock()
            mock_record.values.return_value = [
                f"memory-{i}",
                f"Search result {i}",
                "HIGH",
                '{"relevance": 0.9}',
                datetime.now().isoformat()
            ]
            mock_records.append(mock_record)

        mock_cursor.fetchall.return_value = mock_records
        mock_connection.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_connection

        backend = MemgraphBackend(self.config)

        memories = await backend.search_memories("test query", limit=3)

        assert len(memories) == 3
        assert all(isinstance(m, Memory) for m in memories)
        assert memories[0].content == "Search result 0"

    @patch('memory.backends.memgraph_backend.mgclient')
    @pytest.mark.asyncio
    async def test_search_memories_with_filters(self, mock_mgclient):
        """Test memory search with filters."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_connection

        backend = MemgraphBackend(self.config)

        filters = {
            "importance": "HIGH",
            "type": "conversation"
        }

        memories = await backend.search_memories(
            "test query",
            limit=5,
            filters=filters
        )

        # Verify query was executed with filters
        mock_cursor.execute.assert_called()
        query_call = mock_cursor.execute.call_args[0][0]

        # Should include filter conditions
        assert "WHERE" in query_call or "where" in query_call

    @patch('memory.backends.memgraph_backend.mgclient')
    @pytest.mark.asyncio
    async def test_delete_memory_success(self, mock_mgclient):
        """Test successful memory deletion."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_connection

        backend = MemgraphBackend(self.config)

        success = await backend.delete_memory("test-id")

        assert success is True
        mock_cursor.execute.assert_called()

        # Verify deletion query
        query = mock_cursor.execute.call_args[0][0]
        assert "DELETE" in query or "DETACH DELETE" in query

    @patch('memory.backends.memgraph_backend.mgclient')
    @pytest.mark.asyncio
    async def test_update_memory_success(self, mock_mgclient):
        """Test successful memory update."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_connection

        backend = MemgraphBackend(self.config)

        updates = {
            "content": "Updated content",
            "importance": "HIGH"
        }

        success = await backend.update_memory("test-id", updates)

        assert success is True
        mock_cursor.execute.assert_called()

        # Verify update query
        query = mock_cursor.execute.call_args[0][0]
        assert "SET" in query

    @patch('memory.backends.memgraph_backend.mgclient')
    @pytest.mark.asyncio
    async def test_create_relationship_success(self, mock_mgclient):
        """Test successful relationship creation."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_connection

        backend = MemgraphBackend(self.config)

        success = await backend.create_relationship(
            memory_id_1="memory-1",
            memory_id_2="memory-2",
            relationship_type="RELATES_TO",
            properties={"strength": 0.8, "context": "conversation"}
        )

        assert success is True
        mock_cursor.execute.assert_called()

        # Verify relationship query
        query = mock_cursor.execute.call_args[0][0]
        assert "MATCH" in query
        assert "CREATE" in query or "MERGE" in query
        assert "RELATES_TO" in query

    @patch('memory.backends.memgraph_backend.mgclient')
    @pytest.mark.asyncio
    async def test_get_related_memories_success(self, mock_mgclient):
        """Test successful retrieval of related memories."""
        mock_connection = Mock()
        mock_cursor = Mock()

        # Mock related memories
        mock_records = []
        for i in range(2):
            mock_record = Mock()
            mock_record.values.return_value = [
                f"related-{i}",
                f"Related content {i}",
                "MEDIUM",
                '{"relation": "connected"}',
                datetime.now().isoformat()
            ]
            mock_records.append(mock_record)

        mock_cursor.fetchall.return_value = mock_records
        mock_connection.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_connection

        backend = MemgraphBackend(self.config)

        related = await backend.get_related_memories("base-memory")

        assert len(related) == 2
        assert related[0].content == "Related content 0"

    @patch('memory.backends.memgraph_backend.mgclient')
    @pytest.mark.asyncio
    async def test_get_memory_graph_success(self, mock_mgclient):
        """Test successful memory graph retrieval."""
        mock_connection = Mock()
        mock_cursor = Mock()

        # Mock graph data
        mock_record = Mock()
        mock_record.values.return_value = [
            {
                "nodes": [
                    {"id": "memory-1", "properties": {"content": "Node 1"}},
                    {"id": "memory-2", "properties": {"content": "Node 2"}}
                ],
                "relationships": [
                    {
                        "start": "memory-1",
                        "end": "memory-2",
                        "type": "RELATES_TO",
                        "properties": {"strength": 0.8}
                    }
                ]
            }
        ]
        mock_cursor.fetchall.return_value = [mock_record]

        mock_connection.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_connection

        backend = MemgraphBackend(self.config)

        graph = await backend.get_memory_graph("center-memory", depth=2)

        assert graph is not None
        assert "nodes" in graph
        assert "relationships" in graph

    @patch('memory.backends.memgraph_backend.mgclient')
    def test_get_backend_stats(self, mock_mgclient):
        """Test getting backend statistics."""
        mock_connection = Mock()
        mock_cursor = Mock()

        # Mock stats query results
        mock_records = [
            Mock(values=Mock(return_value=[100])),  # total_memories
            Mock(values=Mock(return_value=[50])),   # total_relationships
        ]
        mock_cursor.fetchall.side_effect = [
            [mock_records[0]],  # First query
            [mock_records[1]]   # Second query
        ]

        mock_connection.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_connection

        backend = MemgraphBackend(self.config)

        stats = backend.get_backend_stats()

        assert stats["backend_type"] == "memgraph"
        assert stats["connection_status"] == "connected"

    @patch('memory.backends.memgraph_backend.mgclient')
    @pytest.mark.asyncio
    async def test_clear_all_memories_success(self, mock_mgclient):
        """Test successful clearing of all memories."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_connection

        backend = MemgraphBackend(self.config)

        success = await backend.clear_all_memories()

        assert success is True
        mock_cursor.execute.assert_called()

        # Verify clear query
        query = mock_cursor.execute.call_args[0][0]
        assert "MATCH" in query and "DELETE" in query

    @patch('memory.backends.memgraph_backend.mgclient')
    @pytest.mark.asyncio
    async def test_close_connection(self, mock_mgclient):
        """Test connection closing."""
        mock_connection = Mock()
        mock_mgclient.connect.return_value = mock_connection

        backend = MemgraphBackend(self.config)

        await backend.close()

        mock_connection.close.assert_called_once()
        assert backend.connection is None
        assert backend.is_connected is False

    def test_connection_health_check(self):
        """Test connection health checking."""
        # No connection
        backend = MemgraphBackend(self.config)
        backend.connection = None
        backend.is_connected = False

        assert not backend.is_healthy()

        # With connection
        with patch('memory.backends.memgraph_backend.mgclient') as mock_mgclient:
            mock_connection = Mock()
            mock_mgclient.connect.return_value = mock_connection

            backend = MemgraphBackend(self.config)
            assert backend.is_healthy()


class TestMemgraphBackendIntegration:
    """Integration tests for MemgraphBackend."""

    def setup_method(self):
        """Set up integration test fixtures."""
        self.config = {
            "host": "localhost",
            "port": 7687,
            "username": "test",
            "password": "test"
        }

    @patch('memory.backends.memgraph_backend.mgclient')
    @pytest.mark.asyncio
    async def test_memory_lifecycle(self, mock_mgclient):
        """Test complete memory lifecycle."""
        # Setup mocks
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_connection

        # For retrieval, mock the return data
        mock_record = Mock()
        mock_record.values.return_value = [
            "test-memory",
            "Test content",
            "HIGH",
            '{"type": "test"}',
            datetime.now().isoformat()
        ]
        mock_cursor.fetchall.return_value = [mock_record]

        backend = MemgraphBackend(self.config)

        # Create memory
        memory = Memory(
            id="test-memory",
            content="Test content",
            importance=MemoryImportance.HIGH,
            metadata={"type": "test"}
        )

        # Store
        store_success = await backend.store_memory(memory)
        assert store_success is True

        # Retrieve
        retrieved = await backend.retrieve_memory("test-memory")
        assert retrieved is not None
        assert retrieved.content == "Test content"

        # Update
        update_success = await backend.update_memory(
            "test-memory",
            {"content": "Updated content"}
        )
        assert update_success is True

        # Delete
        delete_success = await backend.delete_memory("test-memory")
        assert delete_success is True

    @patch('memory.backends.memgraph_backend.mgclient')
    @pytest.mark.asyncio
    async def test_relationship_workflow(self, mock_mgclient):
        """Test relationship creation and retrieval workflow."""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_connection

        # Mock related memories
        mock_record = Mock()
        mock_record.values.return_value = [
            "related-memory",
            "Related content",
            "MEDIUM",
            '{"context": "related"}',
            datetime.now().isoformat()
        ]
        mock_cursor.fetchall.return_value = [mock_record]

        backend = MemgraphBackend(self.config)

        # Create relationship
        rel_success = await backend.create_relationship(
            "memory-1",
            "memory-2",
            "CONNECTS_TO",
            {"strength": 0.9}
        )
        assert rel_success is True

        # Get related memories
        related = await backend.get_related_memories("memory-1")
        assert len(related) == 1
        assert related[0].content == "Related content"


class TestMemgraphBackendEdgeCases:
    """Test edge cases and error conditions."""

    @patch('memory.backends.memgraph_backend.mgclient')
    def test_invalid_config(self, mock_mgclient):
        """Test handling of invalid configuration."""
        # Missing required fields
        invalid_config = {"host": "localhost"}

        mock_mgclient.connect.side_effect = Exception("Invalid config")

        backend = MemgraphBackend(invalid_config)

        assert backend.connection is None
        assert not backend.is_connected

    @patch('memory.backends.memgraph_backend.mgclient')
    @pytest.mark.asyncio
    async def test_operations_without_connection(self, mock_mgclient):
        """Test operations when not connected."""
        backend = MemgraphBackend(self.config)
        backend.connection = None
        backend.is_connected = False

        memory = Memory(
            id="test",
            content="test",
            importance=MemoryImportance.LOW
        )

        # All operations should fail gracefully
        assert await backend.store_memory(memory) is False
        assert await backend.retrieve_memory("test") is None
        assert await backend.delete_memory("test") is False
        assert await backend.update_memory("test", {}) is False
        assert await backend.search_memories("query") == []

    @patch('memory.backends.memgraph_backend.mgclient')
    @pytest.mark.asyncio
    async def test_malformed_data_handling(self, mock_mgclient):
        """Test handling of malformed data."""
        mock_connection = Mock()
        mock_cursor = Mock()

        # Mock malformed record
        mock_record = Mock()
        mock_record.values.return_value = [
            "test-id",
            None,  # Malformed content
            "INVALID_IMPORTANCE",  # Invalid importance
            "invalid_json",  # Invalid JSON
            "invalid_date"  # Invalid date
        ]
        mock_cursor.fetchall.return_value = [mock_record]

        mock_connection.cursor.return_value = mock_cursor
        mock_mgclient.connect.return_value = mock_connection

        backend = MemgraphBackend(self.config)

        # Should handle malformed data gracefully
        memory = await backend.retrieve_memory("test-id")

        # Should either return None or a memory with default values
        if memory is not None:
            assert memory.id == "test-id"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])