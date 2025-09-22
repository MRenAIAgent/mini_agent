"""Integration tests for complete agent workflows."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List, Optional
import pytest
import tempfile
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from agent import CoreAgent
    from memory.memory_manager import CoreMemoryManager
    from memory.backends.in_memory_backend import InMemoryBackend
    from tools.tool_manager import ToolManager
    from integrations.llm_interfaces import LLMConfig, LLMMessage, LLMResponse
    from execution.execution_patterns import ExecutionPattern
except ImportError as e:
    pytest.skip(f"Integration imports not available: {e}", allow_module_level=True)


class TestAgentWorkflowIntegration:
    """Test complete agent workflows with real components."""

    def setup_method(self):
        """Set up integration test fixtures."""
        # Create real memory manager with in-memory backend
        self.memory_manager = CoreMemoryManager()
        self.memory_backend = InMemoryBackend()
        asyncio.run(self.memory_manager.set_backend("in_memory", self.memory_backend))

        # Create real tool manager
        self.tool_manager = ToolManager()

        # Mock LLM function for controlled responses
        self.mock_llm_function = AsyncMock()

        # Create agent with real components
        self.agent = CoreAgent(
            llm_function=self.mock_llm_function,
            memory_manager=self.memory_manager,
            tool_manager=self.tool_manager
        )

    @pytest.mark.asyncio
    async def test_simple_conversation_workflow(self):
        """Test a simple conversation workflow."""
        # Setup LLM response
        self.mock_llm_function.return_value = "Hello! I'm here to help you."

        # Run conversation
        response = await self.agent.run(
            "Hello, can you help me?",
            pattern=ExecutionPattern.SIMPLE
        )

        # Verify response
        assert response == "Hello! I'm here to help you."

        # Verify memory was stored
        memories = await self.memory_manager.get_all_memories()
        assert len(memories) >= 1

        # Verify LLM was called with proper messages
        self.mock_llm_function.assert_called_once()
        call_args = self.mock_llm_function.call_args[0][0]
        assert len(call_args) >= 1
        assert call_args[-1]["content"] == "Hello, can you help me?"

    @pytest.mark.asyncio
    async def test_conversation_with_memory_context(self):
        """Test conversation that uses memory context."""
        # First conversation
        self.mock_llm_function.return_value = "Nice to meet you, John!"
        await self.agent.run("My name is John", pattern=ExecutionPattern.SIMPLE)

        # Second conversation - should have context
        self.mock_llm_function.return_value = "Hello again, John! How can I help?"
        response = await self.agent.run(
            "What's my name?",
            pattern=ExecutionPattern.SIMPLE
        )

        # Verify context was included
        assert self.mock_llm_function.call_count == 2

        # Check that the second call included memory context
        second_call_args = self.mock_llm_function.call_args[0][0]

        # Should have more than just the current message
        assert len(second_call_args) > 1

    @pytest.mark.asyncio
    async def test_tool_usage_workflow(self):
        """Test workflow that uses tools."""
        # Register a test tool
        class TestTool:
            def get_definition(self):
                return Mock(
                    name="calculator",
                    description="Performs calculations",
                    parameters={"type": "object", "properties": {}}
                )

            async def execute(self, tool_call):
                from tools.tool_interfaces import ToolResult
                return ToolResult(
                    call_id=tool_call.id,
                    success=True,
                    content="The result is 42",
                    execution_time=0.1
                )

        test_tool = TestTool()
        await self.tool_manager.register_tool(test_tool)

        # Setup LLM responses for REACT pattern
        self.mock_llm_function.side_effect = [
            "I need to use the calculator tool to solve this.",
            "Based on the calculation, the answer is 42."
        ]

        # Mock tool execution
        with patch.object(self.tool_manager, 'execute_tool_by_name') as mock_execute:
            mock_result = Mock()
            mock_result.success = True
            mock_result.content = "The result is 42"
            mock_execute.return_value = mock_result

            # Run with tool usage
            response = await self.agent.run(
                "What is 6 times 7?",
                pattern=ExecutionPattern.REACT
            )

            # Verify tool was used
            mock_execute.assert_called()

    @pytest.mark.asyncio
    async def test_streaming_workflow(self):
        """Test streaming response workflow."""
        # Setup streaming response
        async def mock_stream():
            yield "Hello "
            yield "there! "
            yield "How "
            yield "can "
            yield "I "
            yield "help?"

        self.mock_llm_function.return_value = mock_stream()

        # Collect streaming response
        chunks = []
        async for chunk in self.agent.run_stream("Hello"):
            chunks.append(chunk)

        # Verify streaming
        assert len(chunks) == 6
        full_response = "".join(chunks)
        assert full_response == "Hello there! How can I help?"

    @pytest.mark.asyncio
    async def test_planning_workflow(self):
        """Test planning execution pattern workflow."""
        # Setup planning responses
        self.mock_llm_function.side_effect = [
            "Plan:\n1. Analyze the request\n2. Research the topic\n3. Provide a comprehensive answer",
            "Step 1: Analyzing your request about Python programming...",
            "Step 2: Researching best practices and examples...",
            "Step 3: Here's a comprehensive guide to Python programming..."
        ]

        # Run planning workflow
        response = await self.agent.run(
            "Teach me Python programming",
            pattern=ExecutionPattern.PLANNING
        )

        # Verify planning pattern was used
        assert "comprehensive guide" in response
        assert self.mock_llm_function.call_count >= 2

    @pytest.mark.asyncio
    async def test_auto_pattern_selection_workflow(self):
        """Test automatic pattern selection workflow."""
        self.mock_llm_function.return_value = "Simple answer to your question."

        # Simple question should use SIMPLE pattern
        response = await self.agent.run(
            "What is 2+2?",
            pattern=ExecutionPattern.AUTO
        )

        assert response == "Simple answer to your question."

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """Test error recovery in workflows."""
        # Setup LLM to fail first, then succeed
        self.mock_llm_function.side_effect = [
            Exception("LLM temporarily unavailable"),
            "Recovery successful! Here's your answer."
        ]

        # First call should fail
        with pytest.raises(Exception):
            await self.agent.run("Test message")

        # Reset mock for retry
        self.mock_llm_function.side_effect = None
        self.mock_llm_function.return_value = "Recovery successful!"

        # Second call should succeed
        response = await self.agent.run("Test message")
        assert response == "Recovery successful!"

    @pytest.mark.asyncio
    async def test_memory_persistence_workflow(self):
        """Test memory persistence across agent interactions."""
        # Store some initial memories
        await self.agent.run("I love pizza", pattern=ExecutionPattern.SIMPLE)
        await self.agent.run("My favorite color is blue", pattern=ExecutionPattern.SIMPLE)

        # Query memory
        memories = await self.memory_manager.get_all_memories()
        initial_count = len(memories)

        # Add more memories
        await self.agent.run("I work as a developer", pattern=ExecutionPattern.SIMPLE)

        # Verify memory count increased
        updated_memories = await self.memory_manager.get_all_memories()
        assert len(updated_memories) > initial_count

        # Search for specific memory
        pizza_memories = await self.memory_manager.search_memories("pizza")
        assert len(pizza_memories) > 0
        assert any("pizza" in m.content.lower() for m in pizza_memories)

    @pytest.mark.asyncio
    async def test_benchmark_workflow(self):
        """Test benchmarking workflow."""
        # Setup test scenarios
        test_scenarios = [
            {"input": "Hello", "expected_pattern": "greeting"},
            {"input": "What is 2+2?", "expected_pattern": "simple_math"},
            {"input": "Explain quantum physics", "expected_pattern": "complex_explanation"}
        ]

        self.mock_llm_function.return_value = "Benchmark response"

        # Run benchmark
        results = await self.agent.run_benchmark(test_scenarios)

        # Verify benchmark results
        assert "total_scenarios" in results
        assert "successful_runs" in results
        assert "average_response_time" in results
        assert results["total_scenarios"] == 3

    @pytest.mark.asyncio
    async def test_multi_turn_conversation_workflow(self):
        """Test multi-turn conversation workflow."""
        # Setup conversation responses
        responses = [
            "Hello! I'm Claude, an AI assistant.",
            "I can help with many tasks including answering questions, writing, and analysis.",
            "Python is a versatile programming language known for its simplicity.",
            "You can start with basic syntax, variables, and functions."
        ]

        self.mock_llm_function.side_effect = responses

        # Multi-turn conversation
        conversation = [
            "Hi, who are you?",
            "What can you help me with?",
            "Tell me about Python",
            "How should I start learning it?"
        ]

        responses_received = []
        for message in conversation:
            response = await self.agent.run(message, pattern=ExecutionPattern.SIMPLE)
            responses_received.append(response)

        # Verify all responses
        assert len(responses_received) == 4
        assert all(isinstance(r, str) for r in responses_received)

        # Verify memory accumulated conversation history
        memories = await self.memory_manager.get_all_memories()
        assert len(memories) >= 4  # At least one memory per turn


class TestAgentToolIntegration:
    """Test agent integration with tools."""

    def setup_method(self):
        """Set up tool integration tests."""
        self.memory_manager = CoreMemoryManager()
        self.memory_backend = InMemoryBackend()
        asyncio.run(self.memory_manager.set_backend("in_memory", self.memory_backend))

        self.tool_manager = ToolManager()
        self.mock_llm_function = AsyncMock()

        self.agent = CoreAgent(
            llm_function=self.mock_llm_function,
            memory_manager=self.memory_manager,
            tool_manager=self.tool_manager
        )

    @pytest.mark.asyncio
    async def test_calculator_tool_integration(self):
        """Test integration with a calculator tool."""
        # Register calculator tool
        class CalculatorTool:
            def get_definition(self):
                return Mock(
                    name="calculator",
                    description="Performs mathematical calculations",
                    parameters={
                        "type": "object",
                        "properties": {
                            "expression": {"type": "string", "description": "Math expression"}
                        }
                    }
                )

            async def execute(self, tool_call):
                from tools.tool_interfaces import ToolResult
                # Simple eval for test purposes
                try:
                    result = eval(tool_call.arguments.get("expression", "0"))
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

        calculator = CalculatorTool()
        await self.tool_manager.register_tool(calculator)

        # Test calculation workflow
        self.mock_llm_function.return_value = "The result of 15 + 27 is 42."

        with patch.object(self.tool_manager, 'execute_tool_by_name') as mock_execute:
            mock_result = Mock()
            mock_result.success = True
            mock_result.content = "42"
            mock_execute.return_value = mock_result

            response = await self.agent.run(
                "Calculate 15 + 27",
                pattern=ExecutionPattern.REACT
            )

            assert "42" in response

    @pytest.mark.asyncio
    async def test_file_tool_integration(self):
        """Test integration with file operations tool."""
        # Register file tool
        class FileTool:
            def get_definition(self):
                return Mock(
                    name="file_operations",
                    description="Read and write files",
                    parameters={
                        "type": "object",
                        "properties": {
                            "operation": {"type": "string"},
                            "filename": {"type": "string"},
                            "content": {"type": "string"}
                        }
                    }
                )

            async def execute(self, tool_call):
                from tools.tool_interfaces import ToolResult
                return ToolResult(
                    call_id=tool_call.id,
                    success=True,
                    content="File operation completed successfully",
                    execution_time=0.2
                )

        file_tool = FileTool()
        await self.tool_manager.register_tool(file_tool)

        # Test file workflow
        self.mock_llm_function.return_value = "File has been created successfully."

        response = await self.agent.run(
            "Create a file called test.txt with content 'Hello World'",
            pattern=ExecutionPattern.REACT
        )

        assert "File" in response


class TestAgentMemoryIntegration:
    """Test agent integration with different memory backends."""

    def setup_method(self):
        """Set up memory integration tests."""
        self.tool_manager = ToolManager()
        self.mock_llm_function = AsyncMock()

    @pytest.mark.asyncio
    async def test_in_memory_backend_integration(self):
        """Test agent with in-memory backend."""
        memory_manager = CoreMemoryManager()
        backend = InMemoryBackend()
        await memory_manager.set_backend("in_memory", backend)

        agent = CoreAgent(
            llm_function=self.mock_llm_function,
            memory_manager=memory_manager,
            tool_manager=self.tool_manager
        )

        self.mock_llm_function.return_value = "Information stored in memory."

        # Test memory operations
        await agent.run("Remember that I like coffee", pattern=ExecutionPattern.SIMPLE)

        # Verify memory was stored
        memories = await memory_manager.get_all_memories()
        assert len(memories) > 0

        # Search memory
        coffee_memories = await memory_manager.search_memories("coffee")
        assert len(coffee_memories) > 0

    @pytest.mark.asyncio
    async def test_memory_backend_switching(self):
        """Test switching memory backends during operation."""
        memory_manager = CoreMemoryManager()

        # Start with in-memory backend
        in_memory_backend = InMemoryBackend()
        await memory_manager.set_backend("in_memory", in_memory_backend)

        agent = CoreAgent(
            llm_function=self.mock_llm_function,
            memory_manager=memory_manager,
            tool_manager=self.tool_manager
        )

        self.mock_llm_function.return_value = "Using in-memory backend."

        # Store some memories
        await agent.run("I work as a developer", pattern=ExecutionPattern.SIMPLE)

        initial_memories = await memory_manager.get_all_memories()
        assert len(initial_memories) > 0

        # Switch to another in-memory backend (simulating backend change)
        new_backend = InMemoryBackend()
        await memory_manager.set_backend("in_memory_2", new_backend)

        # New backend should be empty
        new_memories = await memory_manager.get_all_memories()
        assert len(new_memories) == 0


class TestAgentPerformanceIntegration:
    """Test agent performance and scalability."""

    def setup_method(self):
        """Set up performance test fixtures."""
        self.memory_manager = CoreMemoryManager()
        self.memory_backend = InMemoryBackend()
        asyncio.run(self.memory_manager.set_backend("in_memory", self.memory_backend))

        self.tool_manager = ToolManager()
        self.mock_llm_function = AsyncMock()

        self.agent = CoreAgent(
            llm_function=self.mock_llm_function,
            memory_manager=self.memory_manager,
            tool_manager=self.tool_manager
        )

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        self.mock_llm_function.return_value = "Concurrent response"

        # Create multiple concurrent requests
        tasks = []
        for i in range(5):
            task = self.agent.run(
                f"Request {i}",
                pattern=ExecutionPattern.SIMPLE
            )
            tasks.append(task)

        # Wait for all to complete
        responses = await asyncio.gather(*tasks)

        # Verify all completed successfully
        assert len(responses) == 5
        assert all(response == "Concurrent response" for response in responses)

    @pytest.mark.asyncio
    async def test_large_memory_handling(self):
        """Test agent with large amount of memories."""
        self.mock_llm_function.return_value = "Memory handled"

        # Add many memories
        for i in range(50):
            await self.agent.run(
                f"Memory item {i} with content about topic {i % 10}",
                pattern=ExecutionPattern.SIMPLE
            )

        # Verify all memories stored
        memories = await self.memory_manager.get_all_memories()
        assert len(memories) >= 50

        # Test search still works
        topic_memories = await self.memory_manager.search_memories("topic 5")
        assert len(topic_memories) > 0

    @pytest.mark.asyncio
    async def test_memory_cleanup_workflow(self):
        """Test memory cleanup and management."""
        self.mock_llm_function.return_value = "Cleanup test"

        # Add memories
        for i in range(10):
            await self.agent.run(f"Item {i}", pattern=ExecutionPattern.SIMPLE)

        initial_count = len(await self.memory_manager.get_all_memories())

        # Clear memories
        await self.memory_manager.clear_all_memories()

        # Verify cleanup
        final_count = len(await self.memory_manager.get_all_memories())
        assert final_count < initial_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])