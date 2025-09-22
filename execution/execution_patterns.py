"""
Execution Patterns for Core Agent

This module provides different execution patterns that agents can use to
process information and make decisions. Each pattern represents a different
cognitive approach or reasoning framework.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .execution_context import ExecutionContext
from .execution_result import ExecutionResult


class ExecutionPatternType(Enum):
    """Types of execution patterns."""
    # Core patterns from constitutional compliance requirements
    SIMPLE = "simple"              # Simple direct LLM call
    REACT = "react"               # Reasoning + Acting cycle
    PLANNING = "planning"         # Plan then execute approach
    AUTO = "auto"                # Automatic pattern selection

    # Extended patterns (existing)
    CHAIN_OF_THOUGHT = "chain_of_thought"
    PLAN_AND_EXECUTE = "plan_and_execute"
    REFLECTION = "reflection"
    TREE_OF_THOUGHTS = "tree_of_thoughts"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    CRITICAL = "critical"
    SOCRATIC = "socratic"


@dataclass
class ExecutionStep:
    """Represents a single step in execution."""

    step_type: str
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]
    iteration: int = 0


class ExecutionPattern(ABC):
    """
    Abstract base class for execution patterns.

    Each pattern defines how an agent processes information, makes decisions,
    and formats its reasoning process.
    """

    def __init__(self, pattern_type: ExecutionPatternType, name: str, description: str):
        self.pattern_type = pattern_type
        self.name = name
        self.description = description
        self.steps: List[ExecutionStep] = []
        self.current_iteration = 0

    @abstractmethod
    async def execute(
        self,
        user_input: str,
        llm_call: Callable[[str], Awaitable[str]],
        tool_call: Callable[[str, Dict[str, Any]], Awaitable[str]],
        context: ExecutionContext
    ) -> ExecutionResult:
        """
        Execute the pattern with given input and context.

        Args:
            user_input: User's input/question
            llm_call: Function to call LLM
            tool_call: Function to call tools
            context: Execution context

        Returns:
            Execution result with final answer and steps
        """
        pass

    @abstractmethod
    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response according to this pattern.

        Args:
            response: Raw LLM response

        Returns:
            Parsed response components
        """
        pass

    @abstractmethod
    def should_continue(self, parsed_response: Dict[str, Any]) -> bool:
        """
        Determine if execution should continue.

        Args:
            parsed_response: Parsed LLM response

        Returns:
            True if should continue, False otherwise
        """
        pass

    @abstractmethod
    def format_intermediate_steps(self) -> str:
        """
        Format intermediate steps for context.

        Returns:
            Formatted steps as string
        """
        pass

    def add_step(self, step_type: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a step to the execution history."""
        step = ExecutionStep(
            step_type=step_type,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {},
            iteration=self.current_iteration
        )
        self.steps.append(step)

    def get_system_prompt(self) -> str:
        """Get system prompt for this pattern."""
        return f"""
You are following the {self.name} execution pattern.

Pattern Description: {self.description}

Follow this pattern strictly in your responses.
"""

    def clear_steps(self) -> None:
        """Clear execution steps."""
        self.steps.clear()
        self.current_iteration = 0


class ReActPattern(ExecutionPattern):
    """ReAct (Reasoning and Acting) execution pattern."""

    def __init__(self):
        super().__init__(
            pattern_type=ExecutionPatternType.REACT,
            name="ReAct (Reasoning and Acting)",
            description="Think step by step, then take actions. Format: Thought -> Action -> Observation -> repeat until Final Answer."
        )

    async def execute(
        self,
        user_input: str,
        llm_call: Callable[[str], Awaitable[str]],
        tool_call: Callable[[str, Dict[str, Any]], Awaitable[str]],
        context: ExecutionContext
    ) -> ExecutionResult:
        """Execute ReAct pattern."""
        self.clear_steps()

        # Build initial prompt
        system_prompt = self.get_system_prompt()
        formatted_prompt = f"""{system_prompt}

You can use the following format:
Thought: [your reasoning about what to do next]
Action: [the action to take]
Action Input: [the input to the action]
Observation: [the result of the action]
... (repeat Thought/Action/Observation as needed)
Final Answer: [your final answer to the user]

Question: {user_input}"""

        max_iterations = context.max_iterations

        for iteration in range(max_iterations):
            self.current_iteration = iteration + 1

            # Get LLM response
            response = await llm_call(formatted_prompt)
            self.add_step("llm_response", response)

            # Parse response
            parsed = self.parse_llm_response(response)

            # Check if we have a final answer
            if not self.should_continue(parsed):
                final_answer = parsed.get("final_answer", "I couldn't determine a final answer.")
                return ExecutionResult(
                    final_answer=final_answer,
                    success=True,
                    steps_taken=len(self.steps),
                    execution_time=0.0,
                    iterations_used=iteration + 1,
                    execution_steps=self.steps.copy(),
                    context=context
                )

            # Execute action if present
            if "action" in parsed and "action_input" in parsed:
                try:
                    # Parse action input
                    import json
                    action_input = json.loads(parsed["action_input"]) if isinstance(parsed["action_input"], str) else parsed["action_input"]

                    # Execute tool
                    observation = await tool_call(parsed["action"], action_input)
                    self.add_step("observation", observation)

                    # Add observation to prompt for next iteration
                    formatted_prompt += f"\nObservation: {observation}\n"

                except Exception as e:
                    observation = f"Error executing action: {str(e)}"
                    self.add_step("observation", observation)
                    formatted_prompt += f"\nObservation: {observation}\n"

        # Max iterations reached
        return ExecutionResult(
            final_answer="",
            success=False,
            steps_taken=len(self.steps),
            execution_time=0.0,
            iterations_used=max_iterations,
            execution_steps=self.steps.copy(),
            context=context,
            error_message="Maximum iterations reached without finding final answer"
        )

    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse ReAct formatted response."""
        parsed = {}
        lines = response.strip().split('\n')

        current_key = None
        current_value = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for thought pattern
            if line.startswith("Thought:"):
                if current_key and current_value:
                    parsed[current_key] = '\n'.join(current_value).strip()
                current_key = "thought"
                current_value = [line[len("Thought:"):].strip()]

            # Check for action pattern
            elif line.startswith("Action:"):
                if current_key and current_value:
                    parsed[current_key] = '\n'.join(current_value).strip()
                current_key = "action"
                current_value = [line[len("Action:"):].strip()]

            # Check for action input pattern
            elif line.startswith("Action Input:"):
                if current_key and current_value:
                    parsed[current_key] = '\n'.join(current_value).strip()
                current_key = "action_input"
                current_value = [line[len("Action Input:"):].strip()]

            # Check for final answer pattern
            elif line.startswith("Final Answer:"):
                if current_key and current_value:
                    parsed[current_key] = '\n'.join(current_value).strip()
                current_key = "final_answer"
                current_value = [line[len("Final Answer:"):].strip()]

            # Continue building current value
            else:
                if current_key:
                    current_value.append(line)

        # Add the last key-value pair
        if current_key and current_value:
            parsed[current_key] = '\n'.join(current_value).strip()

        return parsed

    def should_continue(self, parsed_response: Dict[str, Any]) -> bool:
        """Continue if there's an action but no final answer."""
        return "action" in parsed_response and "final_answer" not in parsed_response

    def format_intermediate_steps(self) -> str:
        """Format ReAct steps."""
        formatted = []
        for step in self.steps:
            if step.step_type == "llm_response":
                # Parse and format the response
                parsed = self.parse_llm_response(step.content)
                if "thought" in parsed:
                    formatted.append(f"Thought: {parsed['thought']}")
                if "action" in parsed:
                    formatted.append(f"Action: {parsed['action']}")
                if "action_input" in parsed:
                    formatted.append(f"Action Input: {parsed['action_input']}")
            elif step.step_type == "observation":
                formatted.append(f"Observation: {step.content}")

        return "\n".join(formatted)


class ChainOfThoughtPattern(ExecutionPattern):
    """Chain of Thought execution pattern."""

    def __init__(self):
        super().__init__(
            pattern_type=ExecutionPatternType.CHAIN_OF_THOUGHT,
            name="Chain of Thought",
            description="Break down complex problems into logical steps and reason through each step sequentially."
        )

    async def execute(
        self,
        user_input: str,
        llm_call: Callable[[str], Awaitable[str]],
        tool_call: Callable[[str, Dict[str, Any]], Awaitable[str]],
        context: ExecutionContext
    ) -> ExecutionResult:
        """Execute Chain of Thought pattern."""
        self.clear_steps()

        system_prompt = self.get_system_prompt()
        formatted_prompt = f"""{system_prompt}

Think through this step by step:

1. First, understand what is being asked
2. Break down the problem into logical steps
3. Work through each step carefully
4. Show your reasoning for each step
5. Arrive at a final answer

Question: {user_input}

Let me think step by step:"""

        response = await llm_call(formatted_prompt)
        self.add_step("reasoning", response)

        return ExecutionResult(
            final_answer=response,
            success=True,
            steps_taken=len(self.steps),
            execution_time=0.0,
            iterations_used=1,
            execution_steps=self.steps.copy(),
            context=context
        )

    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse Chain of Thought response."""
        return {"reasoning": response, "final_answer": response}

    def should_continue(self, parsed_response: Dict[str, Any]) -> bool:
        """Chain of Thought typically completes in one step."""
        return False

    def format_intermediate_steps(self) -> str:
        """Format Chain of Thought steps."""
        if self.steps:
            return self.steps[0].content
        return ""


class PlanAndExecutePattern(ExecutionPattern):
    """Plan and Execute execution pattern."""

    def __init__(self):
        super().__init__(
            pattern_type=ExecutionPatternType.PLAN_AND_EXECUTE,
            name="Plan and Execute",
            description="First create a detailed plan, then execute each step of the plan systematically."
        )

    async def execute(
        self,
        user_input: str,
        llm_call: Callable[[str], Awaitable[str]],
        tool_call: Callable[[str, Dict[str, Any]], Awaitable[str]],
        context: ExecutionContext
    ) -> ExecutionResult:
        """Execute Plan and Execute pattern."""
        self.clear_steps()

        # Phase 1: Planning
        planning_prompt = f"""{self.get_system_prompt()}

Create a detailed plan to answer this question: {user_input}

Break it down into specific, actionable steps. Format your plan as:
Step 1: [description]
Step 2: [description]
...

Plan:"""

        plan_response = await llm_call(planning_prompt)
        self.add_step("plan", plan_response)

        # Phase 2: Execution
        execution_prompt = f"""Now execute the plan step by step:

Plan:
{plan_response}

Question: {user_input}

Execute each step and provide your reasoning:"""

        execution_response = await llm_call(execution_prompt)
        self.add_step("execution", execution_response)

        return ExecutionResult(
            final_answer=execution_response,
            success=True,
            steps_taken=len(self.steps),
            execution_time=0.0,
            iterations_used=2,
            execution_steps=self.steps.copy(),
            context=context
        )

    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse Plan and Execute response."""
        return {"response": response}

    def should_continue(self, parsed_response: Dict[str, Any]) -> bool:
        """Plan and Execute has fixed phases."""
        return False

    def format_intermediate_steps(self) -> str:
        """Format Plan and Execute steps."""
        formatted = []
        for step in self.steps:
            formatted.append(f"{step.step_type.title()}:\n{step.content}\n")
        return "\n".join(formatted)


class ReflectionPattern(ExecutionPattern):
    """Reflection execution pattern that includes self-critique."""

    def __init__(self):
        super().__init__(
            pattern_type=ExecutionPatternType.REFLECTION,
            name="Reflection",
            description="Provide an initial answer, reflect on it critically, then provide an improved final answer."
        )

    async def execute(
        self,
        user_input: str,
        llm_call: Callable[[str], Awaitable[str]],
        tool_call: Callable[[str, Dict[str, Any]], Awaitable[str]],
        context: ExecutionContext
    ) -> ExecutionResult:
        """Execute Reflection pattern."""
        self.clear_steps()

        # Phase 1: Initial Answer
        initial_prompt = f"""{self.get_system_prompt()}

Question: {user_input}

Provide your initial answer:"""

        initial_response = await llm_call(initial_prompt)
        self.add_step("initial_answer", initial_response)

        # Phase 2: Reflection
        reflection_prompt = f"""Now reflect critically on your initial answer:

Question: {user_input}
Initial Answer: {initial_response}

Critically evaluate your initial answer:
- What assumptions did you make?
- What could be wrong or incomplete?
- What alternative perspectives should be considered?
- How could the answer be improved?

Reflection:"""

        reflection_response = await llm_call(reflection_prompt)
        self.add_step("reflection", reflection_response)

        # Phase 3: Final Answer
        final_prompt = f"""Based on your reflection, provide an improved final answer:

Question: {user_input}
Initial Answer: {initial_response}
Reflection: {reflection_response}

Improved Final Answer:"""

        final_response = await llm_call(final_prompt)
        self.add_step("final_answer", final_response)

        return ExecutionResult(
            final_answer=final_response,
            success=True,
            steps_taken=len(self.steps),
            execution_time=0.0,
            iterations_used=3,
            execution_steps=self.steps.copy(),
            context=context
        )

    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse Reflection response."""
        return {"response": response}

    def should_continue(self, parsed_response: Dict[str, Any]) -> bool:
        """Reflection has fixed phases."""
        return False

    def format_intermediate_steps(self) -> str:
        """Format Reflection steps."""
        formatted = []
        for step in self.steps:
            formatted.append(f"{step.step_type.replace('_', ' ').title()}:\n{step.content}\n")
        return "\n".join(formatted)


class SocraticPattern(ExecutionPattern):
    """Socratic questioning execution pattern."""

    def __init__(self):
        super().__init__(
            pattern_type=ExecutionPatternType.SOCRATIC,
            name="Socratic Questioning",
            description="Explore the question through systematic inquiry, asking deeper questions to uncover understanding."
        )

    async def execute(
        self,
        user_input: str,
        llm_call: Callable[[str], Awaitable[str]],
        tool_call: Callable[[str, Dict[str, Any]], Awaitable[str]],
        context: ExecutionContext
    ) -> ExecutionResult:
        """Execute Socratic pattern."""
        self.clear_steps()

        socratic_prompt = f"""{self.get_system_prompt()}

Question: {user_input}

Explore this question through Socratic inquiry:

1. What exactly is being asked here?
2. What do we already know about this topic?
3. What assumptions are we making?
4. What are the key concepts involved?
5. How do these concepts relate to each other?
6. What evidence supports our understanding?
7. What questions does this raise?
8. How might someone disagree with this?
9. What are the implications of this?
10. What is the essence of this question?

Work through these systematically:"""

        response = await llm_call(socratic_prompt)
        self.add_step("socratic_inquiry", response)

        return ExecutionResult(
            final_answer=response,
            success=True,
            steps_taken=len(self.steps),
            execution_time=0.0,
            iterations_used=1,
            execution_steps=self.steps.copy(),
            context=context
        )

    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse Socratic response."""
        return {"inquiry": response}

    def should_continue(self, parsed_response: Dict[str, Any]) -> bool:
        """Socratic inquiry typically completes in one step."""
        return False

    def format_intermediate_steps(self) -> str:
        """Format Socratic steps."""
        if self.steps:
            return self.steps[0].content
        return ""


class ExecutionPatternFactory:
    """Factory for creating execution patterns."""

    _patterns = {
        ExecutionPatternType.REACT: ReActPattern,
        ExecutionPatternType.CHAIN_OF_THOUGHT: ChainOfThoughtPattern,
        ExecutionPatternType.PLAN_AND_EXECUTE: PlanAndExecutePattern,
        ExecutionPatternType.REFLECTION: ReflectionPattern,
        ExecutionPatternType.SOCRATIC: SocraticPattern,
    }

    @classmethod
    def create_pattern(cls, pattern_type: ExecutionPatternType) -> ExecutionPattern:
        """Create an execution pattern instance."""
        pattern_class = cls._patterns.get(pattern_type)

        if not pattern_class:
            raise ValueError(f"Unknown execution pattern: {pattern_type}")

        return pattern_class()

    @classmethod
    def register_pattern(cls, pattern_type: ExecutionPatternType, pattern_class: type) -> None:
        """Register a new execution pattern."""
        cls._patterns[pattern_type] = pattern_class

    @classmethod
    def list_patterns(cls) -> List[ExecutionPatternType]:
        """List available execution patterns."""
        return list(cls._patterns.keys())

    @classmethod
    def get_pattern_descriptions(cls) -> Dict[str, str]:
        """Get descriptions of all patterns."""
        descriptions = {}
        for pattern_type in cls._patterns:
            pattern = cls.create_pattern(pattern_type)
            descriptions[pattern_type.value] = pattern.description
        return descriptions