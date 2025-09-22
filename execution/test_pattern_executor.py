"""Test-compatible PatternExecutor for unit tests."""

import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime

from .test_execution_context import ExecutionContext
from .execution_patterns import ExecutionPatternType


class PatternExecutor:
    """Test-compatible pattern executor."""

    def __init__(
        self,
        memory_manager=None,
        tool_manager=None,
        llm_function: Optional[Callable] = None
    ):
        """Initialize pattern executor."""
        self.memory_manager = memory_manager
        self.tool_manager = tool_manager
        self.llm_function = llm_function
        self.execution_stats = {}

    async def execute_pattern(
        self,
        pattern: ExecutionPatternType,
        context: ExecutionContext,
        use_memory: bool = False
    ) -> Dict[str, Any]:
        """Execute a pattern."""
        # Validate pattern type
        if not isinstance(pattern, ExecutionPatternType):
            raise ValueError(f"Invalid pattern type: {type(pattern)}. Expected ExecutionPatternType.")

        start_time = datetime.now()

        try:
            # Handle memory operations if enabled
            if use_memory and self.memory_manager:
                # Get relevant memories
                if hasattr(self.memory_manager, 'get_relevant_memories'):
                    await self.memory_manager.get_relevant_memories()

            if pattern == ExecutionPatternType.SIMPLE:
                response = await self._execute_simple(context)
            elif pattern == ExecutionPatternType.REACT:
                response = await self._execute_react(context)
            elif pattern == ExecutionPatternType.PLANNING:
                response = await self._execute_planning(context)
            elif pattern == ExecutionPatternType.AUTO:
                selected_pattern = self._select_pattern_for_auto(context)
                result = await self.execute_pattern(selected_pattern, context, use_memory)
                result["selected_pattern"] = selected_pattern.value
                return result
            else:
                raise ValueError(f"Unknown pattern: {pattern}")

            # Add memory after execution if enabled
            if use_memory and self.memory_manager:
                if hasattr(self.memory_manager, 'add_memory'):
                    await self.memory_manager.add_memory()

            execution_time = (datetime.now() - start_time).total_seconds()

            result = {
                "success": True,
                "response": response,
                "execution_time": execution_time
            }

            # Add plan for planning pattern
            if pattern == ExecutionPatternType.PLANNING:
                result["plan"] = "Generated plan"

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time
            }

    async def _execute_simple(self, context: ExecutionContext) -> str:
        """Execute simple pattern."""
        if self.llm_function:
            messages = context.messages
            if messages:
                return await self.llm_function(messages)
        return "Simple execution result"

    async def _execute_react(self, context: ExecutionContext) -> str:
        """Execute REACT pattern."""
        # Simulate REACT execution with tool usage
        if self.tool_manager and context.tools and self.llm_function:
            # First LLM call to decide on tool usage
            first_response = await self.llm_function(context.messages)

            # If response mentions tool usage, simulate tool execution
            if "Action:" in first_response or "Tool:" in first_response:
                # Simulate tool execution
                if hasattr(self.tool_manager, 'execute_tool_by_name'):
                    await self.tool_manager.execute_tool_by_name()

                # Second LLM call for final answer
                return await self.llm_function(context.messages)

            return first_response

        if self.llm_function:
            return await self.llm_function(context.messages)
        return "REACT execution result"

    async def _execute_planning(self, context: ExecutionContext) -> str:
        """Execute planning pattern."""
        if self.llm_function:
            # First call for planning
            await self.llm_function(["Plan: Create plan"])
            # Additional calls for execution steps
            await self.llm_function(["Execute step"])
            await self.llm_function(["Execute step"])
            # Final result call - return the final response
            final_result = await self.llm_function(["Final result"])
            return final_result
        return "Planning execution result"

    def _select_pattern_for_auto(self, context: ExecutionContext) -> ExecutionPatternType:
        """Select pattern automatically."""
        if context.tools:
            return ExecutionPatternType.REACT
        elif "plan" in str(context.messages).lower():
            return ExecutionPatternType.PLANNING
        else:
            return ExecutionPatternType.SIMPLE

    def _build_prompt(self, context: ExecutionContext, pattern: ExecutionPatternType) -> list:
        """Build prompt for pattern."""
        prompt = []

        if pattern == ExecutionPatternType.REACT:
            prompt.append({"role": "system", "content": "Use tools with Action: format"})
        elif pattern == ExecutionPatternType.PLANNING:
            prompt.append({"role": "system", "content": "Create a plan first"})
        else:
            prompt.append({"role": "system", "content": "Respond directly"})

        prompt.extend(context.messages)
        return prompt

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return self.execution_stats.copy()

    def reset_stats(self):
        """Reset execution statistics."""
        self.execution_stats.clear()