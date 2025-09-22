"""Unit tests for pattern executor classes."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List, Optional
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    # Use test-compatible versions
    from execution.test_pattern_executor import PatternExecutor
    from execution.test_execution_context import ExecutionContext
    from execution.execution_patterns import ExecutionPatternType as ExecutionPattern
    from memory.memory_manager import CoreMemoryManager
    from tools.tool_manager import ToolManager
except ImportError as e:
    pytest.skip(f"Execution imports not available: {e}", allow_module_level=True)


class TestExecutionContext:
    """Test the ExecutionContext class."""

    def test_init_basic(self):
        """Test basic context initialization."""
        context = ExecutionContext(
            messages=[{"role": "user", "content": "Hello"}],
            tools=[]
        )

        assert len(context.messages) == 1
        assert context.messages[0]["content"] == "Hello"
        assert context.tools == []
        assert context.metadata == {}
        assert context.max_iterations == 10
        assert context.current_iteration == 0

    def test_init_with_metadata(self):
        """Test context initialization with metadata."""
        metadata = {"session_id": "123", "user_id": "456"}
        context = ExecutionContext(
            messages=[],
            tools=[],
            metadata=metadata,
            max_iterations=5
        )

        assert context.metadata == metadata
        assert context.max_iterations == 5

    def test_add_message(self):
        """Test adding messages to context."""
        context = ExecutionContext(messages=[], tools=[])

        context.add_message("user", "First message")
        context.add_message("assistant", "Response")

        assert len(context.messages) == 2
        assert context.messages[0]["role"] == "user"
        assert context.messages[0]["content"] == "First message"
        assert context.messages[1]["role"] == "assistant"
        assert context.messages[1]["content"] == "Response"

    def test_increment_iteration(self):
        """Test iteration incrementing."""
        context = ExecutionContext(messages=[], tools=[])

        assert context.current_iteration == 0
        context.increment_iteration()
        assert context.current_iteration == 1

    def test_is_max_iterations_reached(self):
        """Test max iterations check."""
        context = ExecutionContext(
            messages=[],
            tools=[],
            max_iterations=2
        )

        assert not context.is_max_iterations_reached()

        context.increment_iteration()
        assert not context.is_max_iterations_reached()

        context.increment_iteration()
        assert context.is_max_iterations_reached()

    def test_get_latest_message(self):
        """Test getting latest message."""
        context = ExecutionContext(messages=[], tools=[])

        # No messages
        assert context.get_latest_message() is None

        # Add messages
        context.add_message("user", "Hello")
        latest = context.get_latest_message()
        assert latest["role"] == "user"
        assert latest["content"] == "Hello"

        context.add_message("assistant", "Hi")
        latest = context.get_latest_message()
        assert latest["role"] == "assistant"
        assert latest["content"] == "Hi"

    def test_get_messages_by_role(self):
        """Test getting messages by role."""
        context = ExecutionContext(messages=[], tools=[])

        context.add_message("user", "Message 1")
        context.add_message("assistant", "Response 1")
        context.add_message("user", "Message 2")

        user_messages = context.get_messages_by_role("user")
        assert len(user_messages) == 2
        assert user_messages[0]["content"] == "Message 1"
        assert user_messages[1]["content"] == "Message 2"

        assistant_messages = context.get_messages_by_role("assistant")
        assert len(assistant_messages) == 1
        assert assistant_messages[0]["content"] == "Response 1"

    def test_to_dict(self):
        """Test context serialization."""
        context = ExecutionContext(
            messages=[{"role": "user", "content": "Test"}],
            tools=["tool1"],
            metadata={"key": "value"},
            max_iterations=5
        )
        context.increment_iteration()

        data = context.to_dict()

        assert data["messages"] == [{"role": "user", "content": "Test"}]
        assert data["tools"] == ["tool1"]
        assert data["metadata"] == {"key": "value"}
        assert data["max_iterations"] == 5
        assert data["current_iteration"] == 1

    def test_from_dict(self):
        """Test context deserialization."""
        data = {
            "messages": [{"role": "user", "content": "Test"}],
            "tools": ["tool1"],
            "metadata": {"key": "value"},
            "max_iterations": 8,
            "current_iteration": 3
        }

        context = ExecutionContext.from_dict(data)

        assert len(context.messages) == 1
        assert context.messages[0]["content"] == "Test"
        assert context.tools == ["tool1"]
        assert context.metadata == {"key": "value"}
        assert context.max_iterations == 8
        assert context.current_iteration == 3


class TestPatternExecutor:
    """Test the PatternExecutor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_memory = Mock(spec=CoreMemoryManager)
        self.mock_tools = Mock(spec=ToolManager)
        self.mock_llm_function = AsyncMock()

        self.executor = PatternExecutor(
            memory_manager=self.mock_memory,
            tool_manager=self.mock_tools,
            llm_function=self.mock_llm_function
        )

    def test_init(self):
        """Test executor initialization."""
        assert self.executor.memory_manager == self.mock_memory
        assert self.executor.tool_manager == self.mock_tools
        assert self.executor.llm_function == self.mock_llm_function
        assert self.executor.execution_stats == {}

    @pytest.mark.asyncio
    async def test_execute_simple_pattern(self):
        """Test executing SIMPLE pattern."""
        # Setup
        self.mock_llm_function.return_value = "Simple response"

        context = ExecutionContext(
            messages=[{"role": "user", "content": "Hello"}],
            tools=[]
        )

        # Execute
        result = await self.executor.execute_pattern(
            pattern=ExecutionPattern.SIMPLE,
            context=context
        )

        # Verify
        assert result["success"] is True
        assert result["response"] == "Simple response"
        assert "execution_time" in result
        self.mock_llm_function.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_simple_pattern_with_memory(self):
        """Test SIMPLE pattern with memory operations."""
        # Setup
        self.mock_llm_function.return_value = "Response with memory"
        self.mock_memory.add_memory = AsyncMock()
        self.mock_memory.get_relevant_memories = AsyncMock(return_value=[])

        context = ExecutionContext(
            messages=[{"role": "user", "content": "Remember this"}],
            tools=[]
        )

        # Execute
        result = await self.executor.execute_pattern(
            pattern=ExecutionPattern.SIMPLE,
            context=context,
            use_memory=True
        )

        # Verify
        assert result["success"] is True
        self.mock_memory.get_relevant_memories.assert_called()
        self.mock_memory.add_memory.assert_called()

    @pytest.mark.asyncio
    async def test_execute_react_pattern(self):
        """Test executing REACT pattern."""
        # Setup
        self.mock_llm_function.side_effect = [
            "I need to use a tool.",
            "Final answer based on tool result."
        ]
        self.mock_tools.execute_tool_by_name = AsyncMock(
            return_value=Mock(success=True, content="Tool result")
        )

        context = ExecutionContext(
            messages=[{"role": "user", "content": "Use a tool"}],
            tools=["test_tool"]
        )

        # Execute
        result = await self.executor.execute_pattern(
            pattern=ExecutionPattern.REACT,
            context=context
        )

        # Verify
        assert result["success"] is True
        assert "execution_time" in result
        assert self.mock_llm_function.call_count >= 1

    @pytest.mark.asyncio
    async def test_execute_planning_pattern(self):
        """Test executing PLANNING pattern."""
        # Setup
        self.mock_llm_function.side_effect = [
            "Plan: Step 1, Step 2, Step 3",
            "Executing step 1",
            "Executing step 2",
            "Final result"
        ]

        context = ExecutionContext(
            messages=[{"role": "user", "content": "Complex task"}],
            tools=[]
        )

        # Execute
        result = await self.executor.execute_pattern(
            pattern=ExecutionPattern.PLANNING,
            context=context
        )

        # Verify
        assert result["success"] is True
        assert "plan" in result
        assert "execution_time" in result

    @pytest.mark.asyncio
    async def test_execute_auto_pattern(self):
        """Test executing AUTO pattern (should select best pattern)."""
        # Setup
        self.mock_llm_function.return_value = "Auto-selected response"

        context = ExecutionContext(
            messages=[{"role": "user", "content": "Simple question"}],
            tools=[]
        )

        # Execute
        result = await self.executor.execute_pattern(
            pattern=ExecutionPattern.AUTO,
            context=context
        )

        # Verify
        assert result["success"] is True
        assert "selected_pattern" in result
        assert "execution_time" in result

    @pytest.mark.asyncio
    async def test_execute_pattern_error_handling(self):
        """Test error handling during pattern execution."""
        # Setup
        self.mock_llm_function.side_effect = Exception("LLM Error")

        context = ExecutionContext(
            messages=[{"role": "user", "content": "Test"}],
            tools=[]
        )

        # Execute
        result = await self.executor.execute_pattern(
            pattern=ExecutionPattern.SIMPLE,
            context=context
        )

        # Verify
        assert result["success"] is False
        assert "error" in result
        assert "LLM Error" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_simple_implementation(self):
        """Test the _execute_simple method directly."""
        # Setup
        self.mock_llm_function.return_value = "Simple execution result"

        context = ExecutionContext(
            messages=[{"role": "user", "content": "Test"}],
            tools=[]
        )

        # Execute
        result = await self.executor._execute_simple(context)

        # Verify
        assert result == "Simple execution result"
        self.mock_llm_function.assert_called_once()

        # Check that context messages were used
        call_args = self.mock_llm_function.call_args
        messages = call_args[0][0] if call_args[0] else call_args[1].get('messages', [])
        assert len(messages) >= 1

    @pytest.mark.asyncio
    async def test_execute_react_implementation(self):
        """Test the _execute_react method directly."""
        # Setup - simulate tool use scenario
        self.mock_llm_function.side_effect = [
            "Action: use_tool\nTool: test_tool\nInput: test_input",
            "Final Answer: Tool result processed"
        ]

        mock_tool_result = Mock()
        mock_tool_result.success = True
        mock_tool_result.content = "Tool executed successfully"

        self.mock_tools.execute_tool_by_name = AsyncMock(return_value=mock_tool_result)

        context = ExecutionContext(
            messages=[{"role": "user", "content": "Use a tool"}],
            tools=["test_tool"]
        )

        # Execute
        result = await self.executor._execute_react(context)

        # Verify
        assert "Tool result processed" in result
        self.mock_tools.execute_tool_by_name.assert_called()

    @pytest.mark.asyncio
    async def test_execute_planning_implementation(self):
        """Test the _execute_planning method directly."""
        # Setup
        self.mock_llm_function.side_effect = [
            "Plan:\n1. Analyze the problem\n2. Generate solution\n3. Verify result",
            "Step 1 completed: Analysis done",
            "Step 2 completed: Solution generated",
            "Step 3 completed: Verification passed. Final result ready."
        ]

        context = ExecutionContext(
            messages=[{"role": "user", "content": "Complex planning task"}],
            tools=[]
        )

        # Execute
        result = await self.executor._execute_planning(context)

        # Verify
        assert "Final result ready" in result
        assert self.mock_llm_function.call_count >= 2

    def test_select_pattern_for_auto(self):
        """Test automatic pattern selection."""
        # Simple question - should select SIMPLE
        context1 = ExecutionContext(
            messages=[{"role": "user", "content": "What is 2+2?"}],
            tools=[]
        )
        pattern1 = self.executor._select_pattern_for_auto(context1)
        assert pattern1 == ExecutionPattern.SIMPLE

        # Complex task - should select PLANNING
        context2 = ExecutionContext(
            messages=[{"role": "user", "content": "Plan a multi-step project with dependencies"}],
            tools=[]
        )
        pattern2 = self.executor._select_pattern_for_auto(context2)
        assert pattern2 == ExecutionPattern.PLANNING

        # Tool usage scenario - should select REACT
        context3 = ExecutionContext(
            messages=[{"role": "user", "content": "Search for information"}],
            tools=["search_tool", "web_tool"]
        )
        pattern3 = self.executor._select_pattern_for_auto(context3)
        assert pattern3 == ExecutionPattern.REACT

    def test_build_prompt_simple(self):
        """Test building prompt for SIMPLE pattern."""
        context = ExecutionContext(
            messages=[{"role": "user", "content": "Hello"}],
            tools=[]
        )

        prompt = self.executor._build_prompt(context, ExecutionPattern.SIMPLE)

        assert len(prompt) >= 1
        assert prompt[-1]["role"] == "user"
        assert prompt[-1]["content"] == "Hello"

    def test_build_prompt_react(self):
        """Test building prompt for REACT pattern."""
        context = ExecutionContext(
            messages=[{"role": "user", "content": "Use tools"}],
            tools=["tool1", "tool2"]
        )

        prompt = self.executor._build_prompt(context, ExecutionPattern.REACT)

        # Should include system message with REACT instructions
        assert len(prompt) >= 2
        assert any("Action:" in msg.get("content", "") for msg in prompt)

    def test_build_prompt_planning(self):
        """Test building prompt for PLANNING pattern."""
        context = ExecutionContext(
            messages=[{"role": "user", "content": "Complex task"}],
            tools=[]
        )

        prompt = self.executor._build_prompt(context, ExecutionPattern.PLANNING)

        # Should include system message with planning instructions
        assert len(prompt) >= 2
        assert any("plan" in msg.get("content", "").lower() for msg in prompt)

    def test_get_execution_stats(self):
        """Test getting execution statistics."""
        # Initially empty
        stats = self.executor.get_execution_stats()
        assert stats == {}

        # Add some mock stats
        self.executor.execution_stats = {
            "total_executions": 5,
            "successful_executions": 4,
            "pattern_usage": {
                "SIMPLE": 3,
                "REACT": 1,
                "PLANNING": 1
            }
        }

        stats = self.executor.get_execution_stats()
        assert stats["total_executions"] == 5
        assert stats["successful_executions"] == 4
        assert stats["pattern_usage"]["SIMPLE"] == 3

    def test_reset_stats(self):
        """Test resetting execution statistics."""
        # Add some stats
        self.executor.execution_stats = {"total": 10}

        # Reset
        self.executor.reset_stats()

        # Should be empty
        assert self.executor.execution_stats == {}


