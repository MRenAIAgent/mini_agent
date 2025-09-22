"""Shared test fixtures and utilities for the mini_agent test suite."""

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

try:
    from memory.memory_types import Memory, MemoryImportance
    from memory.memory_manager import CoreMemoryManager
    from memory.backends.in_memory_backend import InMemoryBackend
    from tools.tool_interfaces import ToolInterface, ToolCall, ToolResult, ToolDefinition
    from tools.tool_manager import ToolManager
    from integrations.llm_interfaces import LLMConfig, LLMMessage, LLMResponse
    from agent import CoreAgent
    from execution.execution_patterns import ExecutionPattern
except ImportError:
    # Handle missing imports gracefully in fixture file
    Memory = None
    MemoryImportance = None
    CoreMemoryManager = None
    InMemoryBackend = None
    ToolInterface = None
    ToolCall = None
    ToolResult = None
    ToolDefinition = None
    ToolManager = None
    LLMConfig = None
    LLMMessage = None
    LLMResponse = None
    CoreAgent = None
    ExecutionPattern = None


class TestMemoryFactory:
    """Factory for creating test memory objects."""

    @staticmethod
    def create_memory(
        id: str = None,
        content: str = "Test memory content",
        importance: 'MemoryImportance' = None,
        metadata: Dict[str, Any] = None,
        created_at: datetime = None
    ) -> 'Memory':
        """Create a test memory object."""
        if Memory is None:
            return None

        return Memory(
            id=id or f"test_memory_{datetime.now().timestamp()}",
            content=content,
            importance=importance or MemoryImportance.MEDIUM,
            metadata=metadata or {},
            created_at=created_at or datetime.now()
        )

    @staticmethod
    def create_memories(count: int = 5) -> List['Memory']:
        """Create multiple test memories."""
        memories = []
        for i in range(count):
            memory = TestMemoryFactory.create_memory(
                id=f"memory_{i}",
                content=f"Test memory content {i}",
                importance=list(MemoryImportance)[i % len(list(MemoryImportance))],
                metadata={"index": i, "type": "test"}
            )
            memories.append(memory)
        return memories

    @staticmethod
    def create_conversation_memories(turns: int = 3) -> List['Memory']:
        """Create conversation-like memories."""
        memories = []
        for i in range(turns):
            user_memory = TestMemoryFactory.create_memory(
                id=f"user_msg_{i}",
                content=f"User message {i}",
                importance=MemoryImportance.MEDIUM,
                metadata={"role": "user", "turn": i}
            )
            assistant_memory = TestMemoryFactory.create_memory(
                id=f"assistant_msg_{i}",
                content=f"Assistant response {i}",
                importance=MemoryImportance.MEDIUM,
                metadata={"role": "assistant", "turn": i}
            )
            memories.extend([user_memory, assistant_memory])
        return memories


class TestToolFactory:
    """Factory for creating test tools."""

    @staticmethod
    def create_echo_tool(name: str = "echo_tool"):
        """Create a simple echo tool for testing."""
        if ToolInterface is None:
            return None

        class EchoTool(ToolInterface):
            def __init__(self, tool_name):
                self.tool_name = tool_name

            def get_definition(self):
                return ToolDefinition(
                    name=self.tool_name,
                    description="Echoes back the input",
                    parameters={
                        "type": "object",
                        "properties": {
                            "message": {"type": "string", "description": "Message to echo"}
                        },
                        "required": ["message"]
                    },
                    category="test"
                )

            async def execute(self, tool_call):
                message = tool_call.arguments.get("message", "")
                return ToolResult(
                    call_id=tool_call.id,
                    success=True,
                    content=f"Echo: {message}",
                    execution_time=0.1
                )

        return EchoTool(name)

    @staticmethod
    def create_calculator_tool():
        """Create a calculator tool for testing."""
        class CalculatorTool(ToolInterface):
            def get_definition(self) -> ToolDefinition:
                return ToolDefinition(
                    name="calculator",
                    description="Performs mathematical calculations",
                    parameters={
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "enum": ["add", "subtract", "multiply", "divide"]
                            },
                            "a": {"type": "number"},
                            "b": {"type": "number"}
                        },
                        "required": ["operation", "a", "b"]
                    },
                    category="math"
                )

            async def execute(self, tool_call: ToolCall) -> ToolResult:
                try:
                    operation = tool_call.arguments.get("operation")
                    a = float(tool_call.arguments.get("a", 0))
                    b = float(tool_call.arguments.get("b", 0))

                    if operation == "add":
                        result = a + b
                    elif operation == "subtract":
                        result = a - b
                    elif operation == "multiply":
                        result = a * b
                    elif operation == "divide":
                        if b == 0:
                            raise ValueError("Division by zero")
                        result = a / b
                    else:
                        raise ValueError(f"Unknown operation: {operation}")

                    return ToolResult(
                        call_id=tool_call.id,
                        success=True,
                        content=str(result),
                        execution_time=0.1
                    )
                except Exception as e:
                    return ToolResult(
                        call_id=tool_call.id,
                        success=False,
                        error=str(e),
                        execution_time=0.1
                    )

        return CalculatorTool()

    @staticmethod
    def create_failing_tool(should_fail: bool = True) -> ToolInterface:
        """Create a tool that can be configured to fail."""
        class FailingTool(ToolInterface):
            def __init__(self, fail_mode):
                self.fail_mode = fail_mode

            def get_definition(self) -> ToolDefinition:
                return ToolDefinition(
                    name="failing_tool",
                    description="Tool that can fail for testing",
                    parameters={
                        "type": "object",
                        "properties": {
                            "input": {"type": "string"}
                        }
                    },
                    category="test"
                )

            async def execute(self, tool_call: ToolCall) -> ToolResult:
                if self.fail_mode:
                    return ToolResult(
                        call_id=tool_call.id,
                        success=False,
                        error="Simulated tool failure",
                        execution_time=0.1
                    )
                else:
                    return ToolResult(
                        call_id=tool_call.id,
                        success=True,
                        content="Tool executed successfully",
                        execution_time=0.1
                    )

        return FailingTool(should_fail)


