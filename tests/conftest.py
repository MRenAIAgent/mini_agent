"""Pytest configuration and global fixtures for mini_agent tests."""

import sys
import asyncio
from pathlib import Path
import pytest
from unittest.mock import Mock, AsyncMock, patch

# Add the project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import test fixtures
try:
    from tests.fixtures.test_fixtures import (
        TestMemoryFactory,
        TestToolFactory,
        MockLLMFactory,
        TestAgentFactory,
        TestConfigFactory,
        TestDataFactory,
        TestEnvironment,
        AsyncTestHelper
    )
except ImportError:
    # Fallback to simple fixtures
    from tests.fixtures.simple_fixtures import (
        create_simple_mock_llm,
        create_mock_memory_manager,
        create_mock_tool_manager,
        AsyncTestHelper
    )
    TestMemoryFactory = None
    TestToolFactory = None
    MockLLMFactory = None
    TestAgentFactory = None
    TestConfigFactory = None
    TestDataFactory = None
    TestEnvironment = None


def pytest_configure(config):
    """Configure pytest."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_redis: mark test as requiring Redis"
    )
    config.addinivalue_line(
        "markers", "requires_memgraph: mark test as requiring Memgraph"
    )


def pytest_collection_modifyitems(config, items):
    """Modify collected test items."""
    for item in items:
        # Add unit marker to tests in unit/ directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Add integration marker to tests in integration/ directory
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm_simple():
    """Provide a simple mock LLM function."""
    if MockLLMFactory:
        return MockLLMFactory.create_simple_mock()
    else:
        return create_simple_mock_llm()


@pytest.fixture
def mock_llm_conversation():
    """Provide a mock LLM with conversation responses."""
    if MockLLMFactory:
        responses = [
            "Hello! How can I help you?",
            "I understand your question.",
            "Here's the information you requested.",
            "Is there anything else I can help with?"
        ]
        return MockLLMFactory.create_conversation_mock(responses)
    else:
        mock_llm = AsyncMock()
        mock_llm.side_effect = [
            "Hello! How can I help you?",
            "I understand your question.",
            "Here's the information you requested.",
            "Is there anything else I can help with?"
        ]
        return mock_llm


@pytest.fixture
def mock_llm_streaming():
    """Provide a mock LLM with streaming responses."""
    if MockLLMFactory:
        chunks = ["Hello ", "there! ", "How ", "can ", "I ", "help?"]
        return MockLLMFactory.create_streaming_mock(chunks)
    else:
        async def mock_stream():
            for chunk in ["Hello ", "there! ", "How ", "can ", "I ", "help?"]:
                yield chunk
        mock_llm = AsyncMock()
        mock_llm.return_value = mock_stream()
        return mock_llm


@pytest.fixture
def test_memories():
    """Provide test memory objects."""
    return TestMemoryFactory.create_memories(5)


@pytest.fixture
def conversation_memories():
    """Provide conversation-like memory objects."""
    return TestMemoryFactory.create_conversation_memories(3)


@pytest.fixture
def echo_tool():
    """Provide an echo tool for testing."""
    return TestToolFactory.create_echo_tool()


@pytest.fixture
def calculator_tool():
    """Provide a calculator tool for testing."""
    return TestToolFactory.create_calculator_tool()


@pytest.fixture
def failing_tool():
    """Provide a tool that fails for testing error handling."""
    return TestToolFactory.create_failing_tool(should_fail=True)


@pytest.fixture
def working_tool():
    """Provide a tool that works for testing success paths."""
    return TestToolFactory.create_failing_tool(should_fail=False)


@pytest.fixture
def test_llm_config():
    """Provide a test LLM configuration."""
    return TestConfigFactory.create_llm_config()


@pytest.fixture
def test_llm_messages():
    """Provide test LLM messages."""
    return TestDataFactory.create_llm_messages()


@pytest.fixture
def test_llm_response():
    """Provide a test LLM response."""
    return TestDataFactory.create_llm_response()


@pytest.fixture
def test_tool_calls():
    """Provide test tool calls."""
    return TestDataFactory.create_tool_calls()


@pytest.fixture
def test_env():
    """Provide a test environment with cleanup."""
    env = TestEnvironment()
    yield env
    env.cleanup()


@pytest.fixture
async def in_memory_backend():
    """Provide an in-memory backend for testing."""
    try:
        from memory.backends.in_memory_backend import InMemoryBackend
        return InMemoryBackend()
    except ImportError:
        pytest.skip("InMemoryBackend not available")


@pytest.fixture
async def memory_manager_with_backend():
    """Provide a memory manager with in-memory backend."""
    try:
        from memory.memory_manager import CoreMemoryManager
        from memory.backends.in_memory_backend import InMemoryBackend

        manager = CoreMemoryManager()
        backend = InMemoryBackend()
        await manager.set_backend("test", backend)
        return manager
    except ImportError:
        pytest.skip("Memory components not available")


@pytest.fixture
async def tool_manager():
    """Provide a tool manager."""
    try:
        from tools.tool_manager import ToolManager
        return ToolManager()
    except ImportError:
        pytest.skip("ToolManager not available")


@pytest.fixture
async def basic_agent(mock_llm_simple, memory_manager_with_backend, tool_manager):
    """Provide a basic agent for testing."""
    try:
        from agent import CoreAgent
        return CoreAgent(
            llm_function=mock_llm_simple,
            memory_manager=memory_manager_with_backend,
            tool_manager=tool_manager
        )
    except ImportError:
        pytest.skip("CoreAgent not available")


@pytest.fixture
async def agent_with_tools(basic_agent, echo_tool, calculator_tool):
    """Provide an agent with registered tools."""
    await basic_agent.tool_manager.register_tool(echo_tool)
    await basic_agent.tool_manager.register_tool(calculator_tool)
    return basic_agent


@pytest.fixture
def mock_redis():
    """Provide a mock Redis client."""
    mock_redis = Mock()
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.exists = AsyncMock(return_value=0)
    mock_redis.keys = AsyncMock(return_value=[])
    mock_redis.flushdb = AsyncMock(return_value=True)
    mock_redis.close = AsyncMock()
    return mock_redis


@pytest.fixture
def mock_memgraph():
    """Provide a mock Memgraph connection."""
    mock_connection = Mock()
    mock_cursor = Mock()
    mock_connection.cursor.return_value = mock_cursor
    mock_cursor.execute = Mock()
    mock_cursor.fetchall = Mock(return_value=[])
    mock_cursor.fetchone = Mock(return_value=None)
    mock_connection.close = Mock()
    return mock_connection


@pytest.fixture
def patch_redis(mock_redis):
    """Patch Redis client for testing."""
    with patch('redis.asyncio.Redis', return_value=mock_redis):
        yield mock_redis


@pytest.fixture
def patch_memgraph(mock_memgraph):
    """Patch Memgraph client for testing."""
    with patch('memory.backends.memgraph_backend.mgclient') as mock_mgclient:
        mock_mgclient.connect.return_value = mock_memgraph
        yield mock_memgraph


@pytest.fixture
def patch_litellm():
    """Patch LiteLLM for testing."""
    with patch('integrations.litellm_provider.litellm') as mock_litellm:
        # Setup common mock responses
        mock_litellm.validate_environment.return_value = True
        mock_litellm.get_supported_openai_params.return_value = [
            'temperature', 'max_tokens', 'top_p'
        ]
        mock_litellm.model_list = ["gpt-3.5-turbo", "gpt-4", "claude-3"]
        mock_litellm.completion_cost.return_value = 0.002

        # Mock completion response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Mock LiteLLM response"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_litellm.acompletion = AsyncMock(return_value=mock_response)

        yield mock_litellm


@pytest.fixture
def capture_logs():
    """Capture log messages during tests."""
    import logging
    from io import StringIO

    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)

    # Add handler to root logger
    root_logger = logging.getLogger()
    original_level = root_logger.level
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)

    yield log_capture

    # Cleanup
    root_logger.removeHandler(handler)
    root_logger.setLevel(original_level)


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset any singleton instances between tests."""
    # This fixture runs automatically for each test
    # Add any singleton reset logic here if needed
    yield
    # Cleanup after test


