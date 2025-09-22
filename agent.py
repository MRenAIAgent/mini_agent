"""
Core Agent Implementation

Lightweight agent that combines all core components:
- ReAct execution loop
- Memory management
- Prompt optimization
- Tool/MCP integration
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable, Awaitable, Union, AsyncIterator
from datetime import datetime
import uuid

try:
    from .execution import ReactExecutor, ExecutionContext, ExecutionResult
    from .execution.pattern_executor import PatternExecutor
    from .execution.execution_patterns import ExecutionPatternType
    from .memory import CoreMemoryManager, MemoryContext
    from .optimization import CoreOptimizer, OptimizationContext, TrainingExample
    from .tools import ToolManager, ToolCall, ToolResult
except ImportError:
    # For standalone execution and testing
    from execution import ReactExecutor, ExecutionContext, ExecutionResult
    from execution.pattern_executor import PatternExecutor
    from execution.execution_patterns import ExecutionPatternType
    from memory import CoreMemoryManager, MemoryContext
    from optimization import CoreOptimizer, OptimizationContext, TrainingExample
    from tools import ToolManager, ToolCall, ToolResult


class CoreAgent:
    """
    Core agent that integrates all essential components.

    This agent provides a complete, lightweight framework for autonomous
    agents with reasoning, memory, optimization, and tool capabilities.
    """

    def __init__(
        self,
        llm_function: Optional[Callable[[str], Awaitable[str]]] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        system_prompt: str = "",
        max_iterations: int = 5,
        enable_memory: bool = True,
        enable_optimization: bool = False,
        session_id: Optional[str] = None,
        execution_pattern: ExecutionPatternType = ExecutionPatternType.REACT,
        enable_pattern_selection: bool = True
    ):
        """
        Initialize the core agent.

        Args:
            llm_function: [DEPRECATED] Function to call LLM (prompt) -> response
            llm_config: LLM configuration dict with provider, model, api_key, etc.
            system_prompt: Base system prompt for the agent
            max_iterations: Maximum ReAct iterations per task
            enable_memory: Whether to enable memory management
            enable_optimization: Whether to enable prompt optimization
            session_id: Optional session ID for memory context
            execution_pattern: Default execution pattern to use
            enable_pattern_selection: Whether to enable automatic pattern selection
        """
        # Validate LLM configuration (backward compatibility)
        if llm_function and llm_config:
            raise ValueError("Cannot provide both llm_function and llm_config. Use llm_config for new code.")

        if not llm_function and not llm_config:
            raise ValueError("Must provide either llm_function (deprecated) or llm_config.")

        # Validate LLM function signature if provided
        if llm_function is not None:
            if not callable(llm_function):
                raise TypeError("llm_function must be callable")

            # Check function signature - should accept at least one parameter
            import inspect
            try:
                sig = inspect.signature(llm_function)
                if len(sig.parameters) == 0:
                    raise ValueError("llm_function must accept at least one parameter (prompt)")
            except (ValueError, TypeError) as e:
                raise TypeError(f"Invalid llm_function signature: {e}")

        # Store LLM configuration
        self.llm_function = llm_function
        self.llm_config = llm_config
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.session_id = session_id or str(uuid.uuid4())

        # Initialize components
        self.tool_manager = ToolManager()

        if enable_memory:
            self.memory_manager = CoreMemoryManager()
        else:
            self.memory_manager = None

        if enable_optimization:
            self.optimizer = CoreOptimizer()
        else:
            self.optimizer = None

        # Create execution system
        self.execution_pattern = execution_pattern
        self.current_pattern = execution_pattern  # Track current pattern for switching
        self.enable_pattern_selection = enable_pattern_selection

        # Create ReAct executor (legacy support)
        self.executor = ReactExecutor(
            llm_call=self._enhanced_llm_call,
            tool_call=self._tool_call_wrapper,
            max_iterations=max_iterations
        )

        # Create pattern executor (new system)
        self.pattern_executor = PatternExecutor(
            llm_call=self._enhanced_llm_call,
            tool_call=self._tool_call_wrapper,
            default_pattern=execution_pattern,
            max_iterations=max_iterations
        )

        # Add default pattern selection rules
        if enable_pattern_selection:
            # Note: add_default_rules not implemented yet
            pass

        # State
        self.current_context: Optional[ExecutionContext] = None
        self.optimization_history: List[Dict[str, Any]] = []

    @property
    def tools(self):
        """Backward compatibility property for accessing tools."""
        if hasattr(self.tool_manager, 'tools'):
            return self.tool_manager.tools
        elif hasattr(self.tool_manager, 'get_tools'):
            return self.tool_manager.get_tools()
        else:
            return []

    async def start(self) -> None:
        """Start the agent and initialize components."""
        if self.memory_manager:
            await self.memory_manager.start()

    async def stop(self) -> None:
        """Stop the agent and clean up resources."""
        if self.memory_manager:
            await self.memory_manager.stop()

        await self.tool_manager.shutdown()

    async def run(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        execution_pattern: Optional[ExecutionPatternType] = None
    ) -> str:
        """
        Run the agent on a user input.

        Args:
            user_input: The user's question or request
            context: Optional additional context
            execution_pattern: Optional specific pattern to use

        Returns:
            The agent's response
        """
        # Get enhanced system prompt with context
        enhanced_prompt = await self._build_enhanced_prompt(user_input, context)

        # Use pattern executor if pattern is specified or pattern selection is enabled
        if execution_pattern or self.enable_pattern_selection:
            result = await self.pattern_executor.execute(
                user_input=user_input,
                system_prompt=enhanced_prompt,
                pattern=execution_pattern
            )
        else:
            # Fallback to legacy ReAct executor
            result = await self.executor.execute(
                user_input=user_input,
                system_prompt=enhanced_prompt
            )

        # Store conversation in memory
        if self.memory_manager and result.success:
            await self.memory_manager.add_conversation_turn(
                session_id=self.session_id,
                user_input=user_input,
                agent_response=result.final_answer,
                execution_result=result.to_dict()
            )

        # Return final answer or error
        if result.success:
            # Check for empty or None responses first
            if not result.final_answer or result.final_answer.strip() == "":
                return "I don't have a response to that."
            elif result.final_answer == "I couldn't determine a final answer.":
                # This default message can indicate different scenarios
                # Check if we have actual error information
                if result.error_message:
                    return f"I encountered an error: {result.error_message}"
                elif hasattr(result, 'metadata') and result.metadata:
                    # Check for error info in metadata
                    for key in ['original_error', 'error', 'exception']:
                        if key in result.metadata:
                            return f"I encountered an error: {result.metadata[key]}"

                # Check if steps were taken - if no steps, likely an immediate error (exception)
                # If steps were taken, check if they contain error information
                if not result.execution_steps or len(result.execution_steps) == 0:
                    return "I encountered an error: LLM connection error"
                else:
                    # Check if any execution step contains error information
                    for step in result.execution_steps:
                        step_content = getattr(step, 'content', '') or getattr(step, 'observation', '') or getattr(step, 'thought', '')
                        if step_content and "I encountered an error processing your request" in step_content:
                            return step_content

                    return "I don't have a response to that."

            return result.final_answer
        else:
            return f"I encountered an error: {result.error_message}"

    async def run_stream(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        execution_pattern: Optional[ExecutionPatternType] = None
    ) -> AsyncIterator[str]:
        """
        Run the agent on user input with streaming response.

        Args:
            user_input: The user's question or request
            context: Optional additional context
            execution_pattern: Optional specific pattern to use

        Yields:
            Chunks of the response as strings
        """
        if not user_input.strip():
            raise ValueError("User input cannot be empty")

        # Get enhanced system prompt with context
        enhanced_prompt = await self._build_enhanced_prompt(user_input, context)

        # For now, use simple streaming implementation (constitutional compliance)
        if self.llm_config:
            # Use LiteLLM streaming if available
            async for chunk in self._stream_with_litellm(enhanced_prompt, user_input):
                yield chunk
        else:
            # Fallback to non-streaming for legacy llm_function
            response = await self.run(user_input, context, execution_pattern)
            # Simulate streaming by yielding words
            words = response.split()
            for word in words:
                yield word + " "

    async def _stream_with_litellm(self, system_prompt: str, user_input: str) -> AsyncIterator[str]:
        """
        Stream response using LiteLLM configuration.
        """
        if not self.llm_config:
            raise ValueError("LLM config not available")

        try:
            # Import LiteLLM provider
            from integrations.litellm_provider import LiteLLMProvider

            # Create provider instance
            provider = LiteLLMProvider(self.llm_config)

            # Create full prompt
            full_prompt = f"{system_prompt}\n\nUser: {user_input}\nAssistant:"

            # Stream the response
            async for chunk in provider.stream_call(full_prompt):
                yield chunk

        except ImportError:
            # Fallback to word-by-word streaming if LiteLLM not available
            response = await self._enhanced_llm_call(f"{system_prompt}\n\nUser: {user_input}\nAssistant:")
            words = response.split()
            for word in words:
                yield word + " "

        except Exception:
            # Fallback to word-by-word streaming on error
            response = await self._enhanced_llm_call(f"{system_prompt}\n\nUser: {user_input}\nAssistant:")
            words = response.split()
            for word in words:
                yield word + " "

    async def add_tool(self, tool, aliases: Optional[List[str]] = None) -> bool:
        """
        Add a tool to the agent.

        Args:
            tool: Tool implementation
            aliases: Optional aliases for the tool

        Returns:
            True if successful
        """
        return await self.tool_manager.register_tool(tool, aliases)

    async def connect_mcp_server(
        self,
        name: str,
        connection_info: Dict[str, Any]
    ) -> bool:
        """
        Connect to an MCP server.

        Args:
            name: Name for the connection
            connection_info: Connection configuration

        Returns:
            True if successful
        """
        return await self.tool_manager.connect_mcp_server(name, connection_info)

    async def optimize_prompt(
        self,
        training_examples: List[Dict[str, str]],
        strategy: str = "bootstrap"
    ) -> bool:
        """
        Optimize the agent's prompt using training examples.

        Args:
            training_examples: List of {"input": ..., "output": ...} examples
            strategy: Optimization strategy to use

        Returns:
            True if optimization improved performance
        """
        if not self.optimizer:
            return False

        # Convert training examples
        examples = [
            TrainingExample(input=ex["input"], expected_output=ex["output"])
            for ex in training_examples
        ]

        # Create agent evaluator
        async def agent_evaluator(prompt: str, example: TrainingExample) -> str:
            # Temporarily use the candidate prompt
            original_prompt = self.system_prompt
            self.system_prompt = prompt

            try:
                # Run agent on the example
                response = await self.run(example.input)
                return response
            finally:
                # Restore original prompt
                self.system_prompt = original_prompt

        # Run optimization
        self.optimizer.set_strategy(strategy)
        result = await self.optimizer.optimize(
            initial_prompt=self.system_prompt,
            training_examples=examples,
            agent_evaluator=agent_evaluator
        )

        # Update prompt if optimization was successful
        if result.success and result.improvement > 0:
            self.system_prompt = result.optimized_prompt
            self.optimization_history.append(result.to_dict())
            return True

        return False

    async def remember(
        self,
        content: str,
        importance: float = 1.0,
        **metadata
    ) -> bool:
        """
        Store something in memory.

        Args:
            content: Content to remember
            importance: Importance score (0.0 to 1.0)
            **metadata: Additional metadata

        Returns:
            True if successful
        """
        if not self.memory_manager:
            return False

        return await self.memory_manager.store_memory(
            content=content,
            importance=importance,
            session_id=self.session_id,
            **metadata
        )

    async def recall(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recall relevant memories.

        Args:
            query: Search query
            limit: Maximum number of memories

        Returns:
            List of relevant memories
        """
        if not self.memory_manager:
            return []

        memories = await self.memory_manager.search_memory(
            query=query,
            limit=limit,
            session_id=self.session_id
        )

        return [
            {
                "content": memory.content,
                "importance": memory.importance,
                "timestamp": memory.timestamp.isoformat(),
                "metadata": memory.metadata
            }
            for memory in memories
        ]

    async def get_context_summary(self) -> str:
        """Get a summary of the current conversation context."""
        if not self.memory_manager:
            return "No memory available."

        return await self.memory_manager.summarize_context(self.session_id)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        definitions = self.tool_manager.list_available_tools()
        return [def_.to_dict() for def_ in definitions]

    def get_agent_stats(self) -> Dict[str, Any]:
        """Get comprehensive agent statistics."""
        stats = {
            "session_id": self.session_id,
            "system_prompt_length": len(self.system_prompt),
            "max_iterations": self.max_iterations,
            "components": {
                "memory_enabled": self.memory_manager is not None,
                "optimization_enabled": self.optimizer is not None,
            },
            "tools": self.tool_manager.get_manager_stats(),
            "optimization_history": len(self.optimization_history)
        }

        if self.memory_manager:
            stats["memory"] = asyncio.create_task(self.memory_manager.get_memory_stats())

        return stats

    async def _build_enhanced_prompt(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build enhanced system prompt with context and memory."""
        prompt_parts = [self.system_prompt]

        # Add tool information
        tools = self.tool_manager.list_available_tools()
        if tools:
            tool_descriptions = []
            for tool_def in tools:
                tool_descriptions.append(f"- {tool_def.name}: {tool_def.description}")

            prompt_parts.append(f"\nYou have access to these tools:\n" + "\n".join(tool_descriptions))

        # Add memory context
        if self.memory_manager:
            relevant_context = await self.memory_manager.get_relevant_context(
                session_id=self.session_id,
                query=user_input
            )

            if relevant_context.get("conversation"):
                summary = relevant_context["conversation"]["summary"]
                if summary:
                    prompt_parts.append(f"\nConversation context:\n{summary}")

            if relevant_context.get("memories"):
                memories = relevant_context["memories"][:3]  # Limit to top 3
                if memories:
                    memory_text = "\n".join([
                        f"- {mem['content']}" for mem in memories
                    ])
                    prompt_parts.append(f"\nRelevant memories:\n{memory_text}")

        # Add examples for in-context learning (constitutional compliance: simple approach)
        if self.memory_manager:
            try:
                examples = await self.memory_manager.search_memory(
                    query=user_input,
                    limit=3
                )
                # Filter for example-type memories
                example_memories = [
                    mem for mem in examples
                    if mem.get("metadata", {}).get("type") == "example"
                ]
                if example_memories:
                    example_text = "\n".join([
                        f"Example: {mem['content']}" for mem in example_memories
                    ])
                    prompt_parts.append(f"\nExamples:\n{example_text}")
            except Exception:
                # Non-critical: skip examples if retrieval fails
                pass

        # Add custom context
        if context:
            context_text = "\n".join([f"{k}: {v}" for k, v in context.items()])
            prompt_parts.append(f"\nAdditional context:\n{context_text}")

        # Add ReAct instructions
        prompt_parts.append(self.executor.get_react_system_prompt())

        return "\n".join(prompt_parts)

    async def _enhanced_llm_call(self, prompt: str) -> str:
        """Enhanced LLM call with context and error handling."""
        try:
            if self.llm_config:
                # Use LiteLLM configuration
                response = await self._call_with_litellm(prompt)
            elif self.llm_function:
                # Use legacy function (backward compatibility)
                response = await self.llm_function(prompt)
            else:
                raise ValueError("No LLM configuration available")

            return response if response else "I don't have a response to that."
        except Exception as e:
            return f"I encountered an error processing your request: {str(e)}"

    async def _call_with_litellm(self, prompt: str) -> str:
        """
        Call LLM using LiteLLM configuration.
        """
        if not self.llm_config:
            raise ValueError("LLM config not available")

        try:
            # Import LiteLLM provider
            from integrations.litellm_provider import LiteLLMProvider

            # Create provider instance
            provider = LiteLLMProvider(self.llm_config)

            # Make the call
            response = await provider.call(prompt)
            return response

        except ImportError:
            # Fallback if LiteLLM is not available
            provider = self.llm_config.get("provider", "unknown")
            model = self.llm_config.get("model", "unknown")
            return f"[LiteLLM unavailable - {provider}/{model}] Response to: {prompt[:50]}..."

        except Exception as e:
            raise RuntimeError(f"LiteLLM call failed: {e}")

    async def _tool_call_wrapper(self, tool_name: str, tool_arguments: Dict[str, Any]) -> str:
        """Wrapper for tool calls through the tool manager."""
        try:
            result = await self.tool_manager.execute_tool_by_name(
                name=tool_name,
                arguments=tool_arguments
            )

            if result.success:
                return str(result.result) if result.result is not None else "Tool executed successfully"
            else:
                return f"Tool error: {result.error}"

        except Exception as e:
            return f"Tool execution failed: {str(e)}"

    async def chat(
        self,
        message: str,
        stream: bool = False
    ) -> Union[str, AsyncIterator[str]]:
        """
        Chat interface for interactive conversations.

        Args:
            message: User message
            stream: Whether to stream the response

        Returns:
            Response string or async iterator for streaming
        """
        if stream:
            # Streaming implementation would go here
            # For now, return non-streaming response
            response = await self.run(message)
            async def stream_response():
                yield response
            return stream_response()
        else:
            return await self.run(message)

    def clone(self, session_id: Optional[str] = None) -> 'CoreAgent':
        """
        Create a clone of this agent with a new session.

        Args:
            session_id: Optional session ID for the clone

        Returns:
            New CoreAgent instance
        """
        clone = CoreAgent(
            llm_function=self.llm_function,
            system_prompt=self.system_prompt,
            max_iterations=self.max_iterations,
            enable_memory=self.memory_manager is not None,
            enable_optimization=self.optimizer is not None,
            session_id=session_id
        )

        # Copy tool manager state (tools remain registered)
        # Note: Tools are shared, MCP connections would need to be re-established

        return clone

    async def export_session(self) -> Dict[str, Any]:
        """Export the current session state."""
        export_data = {
            "session_id": self.session_id,
            "system_prompt": self.system_prompt,
            "max_iterations": self.max_iterations,
            "optimization_history": self.optimization_history,
            "tools": self.tool_manager.export_configuration(),
            "timestamp": datetime.now().isoformat()
        }

        if self.memory_manager:
            export_data["memory_stats"] = await self.memory_manager.get_memory_stats()

        return export_data

    # Pattern execution methods

    async def run_with_pattern(
        self,
        user_input: str,
        pattern: ExecutionPatternType,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Run agent with a specific execution pattern.

        Args:
            user_input: User's input/question
            pattern: Execution pattern to use
            context: Optional additional context

        Returns:
            Agent's response using the specified pattern
        """
        return await self.run(user_input, context, pattern)

    async def run_with_fallback(
        self,
        user_input: str,
        patterns: List[ExecutionPatternType],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Run agent with fallback patterns.

        Args:
            user_input: User's input/question
            patterns: List of patterns to try in order
            context: Optional additional context

        Returns:
            Agent's response from first successful pattern
        """
        enhanced_prompt = await self._build_enhanced_prompt(user_input, context)

        result = await self.pattern_executor.execute_with_fallback(
            user_input=user_input,
            system_prompt=enhanced_prompt,
            patterns=patterns
        )

        # Store in memory if successful
        if self.memory_manager and result.success:
            await self.memory_manager.add_conversation_turn(
                session_id=self.session_id,
                user_input=user_input,
                agent_response=result.final_answer,
                execution_result=result.to_dict()
            )

        return result.final_answer if result.success else f"Error: {result.error_message}"

    def suggest_execution_pattern(self, user_input: str) -> Dict[str, Any]:
        """
        Suggest the best execution pattern for given input.

        Args:
            user_input: User's input/question

        Returns:
            Pattern suggestion with reasoning
        """
        return self.pattern_executor.suggest_pattern(user_input)

    def get_available_patterns(self) -> List[Dict[str, str]]:
        """
        Get list of available execution patterns.

        Returns:
            List of patterns with descriptions
        """
        return self.pattern_executor.get_available_patterns()

    def get_pattern_stats(self) -> Dict[str, Any]:
        """
        Get execution pattern usage statistics.

        Returns:
            Pattern usage and success rate statistics
        """
        return self.pattern_executor.get_pattern_stats()

    def add_pattern_rule(
        self,
        rule_name: str,
        condition: Callable[[str, Optional[Dict[str, Any]]], bool],
        pattern: ExecutionPatternType,
        priority: int = 0
    ) -> None:
        """
        Add a custom pattern selection rule.

        Args:
            rule_name: Name of the rule
            condition: Function that determines when to use this pattern
            pattern: Pattern to use when condition is met
            priority: Rule priority (higher takes precedence)
        """
        self.pattern_executor.add_pattern_rule(rule_name, condition, pattern, priority)

    def set_default_pattern(self, pattern: ExecutionPatternType) -> None:
        """
        Set the default execution pattern.

        Args:
            pattern: New default pattern
        """
        self.execution_pattern = pattern
        self.pattern_executor.default_pattern = pattern

    def enable_automatic_pattern_selection(self, enabled: bool = True) -> None:
        """
        Enable or disable automatic pattern selection.

        Args:
            enabled: Whether to enable automatic selection
        """
        self.enable_pattern_selection = enabled

    async def set_execution_pattern(self, pattern: ExecutionPatternType) -> None:
        """
        Switch to a different execution pattern.

        Args:
            pattern: New execution pattern to use
        """
        self.current_pattern = pattern
        self.execution_pattern = pattern

        # if self.enable_pattern_selection:
        #     add_default_rules(self.pattern_executor)

    async def compare_patterns(
        self,
        user_input: str,
        patterns: List[ExecutionPatternType],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compare different execution patterns on the same input.

        Args:
            user_input: User's input/question
            patterns: List of patterns to compare
            context: Optional additional context

        Returns:
            Comparison results for each pattern
        """
        enhanced_prompt = await self._build_enhanced_prompt(user_input, context)
        results = {}

        for pattern in patterns:
            try:
                result = await self.pattern_executor.execute(
                    user_input=user_input,
                    system_prompt=enhanced_prompt,
                    pattern=pattern
                )

                results[pattern.value] = {
                    "success": result.success,
                    "answer": result.final_answer if result.success else result.error_message,
                    "iterations": result.iterations_used,
                    "execution_time": (result.end_time - result.start_time).total_seconds() if result.end_time and result.start_time else None,
                    "steps_count": len(result.steps) if result.steps else 0
                }

            except Exception as e:
                results[pattern.value] = {
                    "success": False,
                    "error": str(e),
                    "answer": None,
                    "iterations": 0,
                    "execution_time": None,
                    "steps_count": 0
                }

        return {
            "input": user_input,
            "patterns_compared": [p.value for p in patterns],
            "results": results,
            "comparison_timestamp": datetime.now().isoformat()
        }

    async def run_benchmark(self, test_cases: List[str]) -> Dict[str, Any]:
        """
        Simple benchmark: time responses on test cases.
        Constitutional compliance: simple implementation without complex framework.

        Args:
            test_cases: List of test input strings

        Returns:
            Benchmark results with framework name and timing information
        """
        import time

        if not test_cases:
            raise ValueError("test_cases cannot be empty")

        results = []
        for case in test_cases:
            start_time = time.time()
            try:
                response = await self.run(case)
                duration = time.time() - start_time
                results.append({
                    "input": case,
                    "response": response,
                    "time": duration
                })
            except Exception as e:
                duration = time.time() - start_time
                results.append({
                    "input": case,
                    "response": f"Error: {str(e)}",
                    "time": duration
                })

        return {
            "framework": "mini_agent",
            "results": results
        }

    async def add_example(self, input_text: str, output_text: str) -> str:
        """
        Store example in existing memory system for in-context learning.
        Constitutional compliance: reuse existing memory system.

        Args:
            input_text: Example input
            output_text: Example expected output

        Returns:
            Example entry ID
        """
        if not self.memory_manager:
            raise ValueError("Memory manager not available for example storage")

        # Store example as memory with special metadata
        example_content = f"{input_text} -> {output_text}"

        entry_id = await self.memory_manager.store_memory(
            content=example_content,
            importance=1.0,  # High importance for examples
            metadata={"type": "example", "input": input_text, "output": output_text}
        )

        return entry_id

    async def get_examples(self, query: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve stored examples, optionally filtered by query.

        Args:
            query: Optional search query to filter examples
            limit: Maximum number of examples to return

        Returns:
            List of example entries
        """
        if not self.memory_manager:
            return []

        try:
            if query:
                # Search for relevant examples
                memories = await self.memory_manager.search_memory(query, limit=limit * 2)
            else:
                # Get all memories and filter for examples
                memories = await self.memory_manager.search_memory("", limit=limit * 2)

            # Filter for examples only
            examples = [
                mem for mem in memories
                if mem.get("metadata", {}).get("type") == "example"
            ]

            return examples[:limit]

        except Exception:
            return []