class MockLLMFactory:
    """Factory for creating mock LLM functions."""

    @staticmethod
    def create_simple_mock() -> AsyncMock:
        """Create a simple mock LLM function."""
        mock_llm = AsyncMock()
        mock_llm.return_value = "Mock LLM response"
        return mock_llm

    @staticmethod
    def create_conversation_mock(responses: List[str]) -> AsyncMock:
        """Create a mock LLM with predefined responses."""
        mock_llm = AsyncMock()
        mock_llm.side_effect = responses
        return mock_llm

    @staticmethod
    def create_streaming_mock(chunks: List[str]) -> AsyncMock:
        """Create a mock LLM that returns streaming responses."""
        async def mock_stream():
            for chunk in chunks:
                yield chunk

        mock_llm = AsyncMock()
        mock_llm.return_value = mock_stream()
        return mock_llm

    @staticmethod
    def create_error_mock(error_message: str = "LLM Error") -> AsyncMock:
        """Create a mock LLM that raises an error."""
        mock_llm = AsyncMock()
        mock_llm.side_effect = Exception(error_message)
        return mock_llm


class TestAgentFactory:
    """Factory for creating test agent instances."""

    @staticmethod
    async def create_basic_agent(
        llm_function: Callable = None,
        with_memory: bool = True,
        with_tools: bool = True
    ) -> 'CoreAgent':
        """Create a basic test agent."""
        if CoreAgent is None:
            return None

        # Setup LLM
        if llm_function is None:
            llm_function = MockLLMFactory.create_simple_mock()

        # Setup memory
        memory_manager = None
        if with_memory:
            memory_manager = CoreMemoryManager()
            backend = InMemoryBackend()
            await memory_manager.set_backend("test", backend)

        # Setup tools
        tool_manager = None
        if with_tools:
            tool_manager = ToolManager()

        return CoreAgent(
            llm_function=llm_function,
            memory_manager=memory_manager,
            tool_manager=tool_manager
        )

    @staticmethod
    async def create_agent_with_tools(tools: List[ToolInterface]) -> 'CoreAgent':
        """Create agent with specific tools."""
        agent = await TestAgentFactory.create_basic_agent()

        for tool in tools:
            await agent.tool_manager.register_tool(tool)

        return agent


class TestConfigFactory:
    """Factory for creating test configurations."""

    @staticmethod
    def create_llm_config(
        provider: str = "openai",
        model: str = "gpt-3.5-turbo",
        **kwargs
    ) -> 'LLMConfig':
        """Create a test LLM configuration."""
        if LLMConfig is None:
            return None

        return LLMConfig(
            provider=provider,
            model=model,
            api_key="test-key",
            temperature=0.7,
            max_tokens=100,
            **kwargs
        )

    @staticmethod
    def create_memory_config(backend_type: str = "in_memory") -> Dict[str, Any]:
        """Create a test memory configuration."""
        configs = {
            "in_memory": {},
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0
            },
            "memgraph": {
                "host": "localhost",
                "port": 7687,
                "username": "memgraph",
                "password": "test"
            }
        }
        return configs.get(backend_type, {})


