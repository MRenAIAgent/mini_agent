"""Unit tests for the simple CoreAgent implementation."""

import asyncio
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from agent_simple import CoreAgent
    from memory.memory_manager import CoreMemoryManager
    from tools.tool_manager import ToolManager
    from execution.execution_patterns import ExecutionPatternType
except ImportError as e:
    pytest.skip(f"Agent imports not available: {e}", allow_module_level=True)


class TestSimpleAgentInitialization:
    """Test simple agent initialization."""

    def test_agent_init_with_llm_function(self):
        """Test agent initialization with LLM function."""
        mock_llm = AsyncMock(return_value="test response")
        agent = CoreAgent(llm_function=mock_llm)

        assert agent.llm_function == mock_llm
        assert agent.llm_config is None
        assert isinstance(agent.memory_manager, CoreMemoryManager)
        assert isinstance(agent.tool_manager, ToolManager)
        assert agent.system_prompt == "You are a helpful AI assistant."
        assert agent.max_iterations == 5

    def test_agent_init_with_llm_config(self):
        """Test agent initialization with LLM config."""
        config = {"provider": "openai", "model": "gpt-3.5-turbo"}
        agent = CoreAgent(llm_config=config)

        assert agent.llm_function is None
        assert agent.llm_config == config

    def test_agent_init_no_llm_raises_error(self):
        """Test that initialization without LLM raises error."""
        with pytest.raises(ValueError, match="Must provide either llm_function or llm_config"):
            CoreAgent()

    def test_agent_init_with_custom_components(self):
        """Test initialization with custom components."""
        mock_llm = AsyncMock()
        mock_memory = Mock()
        mock_tools = Mock()

        agent = CoreAgent(
            llm_function=mock_llm,
            memory_manager=mock_memory,
            tool_manager=mock_tools,
            system_prompt="Custom prompt",
            max_iterations=10
        )

        assert agent.memory_manager == mock_memory
        assert agent.tool_manager == mock_tools
        assert agent.system_prompt == "Custom prompt"
        assert agent.max_iterations == 10


class TestSimpleAgentBasicOperations:
    """Test basic agent operations."""

    @pytest.fixture
    def mock_agent(self):
        """Create agent with mock LLM."""
        mock_llm = AsyncMock(return_value="Mock response")
        return CoreAgent(llm_function=mock_llm)

    @pytest.mark.asyncio
    async def test_run_basic(self, mock_agent):
        """Test basic run method."""
        response = await mock_agent.run("Hello")

        assert response == "Mock response"
        mock_agent.llm_function.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_empty_message_raises_error(self, mock_agent):
        """Test that empty message raises error."""
        with pytest.raises(ValueError, match="Message cannot be empty"):
            await mock_agent.run("")

    @pytest.mark.asyncio
    async def test_run_with_context(self, mock_agent):
        """Test run with context."""
        context = {"user_id": "123", "session": "test"}
        response = await mock_agent.run("Hello", context=context)

        assert response == "Mock response"
        # Check that prompt included context
        call_args = mock_agent.llm_function.call_args[0][0]
        assert "user_id: 123" in call_args
        assert "session: test" in call_args

    @pytest.mark.asyncio
    async def test_run_updates_stats(self, mock_agent):
        """Test that run updates execution stats."""
        initial_stats = mock_agent.get_stats()
        assert initial_stats["total_runs"] == 0
        assert initial_stats["successful_runs"] == 0

        await mock_agent.run("Hello")

        updated_stats = mock_agent.get_stats()
        assert updated_stats["total_runs"] == 1
        assert updated_stats["successful_runs"] == 1
        assert updated_stats["total_execution_time"] > 0

    @pytest.mark.asyncio
    async def test_run_error_handling(self):
        """Test error handling in run method."""
        mock_llm = AsyncMock(side_effect=Exception("LLM Error"))
        agent = CoreAgent(llm_function=mock_llm)

        with pytest.raises(Exception, match="LLM Error"):
            await agent.run("Hello")

        # Stats should still be updated
        stats = agent.get_stats()
        assert stats["total_runs"] == 1
        assert stats["successful_runs"] == 0


class TestSimpleAgentStreaming:
    """Test streaming functionality."""

    @pytest.mark.asyncio
    async def test_run_stream_basic(self):
        """Test basic streaming."""
        mock_llm = AsyncMock(return_value="Stream response")
        agent = CoreAgent(llm_function=mock_llm)

        chunks = []
        async for chunk in agent.run_stream("Hello"):
            chunks.append(chunk)

        assert chunks == ["Stream response"]

    @pytest.mark.asyncio
    async def test_run_stream_empty_message_raises_error(self):
        """Test that empty message raises error in streaming."""
        mock_llm = AsyncMock()
        agent = CoreAgent(llm_function=mock_llm)

        with pytest.raises(ValueError, match="Message cannot be empty"):
            async for chunk in agent.run_stream(""):
                pass

    @pytest.mark.asyncio
    async def test_run_stream_with_async_generator(self):
        """Test streaming with async generator LLM."""
        async def mock_streaming_llm(prompt):
            for chunk in ["Hello ", "world", "!"]:
                yield chunk

        agent = CoreAgent(llm_function=mock_streaming_llm)

        chunks = []
        async for chunk in agent.run_stream("Hello"):
            chunks.append(chunk)

        assert chunks == ["Hello ", "world", "!"]


