"""
Simple Core Agent Implementation

A lightweight agent that works with the actual implemented components.
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable, Awaitable, Union, AsyncIterator
from datetime import datetime
import uuid

try:
    from .memory import CoreMemoryManager
    from .tools import ToolManager
    from .execution.execution_patterns import ExecutionPatternType
except ImportError:
    # For standalone execution and testing
    from memory import CoreMemoryManager
    from tools import ToolManager
    from execution.execution_patterns import ExecutionPatternType


class CoreAgent:
    """
    Simple core agent that integrates memory and tools.

    This agent provides basic functionality for LLM interactions,
    memory management, and tool usage.
    """

    def __init__(
        self,
        llm_function: Optional[Callable] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        memory_manager: Optional[CoreMemoryManager] = None,
        tool_manager: Optional[ToolManager] = None,
        system_prompt: str = "You are a helpful AI assistant.",
        max_iterations: int = 5
    ):
        """
        Initialize the core agent.

        Args:
            llm_function: Function to call LLM (prompt) -> response
            llm_config: LLM configuration dict (alternative to llm_function)
            memory_manager: Optional memory manager instance
            tool_manager: Optional tool manager instance
            system_prompt: System prompt for the agent
            max_iterations: Maximum iterations for complex tasks
        """
        # LLM configuration
        if not llm_function and not llm_config:
            raise ValueError("Must provide either llm_function or llm_config")

        self.llm_function = llm_function
        self.llm_config = llm_config
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.session_id = str(uuid.uuid4())

        # Initialize components
        self.memory_manager = memory_manager or CoreMemoryManager()
        self.tool_manager = tool_manager or ToolManager()

        # Execution stats
        self.execution_stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "total_tokens_used": 0,
            "total_execution_time": 0.0
        }

    async def run(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        pattern: Optional[ExecutionPatternType] = None
    ) -> str:
        """
        Run the agent with a message.

        Args:
            message: Input message
            context: Optional context dict
            pattern: Execution pattern to use (ignored for now)

        Returns:
            Agent response
        """
        if not message:
            raise ValueError("Message cannot be empty")

        start_time = datetime.now()
        self.execution_stats["total_runs"] += 1

        try:
            # Build prompt with system message and context
            prompt = self._build_prompt(message, context)

            # Call LLM
            if self.llm_function:
                response = await self._call_llm_function(prompt)
            else:
                # Handle llm_config case if needed
                response = await self._call_llm_with_config(prompt)

            # Store in memory if available
            if self.memory_manager:
                await self._store_interaction(message, response)

            self.execution_stats["successful_runs"] += 1
            execution_time = (datetime.now() - start_time).total_seconds()
            self.execution_stats["total_execution_time"] += execution_time

            return response

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.execution_stats["total_execution_time"] += execution_time
            raise e

    async def run_stream(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """
        Run the agent with streaming response.

        Args:
            message: Input message
            context: Optional context dict

        Yields:
            Response chunks
        """
        if not message:
            raise ValueError("Message cannot be empty")

        # Build prompt
        prompt = self._build_prompt(message, context)

        # Stream response
        if hasattr(self.llm_function, '__call__'):
            # Check if llm_function returns an async generator
            result = self.llm_function(prompt)
            if hasattr(result, '__aiter__'):
                # It's a streaming response
                full_response = ""
                async for chunk in result:
                    full_response += chunk
                    yield chunk

                # Store final response
                if self.memory_manager:
                    await self._store_interaction(message, full_response)
            else:
                # Regular response, yield as single chunk
                response = await result
                if self.memory_manager:
                    await self._store_interaction(message, response)
                yield response
        else:
            # Fallback to regular run and yield as single chunk
            response = await self.run(message, context)
            yield response

    async def run_benchmark(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run benchmark tests.

        Args:
            test_cases: List of test case dicts

        Returns:
            Benchmark results
        """
        if not test_cases:
            return {
                "total_scenarios": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "average_response_time": 0.0,
                "total_time": 0.0
            }

        start_time = datetime.now()
        successful_runs = 0
        failed_runs = 0
        total_response_time = 0.0

        for i, test_case in enumerate(test_cases):
            try:
                case_start = datetime.now()
                input_msg = test_case.get("input", f"Test case {i}")

                await self.run(input_msg)

                case_time = (datetime.now() - case_start).total_seconds()
                total_response_time += case_time
                successful_runs += 1

            except Exception:
                failed_runs += 1

        total_time = (datetime.now() - start_time).total_seconds()

        return {
            "total_scenarios": len(test_cases),
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "average_response_time": total_response_time / len(test_cases) if test_cases else 0.0,
            "total_time": total_time
        }

    def add_example(self, input_text: str, output_text: str, metadata: Optional[Dict] = None):
        """Add an example for in-context learning."""
        # Store as memory for now - simplified for sync operation
        # In a real implementation, this would be async
        pass

    def get_examples(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get examples for in-context learning."""
        # This would need to be async in real implementation
        # For now, return empty list
        return []

    def set_execution_pattern(self, pattern: ExecutionPatternType):
        """Set execution pattern (placeholder)."""
        pass

    async def add_tool(self, tool) -> bool:
        """Add a tool to the agent."""
        if self.tool_manager:
            return await self.tool_manager.register_tool(tool)
        return False

    async def connect_mcp_server(self, name: str, connection_info: Dict[str, Any]) -> bool:
        """Connect to MCP server."""
        if self.tool_manager:
            return await self.tool_manager.connect_mcp_server(name, connection_info)
        return False

    async def start(self):
        """Start the agent (placeholder)."""
        pass

    async def stop(self):
        """Stop the agent (placeholder)."""
        pass

    def clone(self) -> 'CoreAgent':
        """Clone the agent."""
        return CoreAgent(
            llm_function=self.llm_function,
            llm_config=self.llm_config,
            memory_manager=self.memory_manager,
            tool_manager=self.tool_manager,
            system_prompt=self.system_prompt,
            max_iterations=self.max_iterations
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return self.execution_stats.copy()

    def _build_prompt(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Build the full prompt."""
        prompt_parts = [self.system_prompt]

        if context:
            context_str = "\n".join(f"{k}: {v}" for k, v in context.items())
            prompt_parts.append(f"Context:\n{context_str}")

        prompt_parts.append(f"User: {message}")

        return "\n\n".join(prompt_parts)

    async def _call_llm_function(self, prompt: str) -> str:
        """Call the LLM function."""
        if asyncio.iscoroutinefunction(self.llm_function):
            return await self.llm_function(prompt)
        else:
            return self.llm_function(prompt)

    async def _call_llm_with_config(self, prompt: str) -> str:
        """Call LLM with config (placeholder)."""
        # This would use the LiteLLM integration
        raise NotImplementedError("LLM config not yet implemented")

    async def _store_interaction(self, message: str, response: str):
        """Store interaction in memory."""
        if self.memory_manager:
            try:
                # Store user message
                await self.memory_manager.add_memory(
                    content=message,
                    metadata={"role": "user", "session_id": self.session_id}
                )

                # Store assistant response
                await self.memory_manager.add_memory(
                    content=response,
                    metadata={"role": "assistant", "session_id": self.session_id}
                )
            except Exception:
                # Ignore memory errors for now
                pass