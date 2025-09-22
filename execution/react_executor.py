"""Core ReAct execution loop implementation."""

import asyncio
import uuid
from typing import Dict, Any, Optional, List, Callable, Awaitable
from datetime import datetime

from .execution_context import ExecutionContext, ExecutionStep
from .execution_result import ExecutionResult
from .action_parser import ActionParser, ParsedAction
from .thought_formatter import ThoughtFormatter


class ReactExecutor:
    """
    Core ReAct (Reasoning and Acting) execution loop.

    This executor implements the fundamental thought-action-observation cycle
    that drives autonomous agent behavior. It manages the flow between reasoning,
    action selection, action execution, and observation processing.
    """

    def __init__(
        self,
        llm_call: Callable[[str], Awaitable[str]],
        tool_call: Callable[[str, Dict[str, Any]], Awaitable[str]],
        max_iterations: int = 5,
        timeout_seconds: int = 300
    ):
        """
        Initialize the ReAct executor.

        Args:
            llm_call: Async function to call LLM (prompt) -> response
            tool_call: Async function to call tools (name, params) -> result
            max_iterations: Maximum number of ReAct iterations
            timeout_seconds: Maximum execution time
        """
        self.llm_call = llm_call
        self.tool_call = tool_call
        self.max_iterations = max_iterations
        self.timeout_seconds = timeout_seconds

        self.action_parser = ActionParser()
        self.thought_formatter = ThoughtFormatter()

        # Metrics
        self.total_tokens = 0
        self.api_calls = 0
        self.tool_calls = 0

    async def execute(
        self,
        user_input: str,
        system_prompt: str,
        context: Optional[ExecutionContext] = None
    ) -> ExecutionResult:
        """
        Execute the ReAct loop for a given input.

        Args:
            user_input: The user's question or request
            system_prompt: System prompt for the LLM
            context: Optional existing context to continue

        Returns:
            ExecutionResult containing the complete execution trace
        """
        # Initialize or use existing context
        if context is None:
            context = ExecutionContext(
                user_input=user_input,
                system_prompt=system_prompt,
                max_iterations=self.max_iterations,
                session_id=str(uuid.uuid4())
            )

        try:
            # Execute with timeout
            await asyncio.wait_for(
                self._execute_loop(context),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            context.mark_error(f"Execution timed out after {self.timeout_seconds} seconds")
        except Exception as e:
            context.mark_error(f"Execution failed: {str(e)}")

        # Create result
        result = ExecutionResult.from_context(context)
        result.total_tokens = self.total_tokens
        result.api_calls = self.api_calls
        result.tool_calls = self.tool_calls

        return result

    async def _execute_loop(self, context: ExecutionContext) -> None:
        """Execute the main ReAct loop."""
        while not context.is_complete():
            context.current_iteration += 1

            # Generate thought and action
            response = await self._generate_response(context)
            if not response:
                context.mark_error("Failed to generate LLM response")
                break

            # Parse the response
            parsed_action = self.action_parser.parse_action(response)

            if parsed_action:
                # Add step with action
                step = context.add_step(
                    thought=self._extract_thought(response),
                    action=parsed_action.action,
                    action_input=parsed_action.action_input
                )

                # Execute action
                observation = await self._execute_action(
                    parsed_action.action,
                    parsed_action.action_input
                )
                context.update_observation(observation)

            elif self.action_parser.is_final_answer(response):
                # Final answer reached
                final_answer = self.action_parser.extract_final_answer(response)
                if final_answer:
                    context.add_step(thought=self._extract_thought(response))
                    context.mark_complete(final_answer)
                else:
                    context.mark_error("Failed to extract final answer")
                break

            else:
                # No action found - this might be just thinking
                context.add_step(thought=response)
                # Continue to next iteration

            # Check iteration limit
            if context.current_iteration >= context.max_iterations:
                context.mark_error("Maximum iterations reached without final answer")
                break

    async def _generate_response(self, context: ExecutionContext) -> Optional[str]:
        """Generate LLM response for current context."""
        try:
            # Build prompt
            prompt = self._build_prompt(context)

            # Call LLM
            response = await self.llm_call(prompt)
            self.api_calls += 1

            return response.strip() if response else None

        except Exception as e:
            print(f"Error generating LLM response: {e}")
            return None

    async def _execute_action(self, action: str, action_input: Dict[str, Any]) -> str:
        """Execute a tool action and return observation."""
        try:
            # Call tool
            result = await self.tool_call(action, action_input)
            self.tool_calls += 1

            return str(result) if result is not None else "Action completed successfully"

        except Exception as e:
            return f"Error executing action {action}: {str(e)}"

    def _build_prompt(self, context: ExecutionContext) -> str:
        """Build the complete prompt for LLM."""
        parts = [context.system_prompt]

        # Add user input
        parts.append(f"\nUser: {context.user_input}")

        # Add conversation history
        history = context.get_conversation_history()
        if history:
            parts.append(f"\n{history}")

        # Add next step prompt
        if context.current_iteration == 0:
            parts.append("\nPlease begin by thinking about this step by step.")
        else:
            parts.append("\nWhat should I do next?")

        return "\n".join(parts)

    def _extract_thought(self, response: str) -> str:
        """Extract thought portion from LLM response."""
        # Look for "Thought:" prefix
        if "Thought:" in response:
            thought_part = response.split("Thought:", 1)[1]
            # Extract until "Action:" or end
            if "Action:" in thought_part:
                thought_part = thought_part.split("Action:", 1)[0]
            return thought_part.strip()

        # If no "Thought:" found, use the beginning of response
        lines = response.split('\n')
        thought_lines = []
        for line in lines:
            if line.strip().startswith(('Action:', 'Final Answer:')):
                break
            thought_lines.append(line)

        return '\n'.join(thought_lines).strip()

    def get_react_system_prompt(self) -> str:
        """Get the standard ReAct system prompt."""
        return """You are an intelligent agent that can reason and act to solve problems.

Use the following format to structure your responses:

Thought: Your reasoning about what to do next
Action: The action you want to take
Action Input: The input for the action

After you execute an action, you will receive:
Observation: The result of the action

You can then continue with more Thought/Action/Observation cycles until you have enough information to provide a final answer.

When you have enough information to answer the user's question, respond with:
Thought: Your final reasoning
Final Answer: Your complete answer to the user's question

Remember:
- Always start with a "Thought:" to explain your reasoning
- Use "Action:" only when you need to use a tool
- Use "Final Answer:" only when you're ready to give the complete answer
- Be concise but thorough in your thinking
"""

    def reset_metrics(self) -> None:
        """Reset execution metrics."""
        self.total_tokens = 0
        self.api_calls = 0
        self.tool_calls = 0

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get current execution statistics."""
        return {
            "total_tokens": self.total_tokens,
            "api_calls": self.api_calls,
            "tool_calls": self.tool_calls,
            "max_iterations": self.max_iterations,
            "timeout_seconds": self.timeout_seconds
        }