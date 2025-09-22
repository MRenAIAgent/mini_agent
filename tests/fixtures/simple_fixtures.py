"""Simplified test fixtures that work without imports."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any, List, Optional, Callable
import pytest
from datetime import datetime, timedelta
import tempfile
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def create_mock_memory(id: str = "test_memory", content: str = "Test content") -> Mock:
    """Create a mock memory object."""
    memory = Mock()
    memory.id = id
    memory.content = content
    memory.importance = Mock()
    memory.metadata = {}
    memory.created_at = datetime.now()
    return memory


def create_mock_tool_result(success: bool = True, content: str = "Mock result") -> Mock:
    """Create a mock tool result."""
    result = Mock()
    result.success = success
    result.content = content if success else None
    result.error = None if success else "Mock error"
    result.execution_time = 0.1
    result.call_id = "test_call"
    return result


def create_mock_llm_response(content: str = "Mock LLM response") -> Mock:
    """Create a mock LLM response."""
    response = Mock()
    response.content = content
    response.model = "test-model"
    response.usage = {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    response.metadata = {}
    response.timestamp = datetime.now()
    return response


def create_simple_mock_llm() -> AsyncMock:
    """Create a simple mock LLM function."""
    mock_llm = AsyncMock()
    mock_llm.return_value = "Mock LLM response"
    return mock_llm


def create_mock_memory_manager() -> Mock:
    """Create a mock memory manager."""
    manager = Mock()
    manager.add_memory = AsyncMock(return_value=True)
    manager.get_memory = AsyncMock(return_value=None)
    manager.search_memories = AsyncMock(return_value=[])
    manager.get_all_memories = AsyncMock(return_value=[])
    manager.clear_all_memories = AsyncMock(return_value=True)
    manager.set_backend = AsyncMock(return_value=True)
    return manager


def create_mock_tool_manager() -> Mock:
    """Create a mock tool manager."""
    manager = Mock()
    manager.register_tool = AsyncMock(return_value=True)
    manager.execute_tool_by_name = AsyncMock(return_value=create_mock_tool_result())
    manager.execute_tool = AsyncMock(return_value=create_mock_tool_result())
    manager.has_tool = Mock(return_value=True)
    manager.list_available_tools = Mock(return_value=[])
    manager.get_tool_by_name = Mock(return_value=None)
    return manager


class AsyncTestHelper:
    """Helper utilities for async testing."""

    @staticmethod
    def run_async(coro):
        """Run an async coroutine in tests."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(coro)


# Pytest fixtures using simple mocks
@pytest.fixture
def mock_memory():
    """Provide a mock memory object."""
    return create_mock_memory()


@pytest.fixture
def mock_memories():
    """Provide multiple mock memory objects."""
    return [create_mock_memory(f"mem_{i}", f"Content {i}") for i in range(5)]


@pytest.fixture
def mock_tool_result():
    """Provide a mock tool result."""
    return create_mock_tool_result()


@pytest.fixture
def mock_llm_response():
    """Provide a mock LLM response."""
    return create_mock_llm_response()


@pytest.fixture
def mock_llm_simple():
    """Provide a simple mock LLM function."""
    return create_simple_mock_llm()


@pytest.fixture
def mock_memory_manager():
    """Provide a mock memory manager."""
    return create_mock_memory_manager()


@pytest.fixture
def mock_tool_manager():
    """Provide a mock tool manager."""
    return create_mock_tool_manager()


# Export functions
__all__ = [
    'create_mock_memory',
    'create_mock_tool_result',
    'create_mock_llm_response',
    'create_simple_mock_llm',
    'create_mock_memory_manager',
    'create_mock_tool_manager',
    'AsyncTestHelper'
]