class TestSimpleAgentBenchmarking:
    """Test benchmarking functionality."""

    @pytest.mark.asyncio
    async def test_run_benchmark_basic(self):
        """Test basic benchmarking."""
        mock_llm = AsyncMock(return_value="Benchmark response")
        agent = CoreAgent(llm_function=mock_llm)

        test_cases = [
            {"input": "Test 1"},
            {"input": "Test 2"},
            {"input": "Test 3"}
        ]

        results = await agent.run_benchmark(test_cases)

        assert results["total_scenarios"] == 3
        assert results["successful_runs"] == 3
        assert results["failed_runs"] == 0
        assert results["average_response_time"] > 0
        assert results["total_time"] > 0

    @pytest.mark.asyncio
    async def test_run_benchmark_empty_test_cases(self):
        """Test benchmarking with empty test cases."""
        mock_llm = AsyncMock()
        agent = CoreAgent(llm_function=mock_llm)

        results = await agent.run_benchmark([])

        assert results["total_scenarios"] == 0
        assert results["successful_runs"] == 0
        assert results["failed_runs"] == 0
        assert results["average_response_time"] == 0.0

    @pytest.mark.asyncio
    async def test_run_benchmark_with_errors(self):
        """Test benchmarking with some errors."""
        mock_llm = AsyncMock()
        mock_llm.side_effect = [
            "Success 1",
            Exception("Error"),
            "Success 2"
        ]
        agent = CoreAgent(llm_function=mock_llm)

        test_cases = [
            {"input": "Test 1"},
            {"input": "Test 2"},
            {"input": "Test 3"}
        ]

        results = await agent.run_benchmark(test_cases)

        assert results["total_scenarios"] == 3
        assert results["successful_runs"] == 2
        assert results["failed_runs"] == 1


class TestSimpleAgentToolsAndMemory:
    """Test tools and memory integration."""

    @pytest.fixture
    def agent_with_mocks(self):
        """Create agent with mocked components."""
        mock_llm = AsyncMock(return_value="Response")
        mock_memory = Mock()
        mock_memory.add_memory = AsyncMock(return_value=True)
        mock_tools = Mock()
        mock_tools.register_tool = AsyncMock(return_value=True)
        mock_tools.connect_mcp_server = AsyncMock(return_value=True)

        return CoreAgent(
            llm_function=mock_llm,
            memory_manager=mock_memory,
            tool_manager=mock_tools
        )

    @pytest.mark.asyncio
    async def test_add_tool(self, agent_with_mocks):
        """Test adding a tool."""
        mock_tool = Mock()
        result = await agent_with_mocks.add_tool(mock_tool)

        assert result is True
        agent_with_mocks.tool_manager.register_tool.assert_called_once_with(mock_tool)

    @pytest.mark.asyncio
    async def test_connect_mcp_server(self, agent_with_mocks):
        """Test connecting to MCP server."""
        connection_info = {"host": "localhost", "port": 8080}
        result = await agent_with_mocks.connect_mcp_server("test_server", connection_info)

        assert result is True
        agent_with_mocks.tool_manager.connect_mcp_server.assert_called_once_with(
            "test_server", connection_info
        )

    def test_add_example(self, agent_with_mocks):
        """Test adding examples."""
        agent_with_mocks.add_example("Input text", "Output text", {"category": "test"})

        # Should not raise an error
        assert True

    def test_get_examples(self, agent_with_mocks):
        """Test getting examples."""
        examples = agent_with_mocks.get_examples()

        assert isinstance(examples, list)
        assert len(examples) == 0  # Empty for now


class TestSimpleAgentLifecycle:
    """Test agent lifecycle methods."""

    @pytest.fixture
    def mock_agent(self):
        """Create mock agent."""
        mock_llm = AsyncMock()
        return CoreAgent(llm_function=mock_llm)

    @pytest.mark.asyncio
    async def test_start_stop(self, mock_agent):
        """Test start and stop methods."""
        await mock_agent.start()
        await mock_agent.stop()

        # Should not raise errors
        assert True

    def test_clone(self, mock_agent):
        """Test agent cloning."""
        cloned_agent = mock_agent.clone()

        assert cloned_agent is not mock_agent
        assert cloned_agent.llm_function == mock_agent.llm_function
        assert cloned_agent.system_prompt == mock_agent.system_prompt
        assert cloned_agent.max_iterations == mock_agent.max_iterations

    def test_set_execution_pattern(self, mock_agent):
        """Test setting execution pattern."""
        # Should not raise an error (placeholder implementation)
        mock_agent.set_execution_pattern(ExecutionPatternType.SIMPLE)
        assert True


class TestSimpleAgentMemoryIntegration:
    """Test memory integration."""

    @pytest.mark.asyncio
    async def test_memory_storage_during_run(self):
        """Test that interactions are stored in memory."""
        mock_llm = AsyncMock(return_value="Response")
        mock_memory = Mock()
        mock_memory.add_memory = AsyncMock(return_value=True)

        agent = CoreAgent(llm_function=mock_llm, memory_manager=mock_memory)

        await agent.run("Hello")

        # Should store both user message and assistant response
        assert mock_memory.add_memory.call_count == 2

        # Check call arguments
        calls = mock_memory.add_memory.call_args_list
        user_call = calls[0][1]  # keyword arguments
        assistant_call = calls[1][1]

        assert user_call["content"] == "Hello"
        assert user_call["metadata"]["role"] == "user"
        assert assistant_call["content"] == "Response"
        assert assistant_call["metadata"]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_memory_error_handling(self):
        """Test that memory errors don't break the agent."""
        mock_llm = AsyncMock(return_value="Response")
        mock_memory = Mock()
        mock_memory.add_memory = AsyncMock(side_effect=Exception("Memory error"))

        agent = CoreAgent(llm_function=mock_llm, memory_manager=mock_memory)

        # Should not raise an error despite memory failure
        response = await agent.run("Hello")
        assert response == "Response"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])