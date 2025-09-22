"""Optimization context for managing prompt optimization state."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid


@dataclass
class TrainingExample:
    """A training example for optimization."""

    input: str
    expected_output: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "input": self.input,
            "expected_output": self.expected_output,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrainingExample':
        """Create from dictionary."""
        return cls(
            input=data["input"],
            expected_output=data["expected_output"],
            metadata=data.get("metadata", {})
        )


@dataclass
class OptimizationStep:
    """A single step in the optimization process."""

    step_number: int
    strategy: str
    prompt_candidate: str
    evaluation_score: float
    examples_used: List[TrainingExample] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_number": self.step_number,
            "strategy": self.strategy,
            "prompt_candidate": self.prompt_candidate,
            "evaluation_score": self.evaluation_score,
            "examples_used": [ex.to_dict() for ex in self.examples_used],
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class OptimizationContext:
    """Context for managing prompt optimization state."""

    # Input configuration
    initial_prompt: str
    training_examples: List[TrainingExample]
    optimization_target: str = "accuracy"  # accuracy, efficiency, etc.

    # Optimization settings
    max_iterations: int = 10
    convergence_threshold: float = 0.95
    validation_split: float = 0.2

    # State tracking
    current_iteration: int = 0
    best_prompt: str = ""
    best_score: float = 0.0
    optimization_steps: List[OptimizationStep] = field(default_factory=list)

    # Metadata
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    completed: bool = False
    error: Optional[str] = None

    # Resource tracking
    api_calls: int = 0
    total_tokens: int = 0
    execution_time: float = 0.0

    def __post_init__(self):
        """Initialize computed fields."""
        if not self.best_prompt:
            self.best_prompt = self.initial_prompt

    def add_step(
        self,
        strategy: str,
        prompt_candidate: str,
        evaluation_score: float,
        examples_used: List[TrainingExample] = None,
        **metadata
    ) -> OptimizationStep:
        """Add a new optimization step."""
        step = OptimizationStep(
            step_number=len(self.optimization_steps) + 1,
            strategy=strategy,
            prompt_candidate=prompt_candidate,
            evaluation_score=evaluation_score,
            examples_used=examples_used or [],
            metadata=metadata
        )

        self.optimization_steps.append(step)

        # Update best if this is an improvement
        if evaluation_score > self.best_score:
            self.best_score = evaluation_score
            self.best_prompt = prompt_candidate

        return step

    def get_train_validation_split(self) -> Tuple[List[TrainingExample], List[TrainingExample]]:
        """Split training examples into train and validation sets."""
        total_examples = len(self.training_examples)
        validation_size = int(total_examples * self.validation_split)

        if validation_size == 0:
            # If too few examples, use all for training
            return self.training_examples, []

        train_examples = self.training_examples[:-validation_size]
        validation_examples = self.training_examples[-validation_size:]

        return train_examples, validation_examples

    def should_continue(self) -> bool:
        """Check if optimization should continue."""
        if self.completed or self.error:
            return False

        if self.current_iteration >= self.max_iterations:
            return False

        if self.best_score >= self.convergence_threshold:
            return False

        return True

    def mark_complete(self, final_prompt: str = None) -> None:
        """Mark optimization as complete."""
        self.completed = True
        self.end_time = datetime.now()
        if final_prompt:
            self.best_prompt = final_prompt

    def mark_error(self, error: str) -> None:
        """Mark optimization as failed with error."""
        self.error = error
        self.end_time = datetime.now()

    def get_improvement_history(self) -> List[Tuple[int, float]]:
        """Get history of score improvements."""
        improvements = []
        current_best = 0.0

        for step in self.optimization_steps:
            if step.evaluation_score > current_best:
                current_best = step.evaluation_score
                improvements.append((step.step_number, current_best))

        return improvements

    def get_convergence_rate(self) -> float:
        """Calculate convergence rate (improvement per iteration)."""
        if not self.optimization_steps:
            return 0.0

        improvements = self.get_improvement_history()
        if len(improvements) < 2:
            return 0.0

        total_improvement = improvements[-1][1] - improvements[0][1]
        iterations_taken = improvements[-1][0] - improvements[0][0]

        return total_improvement / max(iterations_taken, 1)

    def get_execution_efficiency(self) -> Dict[str, float]:
        """Get efficiency metrics."""
        total_time = self.execution_time
        if self.end_time and self.start_time:
            total_time = (self.end_time - self.start_time).total_seconds()

        return {
            "score_per_iteration": self.best_score / max(self.current_iteration, 1),
            "score_per_second": self.best_score / max(total_time, 0.001),
            "score_per_api_call": self.best_score / max(self.api_calls, 1),
            "iterations_per_minute": (self.current_iteration / max(total_time, 0.001)) * 60
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "initial_prompt": self.initial_prompt,
            "training_examples": [ex.to_dict() for ex in self.training_examples],
            "optimization_target": self.optimization_target,
            "max_iterations": self.max_iterations,
            "convergence_threshold": self.convergence_threshold,
            "validation_split": self.validation_split,
            "current_iteration": self.current_iteration,
            "best_prompt": self.best_prompt,
            "best_score": self.best_score,
            "optimization_steps": [step.to_dict() for step in self.optimization_steps],
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "completed": self.completed,
            "error": self.error,
            "api_calls": self.api_calls,
            "total_tokens": self.total_tokens,
            "execution_time": self.execution_time,
            "improvement_history": self.get_improvement_history(),
            "convergence_rate": self.get_convergence_rate(),
            "efficiency_metrics": self.get_execution_efficiency()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OptimizationContext':
        """Create from dictionary."""
        training_examples = [
            TrainingExample.from_dict(ex_data)
            for ex_data in data.get("training_examples", [])
        ]

        context = cls(
            initial_prompt=data["initial_prompt"],
            training_examples=training_examples,
            optimization_target=data.get("optimization_target", "accuracy"),
            max_iterations=data.get("max_iterations", 10),
            convergence_threshold=data.get("convergence_threshold", 0.95),
            validation_split=data.get("validation_split", 0.2),
            current_iteration=data.get("current_iteration", 0),
            best_prompt=data.get("best_prompt", data["initial_prompt"]),
            best_score=data.get("best_score", 0.0),
            session_id=data.get("session_id", str(uuid.uuid4())),
            completed=data.get("completed", False),
            error=data.get("error"),
            api_calls=data.get("api_calls", 0),
            total_tokens=data.get("total_tokens", 0),
            execution_time=data.get("execution_time", 0.0)
        )

        # Set timestamps
        if "start_time" in data:
            context.start_time = datetime.fromisoformat(data["start_time"])
        if "end_time" in data and data["end_time"]:
            context.end_time = datetime.fromisoformat(data["end_time"])

        # Load optimization steps
        if "optimization_steps" in data:
            for step_data in data["optimization_steps"]:
                examples_used = [
                    TrainingExample.from_dict(ex_data)
                    for ex_data in step_data.get("examples_used", [])
                ]

                step = OptimizationStep(
                    step_number=step_data["step_number"],
                    strategy=step_data["strategy"],
                    prompt_candidate=step_data["prompt_candidate"],
                    evaluation_score=step_data["evaluation_score"],
                    examples_used=examples_used,
                    metadata=step_data.get("metadata", {}),
                    timestamp=datetime.fromisoformat(step_data["timestamp"])
                )
                context.optimization_steps.append(step)

        return context