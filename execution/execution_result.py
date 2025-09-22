"""Result container for ReAct execution."""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime

from .execution_context import ExecutionContext, ExecutionStep


@dataclass
class ExecutionResult:
    """Result of a ReAct execution session."""

    # Core results
    final_answer: str
    success: bool

    # Execution details
    steps_taken: int
    execution_time: float
    iterations_used: int

    # Steps and context
    execution_steps: List[ExecutionStep]
    context: ExecutionContext

    # Error information
    error_message: Optional[str] = None
    error_step: Optional[int] = None

    # Performance metrics
    total_tokens: Optional[int] = None
    api_calls: Optional[int] = None
    tool_calls: Optional[int] = None

    # Metadata
    session_id: str = ""
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize computed fields."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    @classmethod
    def from_context(cls, context: ExecutionContext) -> 'ExecutionResult':
        """Create ExecutionResult from ExecutionContext."""
        return cls(
            final_answer=context.final_answer or "",
            success=context.completed and context.error is None,
            steps_taken=len(context.steps),
            execution_time=context.get_execution_time(),
            iterations_used=context.current_iteration,
            execution_steps=context.steps.copy(),
            context=context,
            error_message=context.error,
            error_step=len(context.steps) if context.error else None,
            session_id=context.session_id,
            metadata=context.metadata.copy()
        )

    def get_step_summary(self) -> List[Dict[str, Any]]:
        """Get a summary of all execution steps."""
        return [
            {
                "step": step.step_number,
                "thought": step.thought[:100] + "..." if len(step.thought) > 100 else step.thought,
                "action": step.action,
                "has_observation": step.observation is not None,
                "timestamp": step.timestamp.isoformat()
            }
            for step in self.execution_steps
        ]

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            "execution_time": self.execution_time,
            "steps_taken": self.steps_taken,
            "iterations_used": self.iterations_used,
            "total_tokens": self.total_tokens,
            "api_calls": self.api_calls,
            "tool_calls": self.tool_calls,
            "success": self.success,
            "efficiency": self.steps_taken / max(self.execution_time, 0.001)  # steps per second
        }

    def get_execution_trace(self) -> str:
        """Get a formatted trace of the execution."""
        trace = [f"=== ReAct Execution Trace ==="]
        trace.append(f"Session: {self.session_id}")
        trace.append(f"Success: {self.success}")
        trace.append(f"Steps: {self.steps_taken}")
        trace.append(f"Time: {self.execution_time:.2f}s")
        trace.append("")

        for step in self.execution_steps:
            trace.append(f"Step {step.step_number}:")
            trace.append(f"  Thought: {step.thought}")
            if step.action:
                trace.append(f"  Action: {step.action}")
                if step.action_input:
                    trace.append(f"  Input: {step.action_input}")
            if step.observation:
                trace.append(f"  Observation: {step.observation}")
            trace.append("")

        if self.final_answer:
            trace.append(f"Final Answer: {self.final_answer}")

        if self.error_message:
            trace.append(f"Error: {self.error_message}")

        return "\n".join(trace)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "final_answer": self.final_answer,
            "success": self.success,
            "steps_taken": self.steps_taken,
            "execution_time": self.execution_time,
            "iterations_used": self.iterations_used,
            "execution_steps": [
                {
                    "step_number": getattr(step, 'step_number', getattr(step, 'iteration', 0)),
                    "thought": getattr(step, 'thought', ''),
                    "action": getattr(step, 'action', ''),
                    "action_input": getattr(step, 'action_input', ''),
                    "observation": getattr(step, 'observation', ''),
                    "step_type": getattr(step, 'step_type', ''),
                    "content": getattr(step, 'content', ''),
                    "timestamp": step.timestamp.isoformat() if hasattr(step, 'timestamp') else '',
                    "metadata": getattr(step, 'metadata', {})
                }
                for step in self.execution_steps
            ],
            "error_message": self.error_message,
            "error_step": self.error_step,
            "total_tokens": self.total_tokens,
            "api_calls": self.api_calls,
            "tool_calls": self.tool_calls,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "performance_metrics": self.get_performance_metrics()
        }