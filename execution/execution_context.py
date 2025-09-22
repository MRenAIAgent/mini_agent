"""Execution context for managing ReAct loop state."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class ExecutionStep:
    """A single step in the ReAct execution cycle."""

    step_number: int
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """Context for managing the state of a ReAct execution session."""

    # Input
    user_input: str
    system_prompt: str
    max_iterations: int = 5

    # State
    current_iteration: int = 0
    steps: List[ExecutionStep] = field(default_factory=list)
    final_answer: Optional[str] = None
    completed: bool = False
    error: Optional[str] = None

    # Metadata
    session_id: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_step(self, thought: str, action: str = None, action_input: Dict[str, Any] = None) -> ExecutionStep:
        """Add a new execution step."""
        step = ExecutionStep(
            step_number=len(self.steps) + 1,
            thought=thought,
            action=action,
            action_input=action_input
        )
        self.steps.append(step)
        return step

    def update_observation(self, observation: str) -> None:
        """Update the observation for the current step."""
        if self.steps:
            self.steps[-1].observation = observation

    def get_current_step(self) -> Optional[ExecutionStep]:
        """Get the current execution step."""
        return self.steps[-1] if self.steps else None

    def get_conversation_history(self) -> str:
        """Get formatted conversation history for LLM context."""
        history = []

        for step in self.steps:
            history.append(f"Thought: {step.thought}")
            if step.action:
                history.append(f"Action: {step.action}")
                if step.action_input:
                    history.append(f"Action Input: {step.action_input}")
            if step.observation:
                history.append(f"Observation: {step.observation}")

        return "\n".join(history)

    def is_complete(self) -> bool:
        """Check if execution is complete."""
        return self.completed or self.current_iteration >= self.max_iterations or self.error is not None

    def mark_complete(self, final_answer: str = None) -> None:
        """Mark execution as complete."""
        self.completed = True
        self.end_time = datetime.now()
        if final_answer:
            self.final_answer = final_answer

    def mark_error(self, error: str) -> None:
        """Mark execution as failed with error."""
        self.error = error
        self.end_time = datetime.now()

    def get_execution_time(self) -> float:
        """Get total execution time in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "user_input": self.user_input,
            "system_prompt": self.system_prompt,
            "max_iterations": self.max_iterations,
            "current_iteration": self.current_iteration,
            "steps": [
                {
                    "step_number": step.step_number,
                    "thought": step.thought,
                    "action": step.action,
                    "action_input": step.action_input,
                    "observation": step.observation,
                    "timestamp": step.timestamp.isoformat(),
                    "metadata": step.metadata
                }
                for step in self.steps
            ],
            "final_answer": self.final_answer,
            "completed": self.completed,
            "error": self.error,
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time": self.get_execution_time(),
            "metadata": self.metadata
        }