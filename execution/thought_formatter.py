"""Formatter for structuring agent thoughts and reasoning."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ThoughtStructure:
    """Structure for organizing agent thoughts."""

    observation: str = ""
    analysis: str = ""
    reasoning: str = ""
    conclusion: str = ""
    next_action: str = ""


class ThoughtFormatter:
    """Formatter for structuring and organizing agent thoughts."""

    def __init__(self):
        self.react_template = """Thought: {thought}
Action: {action}
Action Input: {action_input}"""

        self.structured_template = """Thought: Let me analyze this step by step.

Observation: {observation}
Analysis: {analysis}
Reasoning: {reasoning}
Conclusion: {conclusion}

Action: {action}
Action Input: {action_input}"""

    def format_react_step(
        self,
        thought: str,
        action: str = None,
        action_input: Dict[str, Any] = None
    ) -> str:
        """Format a basic ReAct step."""
        if action is None:
            return f"Thought: {thought}"

        formatted_input = self._format_action_input(action_input)

        return self.react_template.format(
            thought=thought,
            action=action,
            action_input=formatted_input
        )

    def format_structured_thought(
        self,
        observation: str,
        analysis: str,
        reasoning: str,
        conclusion: str,
        action: str = None,
        action_input: Dict[str, Any] = None
    ) -> str:
        """Format a structured thought with detailed reasoning."""
        if action is None:
            return f"""Thought: Let me analyze this step by step.

Observation: {observation}
Analysis: {analysis}
Reasoning: {reasoning}
Conclusion: {conclusion}"""

        formatted_input = self._format_action_input(action_input)

        return self.structured_template.format(
            observation=observation,
            analysis=analysis,
            reasoning=reasoning,
            conclusion=conclusion,
            action=action,
            action_input=formatted_input
        )

    def format_final_answer(self, answer: str, reasoning: str = None) -> str:
        """Format a final answer with optional reasoning."""
        if reasoning:
            return f"""Thought: I now have enough information to provide a final answer.

{reasoning}

Final Answer: {answer}"""
        else:
            return f"""Thought: I can now provide the final answer.

Final Answer: {answer}"""

    def format_error_recovery(self, error: str, recovery_plan: str) -> str:
        """Format error recovery reasoning."""
        return f"""Thought: I encountered an error that I need to handle.

Error: {error}
Recovery Plan: {recovery_plan}

Let me try a different approach."""

    def format_context_summary(
        self,
        user_input: str,
        current_progress: str,
        next_steps: List[str]
    ) -> str:
        """Format a context summary for complex tasks."""
        next_steps_text = "\n".join(f"- {step}" for step in next_steps)

        return f"""Thought: Let me summarize the current situation and plan next steps.

User Request: {user_input}
Current Progress: {current_progress}
Next Steps:
{next_steps_text}

I'll proceed with the first step."""

    def extract_thought_components(self, thought_text: str) -> ThoughtStructure:
        """Extract structured components from thought text."""
        structure = ThoughtStructure()

        # Simple extraction based on keywords
        lines = thought_text.split('\n')
        current_component = None
        current_text = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for component headers
            if line.lower().startswith('observation:'):
                if current_component:
                    setattr(structure, current_component, '\n'.join(current_text))
                current_component = 'observation'
                current_text = [line.split(':', 1)[1].strip()]
            elif line.lower().startswith('analysis:'):
                if current_component:
                    setattr(structure, current_component, '\n'.join(current_text))
                current_component = 'analysis'
                current_text = [line.split(':', 1)[1].strip()]
            elif line.lower().startswith('reasoning:'):
                if current_component:
                    setattr(structure, current_component, '\n'.join(current_text))
                current_component = 'reasoning'
                current_text = [line.split(':', 1)[1].strip()]
            elif line.lower().startswith('conclusion:'):
                if current_component:
                    setattr(structure, current_component, '\n'.join(current_text))
                current_component = 'conclusion'
                current_text = [line.split(':', 1)[1].strip()]
            elif line.lower().startswith('next action:'):
                if current_component:
                    setattr(structure, current_component, '\n'.join(current_text))
                current_component = 'next_action'
                current_text = [line.split(':', 1)[1].strip()]
            else:
                # Continue current component or start general observation
                if current_component is None:
                    current_component = 'observation'
                    current_text = [line]
                else:
                    current_text.append(line)

        # Set the final component
        if current_component and current_text:
            setattr(structure, current_component, '\n'.join(current_text))

        return structure

    def _format_action_input(self, action_input: Dict[str, Any]) -> str:
        """Format action input for display."""
        if not action_input:
            return "{}"

        if len(action_input) == 1 and "input" in action_input:
            # Simple input format
            return f'"{action_input["input"]}"'

        # JSON format for complex inputs
        import json
        try:
            return json.dumps(action_input, indent=2)
        except (TypeError, ValueError):
            return str(action_input)

    def create_system_prompt_addition(self) -> str:
        """Create additional system prompt instructions for thought formatting."""
        return """
When reasoning, structure your thoughts clearly:

1. **Observation**: What you can observe from the current situation
2. **Analysis**: Break down the problem or information
3. **Reasoning**: Your logical thought process
4. **Conclusion**: What you've determined
5. **Action**: What you'll do next (if needed)

Format your responses as:
Thought: [Your reasoning]
Action: [Action name]
Action Input: [Action parameters]

Or for final answers:
Thought: [Your reasoning]
Final Answer: [Your answer]
"""

    def validate_thought_structure(self, thought: str) -> bool:
        """Validate if thought follows proper structure."""
        # Basic validation
        if not thought.strip():
            return False

        # Should start with "Thought:"
        if not thought.strip().lower().startswith('thought:'):
            return False

        # Should contain meaningful content
        content = thought.split(':', 1)[1].strip() if ':' in thought else thought
        return len(content) > 10  # Minimum meaningful length