# Custom pytest markers for different test categories
pytestmark = [
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
    pytest.mark.filterwarnings("ignore::PendingDeprecationWarning"),
]


# Helper functions for test discovery
def is_unit_test(test_path: str) -> bool:
    """Check if a test is a unit test."""
    return "unit" in test_path


def is_integration_test(test_path: str) -> bool:
    """Check if a test is an integration test."""
    return "integration" in test_path


def requires_external_service(markers) -> bool:
    """Check if test requires external services."""
    external_markers = {"requires_redis", "requires_memgraph"}
    return any(marker.name in external_markers for marker in markers)


# Test collection hooks
def pytest_runtest_setup(item):
    """Setup hook for each test."""
    # Skip tests requiring external services if not available
    if requires_external_service(item.iter_markers()):
        # Add logic to check if external services are available
        pass


def pytest_runtest_teardown(item, nextitem):
    """Teardown hook for each test."""
    # Cleanup any test artifacts
    pass


# Custom assertion helpers
def assert_memory_equal(memory1, memory2):
    """Assert that two memory objects are equal."""
    assert memory1.id == memory2.id
    assert memory1.content == memory2.content
    assert memory1.importance == memory2.importance
    assert memory1.metadata == memory2.metadata


def assert_tool_result_success(result):
    """Assert that a tool result is successful."""
    assert result.success is True
    assert result.error is None
    assert result.content is not None


def assert_tool_result_failure(result, expected_error=None):
    """Assert that a tool result is a failure."""
    assert result.success is False
    assert result.error is not None
    if expected_error:
        assert expected_error in result.error


# Export helper functions
__all__ = [
    'assert_memory_equal',
    'assert_tool_result_success',
    'assert_tool_result_failure',
    'is_unit_test',
    'is_integration_test',
    'requires_external_service'
]