class TestPatternExecutorIntegration:
    """Integration tests for PatternExecutor."""

    def setup_method(self):
        """Set up integration test fixtures."""
        self.mock_memory = Mock(spec=CoreMemoryManager)
        self.mock_tools = Mock(spec=ToolManager)
        self.mock_llm = AsyncMock()

        self.executor = PatternExecutor(
            memory_manager=self.mock_memory,
            tool_manager=self.mock_tools,
            llm_function=self.mock_llm
        )

    @pytest.mark.asyncio
    async def test_full_execution_workflow(self):
        """Test complete execution workflow."""
        # Setup
        self.mock_llm.return_value = "Workflow completed"
        self.mock_memory.get_relevant_memories = AsyncMock(return_value=[])
        self.mock_memory.add_memory = AsyncMock()

        context = ExecutionContext(
            messages=[{"role": "user", "content": "Execute workflow"}],
            tools=[],
            metadata={"session_id": "test-123"}
        )

        # Execute
        result = await self.executor.execute_pattern(
            pattern=ExecutionPattern.SIMPLE,
            context=context,
            use_memory=True
        )

        # Verify complete workflow
        assert result["success"] is True
        assert result["response"] == "Workflow completed"
        assert "execution_time" in result

        # Memory operations called
        self.mock_memory.get_relevant_memories.assert_called()
        self.mock_memory.add_memory.assert_called()

    @pytest.mark.asyncio
    async def test_pattern_switching_workflow(self):
        """Test workflow with pattern switching."""
        # Test AUTO pattern selection
        self.mock_llm.return_value = "Auto-selected result"

        # Simple context should select SIMPLE pattern
        simple_context = ExecutionContext(
            messages=[{"role": "user", "content": "What's 1+1?"}],
            tools=[]
        )

        result = await self.executor.execute_pattern(
            pattern=ExecutionPattern.AUTO,
            context=simple_context
        )

        assert result["success"] is True
        assert result["selected_pattern"] == ExecutionPattern.SIMPLE.value

        # Complex context should select PLANNING pattern
        complex_context = ExecutionContext(
            messages=[{"role": "user", "content": "Create a detailed multi-phase project plan"}],
            tools=[]
        )

        result = await self.executor.execute_pattern(
            pattern=ExecutionPattern.AUTO,
            context=complex_context
        )

        assert result["success"] is True
        assert result["selected_pattern"] == ExecutionPattern.PLANNING.value


class TestPatternExecutorEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up edge case test fixtures."""
        self.mock_memory = Mock()
        self.mock_tools = Mock()
        self.mock_llm = AsyncMock()

        self.executor = PatternExecutor(
            memory_manager=self.mock_memory,
            tool_manager=self.mock_tools,
            llm_function=self.mock_llm
        )

    @pytest.mark.asyncio
    async def test_empty_context(self):
        """Test handling of empty context."""
        context = ExecutionContext(messages=[], tools=[])

        # Should handle gracefully
        result = await self.executor.execute_pattern(
            pattern=ExecutionPattern.SIMPLE,
            context=context
        )

        # Should still attempt execution
        assert "success" in result

    @pytest.mark.asyncio
    async def test_max_iterations_reached(self):
        """Test handling when max iterations are reached."""
        # Setup context with low max iterations
        context = ExecutionContext(
            messages=[{"role": "user", "content": "Test"}],
            tools=[],
            max_iterations=1
        )

        # Force iteration increment
        context.increment_iteration()

        # Should handle max iterations
        result = await self.executor.execute_pattern(
            pattern=ExecutionPattern.REACT,
            context=context
        )

        # Should complete despite max iterations
        assert "success" in result

    @pytest.mark.asyncio
    async def test_invalid_pattern(self):
        """Test handling of invalid execution pattern."""
        context = ExecutionContext(messages=[], tools=[])

        # Test with invalid pattern (using string instead of enum)
        with pytest.raises((ValueError, AttributeError)):
            await self.executor.execute_pattern(
                pattern="INVALID_PATTERN",
                context=context
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])