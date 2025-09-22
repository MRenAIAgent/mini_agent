"""
Comprehensive unit tests for CoreAgent class.

These tests validate the core functionality of the agent including
initialization, LLM integration, memory operations, and tool execution.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any
import uuid

# Import the classes we want to test
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agent import CoreAgent
from execution.execution_patterns import ExecutionPatternType
from integrations.llm_interfaces import LLMConfig


class TestCoreAgentInitialization:
    """Test CoreAgent initialization and configuration."""

    @pytest.fixture
    def mock_llm_function(self):
        """Mock LLM function for testing."""
        async def mock_llm(prompt: str) -> str:
            return f"Mock response to: {prompt[:50]}"
        return mock_llm

    @pytest.fixture
    def valid_llm_config(self):
        """Valid LLM configuration for testing."""
        return {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "api_key": "test-key",
            "temperature": 0.7
        }

    def test_agent_initialization_with_llm_function(self, mock_llm_function):
        """Test agent initialization with legacy llm_function."""
        agent = CoreAgent(llm_function=mock_llm_function)

        assert agent.llm_function == mock_llm_function
        assert agent.llm_config is None
        assert agent.system_prompt == ""
        assert agent.max_iterations == 5
        assert agent.session_id is not None
        assert len(agent.session_id) > 0

    def test_agent_initialization_with_llm_config(self, valid_llm_config):
        """Test agent initialization with new llm_config."""
        agent = CoreAgent(llm_config=valid_llm_config)

        assert agent.llm_function is None
        assert agent.llm_config == valid_llm_config
        assert agent.system_prompt == ""
        assert agent.max_iterations == 5

    def test_agent_initialization_with_custom_params(self, mock_llm_function):
        """Test agent initialization with custom parameters."""
        custom_prompt = "You are a helpful assistant."
        custom_session = "test-session-123"

        agent = CoreAgent(
            llm_function=mock_llm_function,
            system_prompt=custom_prompt,
            max_iterations=10,
            session_id=custom_session,
            execution_pattern=ExecutionPatternType.SIMPLE
        )

        assert agent.system_prompt == custom_prompt
        assert agent.max_iterations == 10
        assert agent.session_id == custom_session
        assert agent.execution_pattern == ExecutionPatternType.SIMPLE

    def test_agent_initialization_conflicting_configs(self, mock_llm_function, valid_llm_config):
        """Test that providing both llm_function and llm_config raises error."""
        with pytest.raises(ValueError, match="Cannot provide both llm_function and llm_config"):
            CoreAgent(llm_function=mock_llm_function, llm_config=valid_llm_config)

    def test_agent_initialization_no_llm(self):
        """Test that providing neither llm_function nor llm_config raises error."""
        with pytest.raises(ValueError, match="Must provide either llm_function"):
            CoreAgent()

    def test_agent_components_initialization(self, mock_llm_function):
        """Test that agent components are properly initialized."""
        agent = CoreAgent(llm_function=mock_llm_function)

        assert agent.tool_manager is not None
        assert agent.memory_manager is not None
        assert agent.current_pattern == ExecutionPatternType.REACT


class TestCoreAgentBasicOperations:
    """Test basic agent operations like run method."""

    @pytest.fixture
    def agent_with_mock_llm(self):
        """Agent with mocked LLM function."""
        mock_llm = AsyncMock(return_value="Mock LLM response")
        return CoreAgent(llm_function=mock_llm), mock_llm

    @pytest.mark.asyncio
    async def test_basic_run_method(self, agent_with_mock_llm):
        """Test basic run method functionality."""
        agent, mock_llm = agent_with_mock_llm

        response = await agent.run("Hello, how are you?")

        assert isinstance(response, str)
        assert len(response) > 0
        mock_llm.assert_called()

    @pytest.mark.asyncio
    async def test_run_with_context(self, agent_with_mock_llm):
        """Test run method with additional context."""
        agent, mock_llm = agent_with_mock_llm

        context = {"user_id": "123", "preferences": {"verbose": True}}
        response = await agent.run("Test input", context=context)

        assert isinstance(response, str)
        mock_llm.assert_called()

    @pytest.mark.asyncio
    async def test_run_with_empty_input(self, agent_with_mock_llm):
        """Test run method with empty input."""
        agent, mock_llm = agent_with_mock_llm

        response = await agent.run("")

        # Should handle empty input gracefully
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_run_stream_method(self, agent_with_mock_llm):
        """Test streaming run method."""
        agent, mock_llm = agent_with_mock_llm

        chunks = []
        async for chunk in agent.run_stream("Test streaming"):
            chunks.append(chunk)
            if len(chunks) >= 3:  # Limit for testing
                break

        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

    @pytest.mark.asyncio
    async def test_run_stream_empty_input_error(self, agent_with_mock_llm):
        """Test that streaming with empty input raises error."""
        agent, mock_llm = agent_with_mock_llm

        with pytest.raises(ValueError, match="User input cannot be empty"):
            async for chunk in agent.run_stream(""):
                pass


class TestCoreAgentLLMIntegration:
    """Test LLM integration functionality."""

    @pytest.fixture
    def agent_with_config(self):
        """Agent with LLM config."""
        config = {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "api_key": "test-key"
        }
        return CoreAgent(llm_config=config)

    @pytest.fixture
    def agent_with_function(self):
        """Agent with LLM function."""
        mock_llm = AsyncMock(return_value="Function response")
        return CoreAgent(llm_function=mock_llm), mock_llm

    @pytest.mark.asyncio
    async def test_enhanced_llm_call_with_config(self, agent_with_config):
        """Test enhanced LLM call with config."""
        agent = agent_with_config

        with patch('integrations.litellm_provider.LiteLLMProvider') as mock_provider_class:
            mock_provider = Mock()
            mock_provider.call = AsyncMock(return_value="LiteLLM response")
            mock_provider_class.return_value = mock_provider

            response = await agent._enhanced_llm_call("Test prompt")

            assert response == "LiteLLM response"
            mock_provider.call.assert_called_once_with("Test prompt")

    @pytest.mark.asyncio
    async def test_enhanced_llm_call_with_function(self, agent_with_function):
        """Test enhanced LLM call with function."""
        agent, mock_llm = agent_with_function

        response = await agent._enhanced_llm_call("Test prompt")

        assert response == "Function response"
        mock_llm.assert_called_once_with("Test prompt")

    @pytest.mark.asyncio
    async def test_enhanced_llm_call_error_handling(self, agent_with_function):
        """Test error handling in enhanced LLM call."""
        agent, mock_llm = agent_with_function
        mock_llm.side_effect = Exception("LLM Error")

        response = await agent._enhanced_llm_call("Test prompt")

        assert "I encountered an error" in response
        assert "LLM Error" in response

    @pytest.mark.asyncio
    async def test_call_with_litellm_fallback(self, agent_with_config):
        """Test LiteLLM call with import fallback."""
        agent = agent_with_config

        with patch('integrations.litellm_provider.LiteLLMProvider', side_effect=ImportError):
            response = await agent._call_with_litellm("Test prompt")

            assert "LiteLLM unavailable" in response

    @pytest.mark.asyncio
    async def test_stream_with_litellm_fallback(self, agent_with_config):
        """Test streaming with LiteLLM fallback."""
        agent = agent_with_config

        with patch('integrations.litellm_provider.LiteLLMProvider', side_effect=ImportError):
            chunks = []
            async for chunk in agent._stream_with_litellm("System prompt", "User input"):
                chunks.append(chunk)
                if len(chunks) >= 2:
                    break

            assert len(chunks) > 0
            assert all(isinstance(chunk, str) for chunk in chunks)


class TestCoreAgentMemoryIntegration:
    """Test memory integration functionality."""

    @pytest.fixture
    def agent_with_memory(self):
        """Agent with mocked memory manager."""
        mock_llm = AsyncMock(return_value="Response")
        agent = CoreAgent(llm_function=mock_llm)

        # Mock memory manager
        agent.memory_manager = Mock()
        agent.memory_manager.store_memory = AsyncMock(return_value="mem_123")
        agent.memory_manager.search_memory = AsyncMock(return_value=[])
        agent.memory_manager.get_relevant_context = AsyncMock(return_value={})

        return agent

    @pytest.mark.asyncio
    async def test_add_example_functionality(self, agent_with_memory):
        """Test add_example method."""
        agent = agent_with_memory

        entry_id = await agent.add_example("input example", "output example")

        assert entry_id == "mem_123"
        agent.memory_manager.store_memory.assert_called_once()

        call_args = agent.memory_manager.store_memory.call_args[1]
        assert call_args["content"] == "input example -> output example"
        assert call_args["importance"] == 1.0
        assert call_args["metadata"]["type"] == "example"

    @pytest.mark.asyncio
    async def test_add_example_without_memory_manager(self):
        """Test add_example raises error without memory manager."""
        mock_llm = AsyncMock(return_value="Response")
        agent = CoreAgent(llm_function=mock_llm, enable_memory=False)
        agent.memory_manager = None

        with pytest.raises(ValueError, match="Memory manager not available"):
            await agent.add_example("input", "output")

    @pytest.mark.asyncio
    async def test_get_examples_functionality(self, agent_with_memory):
        """Test get_examples method."""
        agent = agent_with_memory

        # Mock search results
        mock_memories = [
            {"content": "example 1", "metadata": {"type": "example"}},
            {"content": "regular memory", "metadata": {"type": "memory"}},
            {"content": "example 2", "metadata": {"type": "example"}}
        ]
        agent.memory_manager.search_memory.return_value = mock_memories

        examples = await agent.get_examples("test query", limit=5)

        # Should filter only examples
        assert len(examples) == 2
        assert all(ex["metadata"]["type"] == "example" for ex in examples)

    @pytest.mark.asyncio
    async def test_get_examples_without_memory_manager(self):
        """Test get_examples returns empty list without memory manager."""
        mock_llm = AsyncMock(return_value="Response")
        agent = CoreAgent(llm_function=mock_llm, enable_memory=False)
        agent.memory_manager = None

        examples = await agent.get_examples()

        assert examples == []

    @pytest.mark.asyncio
    async def test_build_enhanced_prompt_with_examples(self, agent_with_memory):
        """Test prompt building includes examples."""
        agent = agent_with_memory

        # Mock example memories
        example_memories = [
            {"content": "Q: What is 2+2? A: 4", "metadata": {"type": "example"}}
        ]
        agent.memory_manager.search_memory.return_value = example_memories
        agent.memory_manager.get_relevant_context.return_value = {}

        # Mock tool manager
        agent.tool_manager = Mock()
        agent.tool_manager.list_available_tools.return_value = []

        # Mock executor
        agent.executor = Mock()
        agent.executor.get_react_system_prompt.return_value = "ReAct instructions"

        prompt = await agent._build_enhanced_prompt("What is 3+3?")

        assert "Examples:" in prompt
        assert "Q: What is 2+2? A: 4" in prompt


class TestCoreAgentPatternExecution:
    """Test execution pattern functionality."""

    @pytest.fixture
    def agent_with_patterns(self):
        """Agent with mocked pattern executor."""
        mock_llm = AsyncMock(return_value="Response")
        agent = CoreAgent(llm_function=mock_llm)

        # Mock pattern executor
        agent.pattern_executor = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.final_answer = "Pattern response"
        mock_result.to_dict.return_value = {"success": True}
        agent.pattern_executor.execute.return_value = mock_result

        return agent

    @pytest.mark.asyncio
    async def test_set_execution_pattern(self, agent_with_patterns):
        """Test setting execution pattern."""
        agent = agent_with_patterns

        await agent.set_execution_pattern(ExecutionPatternType.SIMPLE)

        assert agent.current_pattern == ExecutionPatternType.SIMPLE
        assert agent.execution_pattern == ExecutionPatternType.SIMPLE

    def test_execution_pattern_initialization(self):
        """Test execution pattern is set during initialization."""
        mock_llm = AsyncMock(return_value="Response")
        agent = CoreAgent(
            llm_function=mock_llm,
            execution_pattern=ExecutionPatternType.PLANNING
        )

        assert agent.execution_pattern == ExecutionPatternType.PLANNING
        assert agent.current_pattern == ExecutionPatternType.PLANNING


class TestCoreAgentBenchmarking:
    """Test benchmarking functionality."""

    @pytest.fixture
    def agent_for_benchmark(self):
        """Agent set up for benchmarking tests."""
        mock_llm = AsyncMock(return_value="Benchmark response")
        agent = CoreAgent(llm_function=mock_llm)

        # Mock the run method to be faster for testing
        agent.run = AsyncMock(return_value="Test response")

        return agent

    @pytest.mark.asyncio
    async def test_run_benchmark_basic(self, agent_for_benchmark):
        """Test basic benchmark functionality."""
        agent = agent_for_benchmark

        test_cases = ["Test 1", "Test 2", "Test 3"]
        result = await agent.run_benchmark(test_cases)

        assert result["framework"] == "mini_agent"
        assert len(result["results"]) == 3

        for i, test_result in enumerate(result["results"]):
            assert test_result["input"] == test_cases[i]
            assert test_result["response"] == "Test response"
            assert isinstance(test_result["time"], float)
            assert test_result["time"] >= 0

    @pytest.mark.asyncio
    async def test_run_benchmark_empty_test_cases(self, agent_for_benchmark):
        """Test benchmark with empty test cases raises error."""
        agent = agent_for_benchmark

        with pytest.raises(ValueError, match="test_cases cannot be empty"):
            await agent.run_benchmark([])

    @pytest.mark.asyncio
    async def test_run_benchmark_with_errors(self, agent_for_benchmark):
        """Test benchmark handles errors gracefully."""
        agent = agent_for_benchmark

        # Make run method raise error for second test
        call_count = 0
        async def mock_run_with_error(input_text):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Test error")
            return "Success response"

        agent.run = mock_run_with_error

        test_cases = ["Test 1", "Test 2", "Test 3"]
        result = await agent.run_benchmark(test_cases)

        assert len(result["results"]) == 3
        assert result["results"][0]["response"] == "Success response"
        assert "Error:" in result["results"][1]["response"]
        assert result["results"][2]["response"] == "Success response"


class TestCoreAgentToolIntegration:
    """Test tool integration functionality."""

    @pytest.fixture
    def agent_with_tools(self):
        """Agent with mocked tool manager."""
        mock_llm = AsyncMock(return_value="Response")
        agent = CoreAgent(llm_function=mock_llm)

        # Mock tool manager
        agent.tool_manager = Mock()
        agent.tool_manager.register_tool = AsyncMock(return_value=True)
        agent.tool_manager.connect_mcp_server = AsyncMock(return_value=True)

        return agent

    @pytest.mark.asyncio
    async def test_add_tool_functionality(self, agent_with_tools):
        """Test add_tool method."""
        agent = agent_with_tools

        mock_tool = Mock()
        mock_tool.name = "test_tool"

        result = await agent.add_tool(mock_tool, aliases=["alias1"])

        assert result is True
        agent.tool_manager.register_tool.assert_called_once_with(mock_tool, ["alias1"])

    @pytest.mark.asyncio
    async def test_connect_mcp_server_functionality(self, agent_with_tools):
        """Test connect_mcp_server method."""
        agent = agent_with_tools

        server_config = {"url": "http://test-server", "name": "test"}
        result = await agent.connect_mcp_server("test_server", server_config)

        assert result is True
        agent.tool_manager.connect_mcp_server.assert_called_once_with("test_server", server_config)


class TestCoreAgentErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_run_with_llm_error(self):
        """Test run method when LLM call fails."""
        mock_llm = AsyncMock(side_effect=Exception("LLM connection error"))
        agent = CoreAgent(llm_function=mock_llm)

        response = await agent.run("Test input")

        assert "I encountered an error" in response
        assert "LLM connection error" in response

    @pytest.mark.asyncio
    async def test_run_with_none_response(self):
        """Test run method when LLM returns None."""
        mock_llm = AsyncMock(return_value=None)
        agent = CoreAgent(llm_function=mock_llm)

        response = await agent.run("Test input")

        assert "I don't have a response to that" in response

    @pytest.mark.asyncio
    async def test_run_with_empty_response(self):
        """Test run method when LLM returns empty string."""
        mock_llm = AsyncMock(return_value="")
        agent = CoreAgent(llm_function=mock_llm)

        response = await agent.run("Test input")

        assert "I don't have a response to that" in response


class TestCoreAgentLifecycle:
    """Test agent lifecycle management."""

    @pytest.fixture
    def agent_for_lifecycle(self):
        """Agent for lifecycle testing."""
        mock_llm = AsyncMock(return_value="Response")
        return CoreAgent(llm_function=mock_llm)

    @pytest.mark.asyncio
    async def test_agent_start_stop(self, agent_for_lifecycle):
        """Test agent start and stop methods."""
        agent = agent_for_lifecycle

        # Mock memory manager start/stop
        agent.memory_manager.start = AsyncMock()
        agent.memory_manager.stop = AsyncMock()

        await agent.start()
        await agent.stop()

        agent.memory_manager.start.assert_called_once()
        agent.memory_manager.stop.assert_called_once()

    def test_agent_session_id_generation(self):
        """Test session ID generation."""
        mock_llm = AsyncMock(return_value="Response")

        agent1 = CoreAgent(llm_function=mock_llm)
        agent2 = CoreAgent(llm_function=mock_llm)

        assert agent1.session_id != agent2.session_id
        assert len(agent1.session_id) > 0
        assert len(agent2.session_id) > 0

    def test_agent_clone_functionality(self, agent_for_lifecycle):
        """Test agent cloning with new session."""
        agent = agent_for_lifecycle
        original_session = agent.session_id

        cloned_agent = agent.clone()

        assert cloned_agent.session_id != original_session
        assert cloned_agent.llm_function == agent.llm_function
        assert cloned_agent.system_prompt == agent.system_prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])