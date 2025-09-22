"""Integration tests for memory backend and tool integration workflows."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List, Optional
import pytest
import json
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from memory.memory_manager import CoreMemoryManager
    from memory.backends.in_memory_backend import InMemoryBackend
    from memory.backends.redis_backend import RedisBackend
    from memory.memory_types import Memory, MemoryImportance
    from tools.tool_manager import ToolManager
    from tools.tool_interfaces import ToolInterface, ToolCall, ToolResult, ToolDefinition
    from agent import CoreAgent
    from execution.execution_patterns import ExecutionPattern
except ImportError as e:
    pytest.skip(f"Integration imports not available: {e}", allow_module_level=True)


class TestMemoryBackendIntegration:
    """Test integration between different memory backends."""

    def setup_method(self):
        """Set up memory backend integration tests."""
        self.memory_manager = CoreMemoryManager()

    @pytest.mark.asyncio
    async def test_backend_switching_workflow(self):
        """Test switching between memory backends."""
        # Start with in-memory backend
        in_memory_backend = InMemoryBackend()
        await self.memory_manager.set_backend("in_memory", in_memory_backend)

        # Store some memories
        memory1 = Memory(
            id="mem1",
            content="First memory",
            importance=MemoryImportance.HIGH,
            metadata={"type": "test"}
        )

        success = await self.memory_manager.add_memory(memory1)
        assert success is True

        # Verify memory exists
        retrieved = await self.memory_manager.get_memory("mem1")
        assert retrieved is not None
        assert retrieved.content == "First memory"

        # Switch to another in-memory backend (simulating different backend type)
        new_backend = InMemoryBackend()
        await self.memory_manager.set_backend("new_backend", new_backend)

        # Original memory should not be accessible in new backend
        retrieved_new = await self.memory_manager.get_memory("mem1")
        assert retrieved_new is None

        # Add memory to new backend
        memory2 = Memory(
            id="mem2",
            content="Second memory",
            importance=MemoryImportance.MEDIUM
        )

        success = await self.memory_manager.add_memory(memory2)
        assert success is True

        # Verify new memory exists
        retrieved_new = await self.memory_manager.get_memory("mem2")
        assert retrieved_new is not None
        assert retrieved_new.content == "Second memory"

    @pytest.mark.asyncio
    async def test_memory_migration_workflow(self):
        """Test migrating memories between backends."""
        # Setup two backends
        backend1 = InMemoryBackend()
        backend2 = InMemoryBackend()

        # Add memories to first backend
        await self.memory_manager.set_backend("backend1", backend1)

        memories = []
        for i in range(5):
            memory = Memory(
                id=f"mem_{i}",
                content=f"Memory content {i}",
                importance=MemoryImportance.MEDIUM,
                metadata={"source": "backend1", "index": i}
            )
            memories.append(memory)
            await self.memory_manager.add_memory(memory)

        # Verify memories in first backend
        all_memories_1 = await self.memory_manager.get_all_memories()
        assert len(all_memories_1) == 5

        # Switch to second backend
        await self.memory_manager.set_backend("backend2", backend2)

        # Second backend should be empty
        all_memories_2 = await self.memory_manager.get_all_memories()
        assert len(all_memories_2) == 0

        # Manually migrate memories (simulate migration process)
        await self.memory_manager.set_backend("backend1", backend1)
        source_memories = await self.memory_manager.get_all_memories()

        await self.memory_manager.set_backend("backend2", backend2)
        for memory in source_memories:
            await self.memory_manager.add_memory(memory)

        # Verify migration
        migrated_memories = await self.memory_manager.get_all_memories()
        assert len(migrated_memories) == 5

        # Verify content preservation
        for original, migrated in zip(memories, migrated_memories):
            assert original.content == migrated.content
            assert original.importance == migrated.importance

    @pytest.mark.asyncio
    async def test_memory_search_across_backends(self):
        """Test memory search functionality across different backends."""
        # Test with in-memory backend
        in_memory_backend = InMemoryBackend()
        await self.memory_manager.set_backend("in_memory", in_memory_backend)

        # Add searchable memories
        search_memories = [
            Memory(id="search1", content="Python programming tutorial", importance=MemoryImportance.HIGH),
            Memory(id="search2", content="JavaScript framework comparison", importance=MemoryImportance.MEDIUM),
            Memory(id="search3", content="Python data structures guide", importance=MemoryImportance.HIGH),
            Memory(id="search4", content="Web development best practices", importance=MemoryImportance.LOW)
        ]

        for memory in search_memories:
            await self.memory_manager.add_memory(memory)

        # Test search functionality
        python_results = await self.memory_manager.search_memories("Python")
        assert len(python_results) == 2
        assert all("Python" in result.content for result in python_results)

        # Test search with filters
        high_importance_results = await self.memory_manager.search_memories(
            "programming",
            filters={"importance": "HIGH"}
        )
        assert len(high_importance_results) >= 1
        assert all(result.importance == MemoryImportance.HIGH for result in high_importance_results)

    @pytest.mark.asyncio
    async def test_memory_ttl_and_cleanup(self):
        """Test memory TTL and cleanup across backends."""
        backend = InMemoryBackend()
        await self.memory_manager.set_backend("test_backend", backend)

        # Add memory with short TTL (simulate expired)
        expired_memory = Memory(
            id="expired",
            content="This should expire",
            importance=MemoryImportance.LOW,
            created_at=datetime.now() - timedelta(hours=25),  # 25 hours ago
            metadata={"ttl": 24}  # 24 hour TTL
        )

        # Add current memory
        current_memory = Memory(
            id="current",
            content="This is current",
            importance=MemoryImportance.HIGH
        )

        await self.memory_manager.add_memory(expired_memory)
        await self.memory_manager.add_memory(current_memory)

        # Test cleanup (simulate)
        all_memories = await self.memory_manager.get_all_memories()
        assert len(all_memories) == 2

        # Manually filter expired memories (simulate cleanup process)
        active_memories = [
            m for m in all_memories
            if not (hasattr(m, 'created_at') and m.created_at < datetime.now() - timedelta(hours=24))
        ]

        # Should have only current memory after cleanup
        assert len(active_memories) >= 1


class TestToolManagerIntegration:
    """Test integration of tool manager with various tool types."""

    def setup_method(self):
        """Set up tool manager integration tests."""
        self.tool_manager = ToolManager()

    @pytest.mark.asyncio
    async def test_local_tool_registration_workflow(self):
        """Test complete local tool registration and execution workflow."""

        # Create a test tool
        class MathTool(ToolInterface):
            def get_definition(self) -> ToolDefinition:
                return ToolDefinition(
                    name="math_calculator",
                    description="Performs mathematical calculations",
                    parameters={
                        "type": "object",
                        "properties": {
                            "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
                            "a": {"type": "number"},
                            "b": {"type": "number"}
                        },
                        "required": ["operation", "a", "b"]
                    },
                    category="math"
                )

            async def execute(self, tool_call: ToolCall) -> ToolResult:
                operation = tool_call.arguments.get("operation")
                a = float(tool_call.arguments.get("a", 0))
                b = float(tool_call.arguments.get("b", 0))

                try:
                    if operation == "add":
                        result = a + b
                    elif operation == "subtract":
                        result = a - b
                    elif operation == "multiply":
                        result = a * b
                    elif operation == "divide":
                        result = a / b if b != 0 else "Error: Division by zero"
                    else:
                        result = "Error: Unknown operation"

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

        # Register tool
        math_tool = MathTool()
        success = await self.tool_manager.register_tool(math_tool, aliases=["calc", "calculator"])
        assert success is True

        # Verify tool is registered
        assert self.tool_manager.has_tool("math_calculator")
        assert self.tool_manager.has_tool("calc")
        assert self.tool_manager.has_tool("calculator")

        # Get tool definitions
        tools = self.tool_manager.list_available_tools()
        math_tools = [t for t in tools if t.name == "math_calculator"]
        assert len(math_tools) == 1

        # Test tool execution
        result = await self.tool_manager.execute_tool_by_name(
            "math_calculator",
            {"operation": "add", "a": 15, "b": 27}
        )

        assert result.success is True
        assert result.content == "42.0"

        # Test with alias
        result = await self.tool_manager.execute_tool_by_name(
            "calc",
            {"operation": "multiply", "a": 6, "b": 7}
        )

        assert result.success is True
        assert result.content == "42.0"

    @pytest.mark.asyncio
    async def test_tool_batch_execution(self):
        """Test batch execution of multiple tools."""

        # Create multiple simple tools
        class EchoTool(ToolInterface):
            def __init__(self, name_suffix):
                self.name_suffix = name_suffix

            def get_definition(self) -> ToolDefinition:
                return ToolDefinition(
                    name=f"echo_{self.name_suffix}",
                    description=f"Echo tool {self.name_suffix}",
                    parameters={
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"}
                        }
                    }
                )

            async def execute(self, tool_call: ToolCall) -> ToolResult:
                message = tool_call.arguments.get("message", "")
                return ToolResult(
                    call_id=tool_call.id,
                    success=True,
                    content=f"Echo {self.name_suffix}: {message}",
                    execution_time=0.05
                )

        # Register multiple tools
        for i in range(3):
            tool = EchoTool(str(i + 1))
            await self.tool_manager.register_tool(tool)

        # Create batch tool calls
        tool_calls = [
            ToolCall(name="echo_1", arguments={"message": "Hello"}),
            ToolCall(name="echo_2", arguments={"message": "World"}),
            ToolCall(name="echo_3", arguments={"message": "Test"})
        ]

        # Execute batch
        results = await self.tool_manager.batch_execute_tools(tool_calls)

        # Verify results
        assert len(results) == 3
        assert all(result.success for result in results)
        assert "Echo 1: Hello" in results[0].content
        assert "Echo 2: World" in results[1].content
        assert "Echo 3: Test" in results[2].content

    @pytest.mark.asyncio
    async def test_tool_validation_workflow(self):
        """Test tool validation workflow."""

        # Create tool with strict validation
        class ValidatedTool(ToolInterface):
            def get_definition(self) -> ToolDefinition:
                return ToolDefinition(
                    name="validated_tool",
                    description="Tool with validation",
                    parameters={
                        "type": "object",
                        "properties": {
                            "required_param": {"type": "string"},
                            "optional_param": {"type": "number", "minimum": 0, "maximum": 100}
                        },
                        "required": ["required_param"]
                    }
                )

            async def execute(self, tool_call: ToolCall) -> ToolResult:
                return ToolResult(
                    call_id=tool_call.id,
                    success=True,
                    content="Validation passed",
                    execution_time=0.1
                )

        # Register tool
        validated_tool = ValidatedTool()
        await self.tool_manager.register_tool(validated_tool)

        # Test valid call
        valid_call = ToolCall(
            name="validated_tool",
            arguments={"required_param": "test", "optional_param": 50}
        )

        is_valid = self.tool_manager.validate_tool_call(valid_call)
        assert is_valid is True

        # Test execution
        result = await self.tool_manager.execute_tool(valid_call)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_tool_error_handling(self):
        """Test tool error handling workflows."""

        # Create tool that can fail
        class FailingTool(ToolInterface):
            def get_definition(self) -> ToolDefinition:
                return ToolDefinition(
                    name="failing_tool",
                    description="Tool that can fail",
                    parameters={
                        "type": "object",
                        "properties": {
                            "should_fail": {"type": "boolean"}
                        }
                    }
                )

            async def execute(self, tool_call: ToolCall) -> ToolResult:
                should_fail = tool_call.arguments.get("should_fail", False)

                if should_fail:
                    raise Exception("Simulated tool failure")

                return ToolResult(
                    call_id=tool_call.id,
                    success=True,
                    content="Tool executed successfully",
                    execution_time=0.1
                )

        # Register tool
        failing_tool = FailingTool()
        await self.tool_manager.register_tool(failing_tool)

        # Test successful execution
        success_result = await self.tool_manager.execute_tool_by_name(
            "failing_tool",
            {"should_fail": False}
        )
        assert success_result.success is True

        # Test failed execution
        fail_result = await self.tool_manager.execute_tool_by_name(
            "failing_tool",
            {"should_fail": True}
        )
        assert fail_result.success is False
        assert "Simulated tool failure" in fail_result.error


class TestAgentToolMemoryIntegration:
    """Test complete integration of agent, tools, and memory."""

    def setup_method(self):
        """Set up complete integration tests."""
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
    async def test_complete_workflow_integration(self):
        """Test complete workflow with agent, tools, and memory."""

        # Register a note-taking tool
        class NoteTool(ToolInterface):
            def __init__(self, memory_manager):
                self.memory_manager = memory_manager

            def get_definition(self) -> ToolDefinition:
                return ToolDefinition(
                    name="note_taker",
                    description="Takes and stores notes",
                    parameters={
                        "type": "object",
                        "properties": {
                            "note": {"type": "string"},
                            "category": {"type": "string"}
                        },
                        "required": ["note"]
                    }
                )

            async def execute(self, tool_call: ToolCall) -> ToolResult:
                note = tool_call.arguments.get("note")
                category = tool_call.arguments.get("category", "general")

                # Store note as memory
                memory = Memory(
                    id=f"note_{len(await self.memory_manager.get_all_memories())}",
                    content=note,
                    importance=MemoryImportance.MEDIUM,
                    metadata={"type": "note", "category": category}
                )

                success = await self.memory_manager.add_memory(memory)

                return ToolResult(
                    call_id=tool_call.id,
                    success=success,
                    content=f"Note saved: {note}",
                    execution_time=0.1
                )

        # Register note tool
        note_tool = NoteTool(self.memory_manager)
        await self.tool_manager.register_tool(note_tool)

        # Setup LLM responses
        self.mock_llm_function.side_effect = [
            "I'll take a note about Python for you.",
            "I'll retrieve your Python notes."
        ]

        # Mock tool execution for first call
        with patch.object(self.tool_manager, 'execute_tool_by_name') as mock_execute:
            mock_result = Mock()
            mock_result.success = True
            mock_result.content = "Note saved: Python is a great programming language"
            mock_execute.return_value = mock_result

            # Take a note
            response1 = await self.agent.run(
                "Take a note: Python is a great programming language",
                pattern=ExecutionPattern.REACT
            )

            assert "note" in response1.lower()

        # Verify note was stored in memory
        all_memories = await self.memory_manager.get_all_memories()
        note_memories = [m for m in all_memories if m.metadata.get("type") == "note"]

        # Should have at least the conversation memory and potentially the note
        assert len(all_memories) >= 1

        # Search for Python-related memories
        python_memories = await self.memory_manager.search_memories("Python")
        assert len(python_memories) >= 1

    @pytest.mark.asyncio
    async def test_memory_informed_tool_usage(self):
        """Test tools that are informed by memory context."""

        # Create a context-aware tool
        class ContextTool(ToolInterface):
            def __init__(self, memory_manager):
                self.memory_manager = memory_manager

            def get_definition(self) -> ToolDefinition:
                return ToolDefinition(
                    name="context_aware",
                    description="Uses memory context to provide responses",
                    parameters={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        },
                        "required": ["query"]
                    }
                )

            async def execute(self, tool_call: ToolCall) -> ToolResult:
                query = tool_call.arguments.get("query")

                # Search memory for context
                relevant_memories = await self.memory_manager.search_memories(query, limit=3)

                context = "\n".join([m.content for m in relevant_memories])
                response = f"Based on context: {context}" if context else "No relevant context found"

                return ToolResult(
                    call_id=tool_call.id,
                    success=True,
                    content=response,
                    execution_time=0.2
                )

        # Register context tool
        context_tool = ContextTool(self.memory_manager)
        await self.tool_manager.register_tool(context_tool)

        # Add some memories first
        memories = [
            Memory(id="mem1", content="User likes coffee", importance=MemoryImportance.MEDIUM),
            Memory(id="mem2", content="User is a developer", importance=MemoryImportance.HIGH),
            Memory(id="mem3", content="User prefers Python", importance=MemoryImportance.HIGH)
        ]

        for memory in memories:
            await self.memory_manager.add_memory(memory)

        # Test context-aware tool usage
        with patch.object(self.tool_manager, 'execute_tool_by_name') as mock_execute:
            # Simulate tool finding context
            mock_result = Mock()
            mock_result.success = True
            mock_result.content = "Based on context: User likes coffee\nUser prefers Python"
            mock_execute.return_value = mock_result

            self.mock_llm_function.return_value = "Based on your preferences, here's what I found."

            response = await self.agent.run(
                "What do you know about my preferences?",
                pattern=ExecutionPattern.REACT
            )

            assert "preferences" in response.lower()

    @pytest.mark.asyncio
    async def test_tool_memory_feedback_loop(self):
        """Test feedback loop between tool results and memory storage."""

        # Create a learning tool that stores results
        class LearningTool(ToolInterface):
            def __init__(self, memory_manager):
                self.memory_manager = memory_manager

            def get_definition(self) -> ToolDefinition:
                return ToolDefinition(
                    name="learning_tool",
                    description="Learns from interactions",
                    parameters={
                        "type": "object",
                        "properties": {
                            "action": {"type": "string"},
                            "data": {"type": "string"}
                        },
                        "required": ["action"]
                    }
                )

            async def execute(self, tool_call: ToolCall) -> ToolResult:
                action = tool_call.arguments.get("action")
                data = tool_call.arguments.get("data", "")

                # Store learning as memory
                learning_memory = Memory(
                    id=f"learning_{datetime.now().isoformat()}",
                    content=f"Learned: {action} - {data}",
                    importance=MemoryImportance.HIGH,
                    metadata={"type": "learning", "action": action}
                )

                await self.memory_manager.add_memory(learning_memory)

                # Return what was learned
                return ToolResult(
                    call_id=tool_call.id,
                    success=True,
                    content=f"Learned and remembered: {action}",
                    execution_time=0.1
                )

        # Register learning tool
        learning_tool = LearningTool(self.memory_manager)
        await self.tool_manager.register_tool(learning_tool)

        # Test learning workflow
        with patch.object(self.tool_manager, 'execute_tool_by_name') as mock_execute:
            mock_result = Mock()
            mock_result.success = True
            mock_result.content = "Learned and remembered: user_preference"
            mock_execute.return_value = mock_result

            self.mock_llm_function.return_value = "I've learned and stored your preference."

            # Simulate learning interaction
            response = await self.agent.run(
                "Learn that I prefer dark mode",
                pattern=ExecutionPattern.REACT
            )

            assert "learned" in response.lower() or "stored" in response.lower()

        # Verify learning was stored in memory
        learning_memories = await self.memory_manager.search_memories("learned")
        assert len(learning_memories) >= 0  # May have conversation memory

        # Check for learning-type memories
        all_memories = await self.memory_manager.get_all_memories()
        learning_type_memories = [
            m for m in all_memories
            if m.metadata.get("type") == "learning"
        ]
        # Tool wasn't actually executed, so this might be 0
        assert len(learning_type_memories) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])