class TestDataFactory:
    """Factory for creating test data structures."""

    @staticmethod
    def create_llm_messages(count: int = 3) -> List['LLMMessage']:
        """Create test LLM messages."""
        if LLMMessage is None:
            return []

        messages = []
        roles = ["system", "user", "assistant"]

        for i in range(count):
            role = roles[i % len(roles)]
            content = f"Test {role} message {i}"

            message = LLMMessage(
                role=role,
                content=content,
                metadata={"index": i, "test": True}
            )
            messages.append(message)

        return messages

    @staticmethod
    def create_llm_response(
        content: str = "Test response",
        model: str = "test-model",
        usage: Dict[str, int] = None
    ) -> 'LLMResponse':
        """Create a test LLM response."""
        if LLMResponse is None:
            return None

        return LLMResponse(
            content=content,
            model=model,
            usage=usage or {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            metadata={"test": True}
        )

    @staticmethod
    def create_tool_calls(count: int = 2) -> List['ToolCall']:
        """Create test tool calls."""
        if ToolCall is None:
            return []

        calls = []
        for i in range(count):
            call = ToolCall(
                name=f"test_tool_{i}",
                arguments={"param": f"value_{i}", "index": i},
                metadata={"test": True}
            )
            calls.append(call)

        return calls


class TestEnvironment:
    """Test environment setup and teardown utilities."""

    def __init__(self):
        self.temp_files = []
        self.temp_dirs = []

    def create_temp_file(self, content: str = "", suffix: str = ".txt") -> str:
        """Create a temporary file for testing."""
        temp_file = tempfile.NamedTemporaryFile(
            mode='w+',
            suffix=suffix,
            delete=False
        )
        temp_file.write(content)
        temp_file.close()

        self.temp_files.append(temp_file.name)
        return temp_file.name

    def create_temp_dir(self) -> str:
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        return temp_dir

    def create_config_file(self, config: Dict[str, Any]) -> str:
        """Create a temporary config file."""
        config_content = json.dumps(config, indent=2)
        return self.create_temp_file(config_content, ".json")

    def cleanup(self):
        """Clean up temporary files and directories."""
        import os
        import shutil

        for file_path in self.temp_files:
            try:
                os.unlink(file_path)
            except FileNotFoundError:
                pass

        for dir_path in self.temp_dirs:
            try:
                shutil.rmtree(dir_path)
            except FileNotFoundError:
                pass

        self.temp_files.clear()
        self.temp_dirs.clear()


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

    @staticmethod
    async def wait_for_condition(
        condition: Callable[[], bool],
        timeout: float = 5.0,
        interval: float = 0.1
    ) -> bool:
        """Wait for a condition to become true."""
        start_time = asyncio.get_event_loop().time()

        while True:
            if condition():
                return True

            current_time = asyncio.get_event_loop().time()
            if current_time - start_time > timeout:
                return False

            await asyncio.sleep(interval)

    @staticmethod
    async def collect_async_generator(async_gen, limit: int = 100) -> List[Any]:
        """Collect items from an async generator."""
        items = []
        count = 0

        async for item in async_gen:
            items.append(item)
            count += 1
            if count >= limit:
                break

        return items


# Pytest fixtures
@pytest.fixture
def test_environment():
    """Provide a test environment with cleanup."""
    env = TestEnvironment()
    yield env
    env.cleanup()


@pytest.fixture
def memory_factory():
    """Provide memory factory."""
    return TestMemoryFactory


@pytest.fixture
def tool_factory():
    """Provide tool factory."""
    return TestToolFactory


@pytest.fixture
def llm_factory():
    """Provide LLM mock factory."""
    return MockLLMFactory


@pytest.fixture
def config_factory():
    """Provide config factory."""
    return TestConfigFactory


@pytest.fixture
def data_factory():
    """Provide data factory."""
    return TestDataFactory


@pytest.fixture
async def basic_agent():
    """Provide a basic test agent."""
    if CoreAgent is None:
        pytest.skip("CoreAgent not available")

    return await TestAgentFactory.create_basic_agent()


@pytest.fixture
async def memory_manager():
    """Provide a memory manager with in-memory backend."""
    if CoreMemoryManager is None:
        pytest.skip("CoreMemoryManager not available")

    manager = CoreMemoryManager()
    backend = InMemoryBackend()
    await manager.set_backend("test", backend)
    return manager


@pytest.fixture
async def tool_manager():
    """Provide a tool manager."""
    if ToolManager is None:
        pytest.skip("ToolManager not available")

    return ToolManager()


# Test utilities
def skip_if_missing(*modules):
    """Decorator to skip tests if modules are missing."""
    def decorator(test_func):
        for module in modules:
            if module is None:
                return pytest.mark.skip(f"Required module not available")(test_func)
        return test_func
    return decorator


def async_test(func):
    """Decorator to run async test functions."""
    def wrapper(*args, **kwargs):
        return AsyncTestHelper.run_async(func(*args, **kwargs))
    return wrapper


# Export commonly used factories for convenience
__all__ = [
    'TestMemoryFactory',
    'TestToolFactory',
    'MockLLMFactory',
    'TestAgentFactory',
    'TestConfigFactory',
    'TestDataFactory',
    'TestEnvironment',
    'AsyncTestHelper',
    'skip_if_missing',
    'async_test'
]