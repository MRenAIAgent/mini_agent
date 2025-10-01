"""
Pattern-based execution engine for the core agent.

This module provides a flexible execution engine that can use different
execution patterns (ReAct, Chain of Thought, Plan and Execute, etc.)
based on the task requirements or user preferences.
"""

import asyncio
import uuid
from typing import Dict, Any, Optional, List, Callable, Awaitable, Union
from datetime import datetime

from .execution_context import ExecutionContext
from .execution_result import ExecutionResult
from .execution_patterns import (
    ExecutionPattern, ExecutionPatternType, ExecutionPatternFactory
)


class PatternExecutor:
    """
    Advanced executor that supports multiple execution patterns.

    This executor can dynamically choose or be configured to use different
    execution patterns based on task complexity, user preferences, or
    performance requirements.
    """

    def __init__(
        self,
        llm_call: Callable[[str], Awaitable[str]],
        tool_call: Callable[[str, Dict[str, Any]], Awaitable[str]],
        default_pattern: ExecutionPatternType = ExecutionPatternType.REACT,
        max_iterations: int = 5,
        timeout_seconds: int = 300
    ):
        """
        Initialize the pattern executor.

        Args:
            llm_call: Async function to call LLM
            tool_call: Async function to call tools
            default_pattern: Default execution pattern to use
            max_iterations: Maximum iterations per execution
            timeout_seconds: Maximum execution time
        """
        self.llm_call = llm_call
        self.tool_call = tool_call
        self.default_pattern = default_pattern
        self.max_iterations = max_iterations
        self.timeout_seconds = timeout_seconds

        # Pattern selection rules
        self.pattern_rules: List[Dict[str, Any]] = []

        # Execution statistics
        self.pattern_usage: Dict[str, int] = {}
        self.pattern_success_rates: Dict[str, List[bool]] = {}

    async def execute(
        self,
        user_input: str,
        system_prompt: str,
        context: Optional[ExecutionContext] = None,
        pattern: Optional[ExecutionPatternType] = None,
        pattern_params: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Execute using specified or automatically selected pattern.

        Args:
            user_input: User's input/question
            system_prompt: System prompt for the LLM
            context: Optional existing execution context
            pattern: Specific pattern to use (overrides automatic selection)
            pattern_params: Optional parameters for the pattern

        Returns:
            ExecutionResult with pattern execution details
        """
        # Select execution pattern
        selected_pattern = pattern or self._select_pattern(user_input, pattern_params)
        print(f"🎯 [EXECUTOR] Selected execution pattern: {selected_pattern.value}")

        # Create execution context
        if context is None:
            context = ExecutionContext(
                user_input=user_input,
                system_prompt=system_prompt,
                max_iterations=self.max_iterations,
                session_id=str(uuid.uuid4())
            )

        # Add pattern info to context
        context.metadata["execution_pattern"] = selected_pattern.value
        context.metadata["pattern_params"] = pattern_params or {}

        # Create pattern instance
        pattern_instance = ExecutionPatternFactory.create_pattern(selected_pattern)
        print(f"🏗️ [EXECUTOR] Created pattern instance: {pattern_instance.__class__.__name__}")

        try:
            print(f"⏱️ [EXECUTOR] Starting execution (timeout: {self.timeout_seconds}s)")
            # Execute with timeout
            result = await asyncio.wait_for(
                pattern_instance.execute(
                    user_input=user_input,
                    llm_call=self.llm_call,
                    tool_call=self.tool_call,
                    context=context
                ),
                timeout=self.timeout_seconds
            )
            print(f"🎉 [EXECUTOR] Pattern execution completed successfully")

            # Update statistics
            self._update_pattern_stats(selected_pattern, True)

            # Add pattern information to result
            result.metadata["execution_pattern"] = selected_pattern.value
            result.metadata["pattern_steps"] = len(pattern_instance.steps)

            return result

        except asyncio.TimeoutError:
            self._update_pattern_stats(selected_pattern, False)
            return ExecutionResult(
                final_answer="",
                success=False,
                steps_taken=0,
                execution_time=self.timeout_seconds,
                iterations_used=0,
                execution_steps=[],
                context=context,
                error_message=f"Pattern execution timed out after {self.timeout_seconds} seconds",
                metadata={"execution_pattern": selected_pattern.value}
            )

        except Exception as e:
            self._update_pattern_stats(selected_pattern, False)
            return ExecutionResult(
                final_answer="",
                success=False,
                steps_taken=0,
                execution_time=0.0,
                iterations_used=0,
                execution_steps=[],
                context=context,
                error_message=f"Pattern execution failed: {str(e)}",
                metadata={"execution_pattern": selected_pattern.value}
            )

    async def execute_with_fallback(
        self,
        user_input: str,
        system_prompt: str,
        patterns: List[ExecutionPatternType],
        context: Optional[ExecutionContext] = None
    ) -> ExecutionResult:
        """
        Execute with fallback patterns if the primary pattern fails.

        Args:
            user_input: User's input/question
            system_prompt: System prompt for the LLM
            patterns: List of patterns to try in order
            context: Optional existing execution context

        Returns:
            ExecutionResult from the first successful pattern
        """
        last_error = None

        for pattern in patterns:
            try:
                result = await self.execute(
                    user_input=user_input,
                    system_prompt=system_prompt,
                    context=context,
                    pattern=pattern
                )

                if result.success:
                    result.metadata["fallback_attempts"] = patterns.index(pattern) + 1
                    result.metadata["patterns_tried"] = [p.value for p in patterns[:patterns.index(pattern) + 1]]
                    return result

                last_error = result.error_message

            except Exception as e:
                last_error = str(e)
                continue

        # All patterns failed
        return ExecutionResult(
            final_answer="",
            success=False,
            steps_taken=0,
            execution_time=0.0,
            iterations_used=0,
            execution_steps=[],
            context=context or ExecutionContext(
                user_input=user_input,
                system_prompt=system_prompt,
                max_iterations=self.max_iterations,
                session_id=str(uuid.uuid4())
            ),
            error_message=f"All fallback patterns failed. Last error: {last_error}",
            metadata={
                "patterns_tried": [p.value for p in patterns],
                "fallback_failed": True
            }
        )

    def add_pattern_rule(
        self,
        rule_name: str,
        condition: Callable[[str, Optional[Dict[str, Any]]], bool],
        pattern: ExecutionPatternType,
        priority: int = 0
    ) -> None:
        """
        Add a rule for automatic pattern selection.

        Args:
            rule_name: Name of the rule
            condition: Function that takes user_input and params, returns bool
            pattern: Pattern to use if condition is true
            priority: Rule priority (higher numbers take precedence)
        """
        self.pattern_rules.append({
            "name": rule_name,
            "condition": condition,
            "pattern": pattern,
            "priority": priority
        })

        # Sort rules by priority
        self.pattern_rules.sort(key=lambda x: x["priority"], reverse=True)

    def _select_pattern(
        self,
        user_input: str,
        pattern_params: Optional[Dict[str, Any]] = None
    ) -> ExecutionPatternType:
        """
        Automatically select the best execution pattern.

        Args:
            user_input: User's input
            pattern_params: Optional parameters

        Returns:
            Selected execution pattern
        """
        # Check rules in priority order
        for rule in self.pattern_rules:
            try:
                if rule["condition"](user_input, pattern_params):
                    return rule["pattern"]
            except Exception:
                # Skip rules that fail
                continue

        # Heuristic selection based on input characteristics
        user_lower = user_input.lower()

        # Complex reasoning tasks
        if any(keyword in user_lower for keyword in [
            "step by step", "explain", "why", "how does", "analyze",
            "break down", "reasoning", "think through"
        ]):
            return ExecutionPatternType.CHAIN_OF_THOUGHT

        # Planning tasks
        if any(keyword in user_lower for keyword in [
            "plan", "strategy", "approach", "steps to", "how to",
            "create a plan", "organize", "structure"
        ]):
            return ExecutionPatternType.PLAN_AND_EXECUTE

        # Critical evaluation tasks
        if any(keyword in user_lower for keyword in [
            "evaluate", "critique", "assess", "judge", "review",
            "pros and cons", "strengths and weaknesses"
        ]):
            return ExecutionPatternType.REFLECTION

        # Philosophical or deep inquiry tasks
        if any(keyword in user_lower for keyword in [
            "what is", "define", "meaning", "essence", "fundamental",
            "philosophical", "explore the concept"
        ]):
            return ExecutionPatternType.SOCRATIC

        # Tool-requiring tasks (actions, calculations, searches)
        if any(keyword in user_lower for keyword in [
            "calculate", "search", "find", "get", "fetch", "call",
            "execute", "run", "compute", "look up"
        ]):
            return ExecutionPatternType.REACT

        # Default to ReAct for general tasks
        return self.default_pattern

    def _update_pattern_stats(self, pattern: ExecutionPatternType, success: bool) -> None:
        """Update pattern usage statistics."""
        pattern_name = pattern.value

        # Update usage count
        self.pattern_usage[pattern_name] = self.pattern_usage.get(pattern_name, 0) + 1

        # Update success rate
        if pattern_name not in self.pattern_success_rates:
            self.pattern_success_rates[pattern_name] = []

        self.pattern_success_rates[pattern_name].append(success)

        # Keep only recent results (last 100)
        if len(self.pattern_success_rates[pattern_name]) > 100:
            self.pattern_success_rates[pattern_name] = self.pattern_success_rates[pattern_name][-100:]

    def get_pattern_stats(self) -> Dict[str, Any]:
        """Get execution pattern statistics."""
        stats = {
            "pattern_usage": self.pattern_usage.copy(),
            "pattern_success_rates": {},
            "total_executions": sum(self.pattern_usage.values()),
            "available_patterns": [p.value for p in ExecutionPatternFactory.list_patterns()]
        }

        # Calculate success rates
        for pattern_name, results in self.pattern_success_rates.items():
            if results:
                success_rate = sum(results) / len(results) * 100
                stats["pattern_success_rates"][pattern_name] = {
                    "success_rate": success_rate,
                    "total_attempts": len(results),
                    "recent_successes": sum(results[-10:]) if len(results) >= 10 else sum(results)
                }

        return stats

    def suggest_pattern(self, user_input: str) -> Dict[str, Any]:
        """
        Suggest the best pattern for a given input with reasoning.

        Args:
            user_input: User's input

        Returns:
            Dictionary with suggested pattern and reasoning
        """
        selected = self._select_pattern(user_input)
        pattern_instance = ExecutionPatternFactory.create_pattern(selected)

        # Get pattern statistics
        pattern_stats = self.get_pattern_stats()
        pattern_name = selected.value

        success_info = pattern_stats["pattern_success_rates"].get(pattern_name, {})

        return {
            "suggested_pattern": pattern_name,
            "pattern_description": pattern_instance.description,
            "selection_reasoning": self._get_selection_reasoning(user_input, selected),
            "success_rate": success_info.get("success_rate", "No data"),
            "usage_count": self.pattern_usage.get(pattern_name, 0),
            "alternatives": self._get_alternative_patterns(user_input)
        }

    def _get_selection_reasoning(self, user_input: str, pattern: ExecutionPatternType) -> str:
        """Get reasoning for pattern selection."""
        user_lower = user_input.lower()

        if pattern == ExecutionPatternType.CHAIN_OF_THOUGHT:
            return "Input suggests need for step-by-step reasoning and explanation"
        elif pattern == ExecutionPatternType.PLAN_AND_EXECUTE:
            return "Input appears to be a planning or multi-step task"
        elif pattern == ExecutionPatternType.REFLECTION:
            return "Input requires critical evaluation or assessment"
        elif pattern == ExecutionPatternType.SOCRATIC:
            return "Input is philosophical or requires deep conceptual exploration"
        elif pattern == ExecutionPatternType.REACT:
            return "Input likely requires tool usage or external actions"
        else:
            return "Default pattern selection based on general task characteristics"

    def _get_alternative_patterns(self, user_input: str) -> List[Dict[str, str]]:
        """Get alternative patterns that might work for the input."""
        alternatives = []

        # Get all patterns except the selected one
        selected = self._select_pattern(user_input)
        all_patterns = ExecutionPatternFactory.list_patterns()

        for pattern_type in all_patterns:
            if pattern_type != selected:
                pattern_instance = ExecutionPatternFactory.create_pattern(pattern_type)
                alternatives.append({
                    "pattern": pattern_type.value,
                    "description": pattern_instance.description
                })

        return alternatives[:3]  # Return top 3 alternatives

    def reset_stats(self) -> None:
        """Reset all pattern statistics."""
        self.pattern_usage.clear()
        self.pattern_success_rates.clear()

    def get_available_patterns(self) -> List[Dict[str, str]]:
        """Get list of all available patterns with descriptions."""
        patterns = []
        for pattern_type in ExecutionPatternFactory.list_patterns():
            pattern_instance = ExecutionPatternFactory.create_pattern(pattern_type)
            patterns.append({
                "type": pattern_type.value,
                "name": pattern_instance.name,
                "description": pattern_instance.description
            })
        return patterns

    # Simple execution methods (constitutional compliance - extend existing file)
    async def execute_simple(self, context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute simple pattern: direct LLM call.
        Constitutional compliance: simplified implementation.
        """
        user_input = context.get("user_input", "")
        if not user_input:
            return ExecutionResult(
                final_answer="",
                success=False,
                steps_taken=0,
                execution_time=0.0,
                iterations_used=0,
                execution_steps=[],
                context=ExecutionContext(user_input="", system_prompt=""),
                error_message="No user input provided"
            )

        # Simple direct call
        try:
            prompt = f"User: {user_input}\nAssistant:"
            response = await self.llm_call(prompt)
            return ExecutionResult(
                final_answer=response,
                success=True,
                steps_taken=1,
                execution_time=0.0,
                iterations_used=1,
                execution_steps=[],
                context=ExecutionContext(user_input=user_input, system_prompt=""),
                metadata={"pattern": "simple"}
            )
        except Exception as e:
            return ExecutionResult(
                final_answer="",
                success=False,
                steps_taken=0,
                execution_time=0.0,
                iterations_used=0,
                execution_steps=[],
                context=ExecutionContext(user_input=user_input, system_prompt=""),
                error_message=str(e)
            )

    async def execute_react(self, context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute ReAct pattern: reasoning and acting cycle.
        Constitutional compliance: simplified implementation.
        """
        # Delegate to existing ReAct implementation
        user_input = context.get("user_input", "")
        system_prompt = context.get("system_prompt", "")

        # Use existing pattern factory for ReAct
        try:
            pattern_instance = ExecutionPatternFactory.create_pattern(ExecutionPatternType.REACT)
            exec_context = ExecutionContext(
                user_input=user_input,
                system_prompt=system_prompt,
                max_iterations=self.max_iterations
            )

            result = await pattern_instance.execute(
                user_input=user_input,
                llm_call=self.llm_call,
                tool_call=self.tool_call,
                context=exec_context
            )
            return result
        except Exception as e:
            return ExecutionResult(
                final_answer="",
                success=False,
                steps_taken=0,
                execution_time=0.0,
                iterations_used=0,
                execution_steps=[],
                context=ExecutionContext(user_input=user_input, system_prompt=system_prompt),
                error_message=str(e)
            )

    async def execute_planning(self, context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute planning pattern: plan then execute.
        Constitutional compliance: simplified implementation.
        """
        user_input = context.get("user_input", "")

        try:
            # Step 1: Create plan
            plan_prompt = f"Create a step-by-step plan for: {user_input}\nPlan:"
            plan = await self.llm_call(plan_prompt)

            # Step 2: Execute plan
            execute_prompt = f"Plan: {plan}\n\nExecute this plan for: {user_input}\nResult:"
            result = await self.llm_call(execute_prompt)

            return ExecutionResult(
                final_answer=result,
                success=True,
                steps_taken=2,
                execution_time=0.0,
                iterations_used=2,
                execution_steps=[],
                context=ExecutionContext(user_input=user_input, system_prompt=""),
                metadata={"pattern": "planning", "plan": plan}
            )
        except Exception as e:
            return ExecutionResult(
                final_answer="",
                success=False,
                steps_taken=0,
                execution_time=0.0,
                iterations_used=0,
                execution_steps=[],
                context=ExecutionContext(user_input=user_input, system_prompt=""),
                error_message=str(e)
            )

    async def execute_auto(self, context: Dict[str, Any]) -> ExecutionResult:
        """
        Execute auto pattern: automatically select best pattern.
        Constitutional compliance: simplified implementation.
        """
        user_input = context.get("user_input", "")

        # Simple heuristics for pattern selection
        if len(user_input.split()) < 5:
            # Short queries use simple pattern
            return await self.execute_simple(context)
        elif any(word in user_input.lower() for word in ["plan", "steps", "how to"]):
            # Planning queries use planning pattern
            return await self.execute_planning(context)
        else:
            # Default to ReAct for complex queries
            return await self.execute_react(context)


# Default pattern selection rules
def add_default_rules(executor: PatternExecutor) -> None:
    """Add default pattern selection rules to executor."""

    # Math and calculation tasks
    def is_math_task(user_input: str, params: Optional[Dict[str, Any]]) -> bool:
        math_keywords = ["calculate", "compute", "solve", "equation", "math", "arithmetic"]
        return any(keyword in user_input.lower() for keyword in math_keywords)

    executor.add_pattern_rule(
        "math_tasks",
        is_math_task,
        ExecutionPatternType.REACT,
        priority=10
    )

    # Creative tasks
    def is_creative_task(user_input: str, params: Optional[Dict[str, Any]]) -> bool:
        creative_keywords = ["create", "write", "compose", "design", "invent", "brainstorm"]
        return any(keyword in user_input.lower() for keyword in creative_keywords)

    executor.add_pattern_rule(
        "creative_tasks",
        is_creative_task,
        ExecutionPatternType.CHAIN_OF_THOUGHT,
        priority=8
    )

    # Complex analysis tasks
    def is_analysis_task(user_input: str, params: Optional[Dict[str, Any]]) -> bool:
        analysis_keywords = ["analyze", "compare", "contrast", "evaluate", "assess"]
        return any(keyword in user_input.lower() for keyword in analysis_keywords)

    executor.add_pattern_rule(
        "analysis_tasks",
        is_analysis_task,
        ExecutionPatternType.REFLECTION,
        priority=7
    )