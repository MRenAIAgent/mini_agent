"""Optimization result container."""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime

from .optimization_context import OptimizationContext, OptimizationStep, TrainingExample


@dataclass
class OptimizationResult:
    """Result of a prompt optimization session."""

    # Core results
    optimized_prompt: str
    best_score: float
    improvement: float  # Improvement over initial prompt

    # Execution details
    iterations_completed: int
    total_execution_time: float
    convergence_achieved: bool

    # Resource usage
    api_calls: int
    total_tokens: int
    examples_used: int

    # Optimization trace
    optimization_history: List[OptimizationStep]
    few_shot_examples: List[TrainingExample] = field(default_factory=list)

    # Performance metrics
    convergence_rate: float = 0.0
    efficiency_score: float = 0.0  # Score per second
    cost_efficiency: float = 0.0   # Score per API call

    # Metadata
    session_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    strategy_used: str = ""
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_context(cls, context: OptimizationContext) -> 'OptimizationResult':
        """Create OptimizationResult from OptimizationContext."""
        initial_score = context.optimization_steps[0].evaluation_score if context.optimization_steps else 0.0
        improvement = context.best_score - initial_score

        # Calculate efficiency metrics
        efficiency_metrics = context.get_execution_efficiency()

        return cls(
            optimized_prompt=context.best_prompt,
            best_score=context.best_score,
            improvement=improvement,
            iterations_completed=context.current_iteration,
            total_execution_time=context.execution_time,
            convergence_achieved=context.best_score >= context.convergence_threshold,
            api_calls=context.api_calls,
            total_tokens=context.total_tokens,
            examples_used=len(context.training_examples),
            optimization_history=context.optimization_steps.copy(),
            convergence_rate=context.get_convergence_rate(),
            efficiency_score=efficiency_metrics.get("score_per_second", 0.0),
            cost_efficiency=efficiency_metrics.get("score_per_api_call", 0.0),
            session_id=context.session_id,
            success=context.completed and context.error is None,
            error_message=context.error,
            metadata=context.to_dict()
        )

    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get a summary of the optimization results."""
        return {
            "success": self.success,
            "final_score": self.best_score,
            "improvement": self.improvement,
            "improvement_percentage": (self.improvement / max(self.best_score - self.improvement, 0.001)) * 100,
            "iterations": self.iterations_completed,
            "execution_time": self.total_execution_time,
            "convergence_achieved": self.convergence_achieved,
            "efficiency": {
                "score_per_second": self.efficiency_score,
                "score_per_api_call": self.cost_efficiency,
                "iterations_per_minute": (self.iterations_completed / max(self.total_execution_time, 0.001)) * 60
            },
            "resource_usage": {
                "api_calls": self.api_calls,
                "total_tokens": self.total_tokens,
                "examples_used": self.examples_used
            }
        }

    def get_step_analysis(self) -> Dict[str, Any]:
        """Analyze the optimization steps."""
        if not self.optimization_history:
            return {"total_steps": 0}

        scores = [step.evaluation_score for step in self.optimization_history]
        strategies = [step.strategy for step in self.optimization_history]

        # Calculate score progression
        score_improvements = []
        for i in range(1, len(scores)):
            improvement = scores[i] - scores[i-1]
            score_improvements.append(improvement)

        # Strategy effectiveness
        strategy_scores = {}
        for step in self.optimization_history:
            strategy = step.strategy
            if strategy not in strategy_scores:
                strategy_scores[strategy] = []
            strategy_scores[strategy].append(step.evaluation_score)

        strategy_effectiveness = {}
        for strategy, scores_list in strategy_scores.items():
            strategy_effectiveness[strategy] = {
                "avg_score": sum(scores_list) / len(scores_list),
                "max_score": max(scores_list),
                "usage_count": len(scores_list)
            }

        return {
            "total_steps": len(self.optimization_history),
            "score_range": {
                "min": min(scores),
                "max": max(scores),
                "final": scores[-1] if scores else 0
            },
            "avg_improvement_per_step": sum(score_improvements) / len(score_improvements) if score_improvements else 0,
            "strategy_effectiveness": strategy_effectiveness,
            "best_step": max(self.optimization_history, key=lambda x: x.evaluation_score).step_number
        }

    def get_performance_comparison(self, baseline_score: float = None) -> Dict[str, Any]:
        """Compare performance against baseline."""
        if baseline_score is None:
            baseline_score = self.optimization_history[0].evaluation_score if self.optimization_history else 0

        return {
            "baseline_score": baseline_score,
            "optimized_score": self.best_score,
            "absolute_improvement": self.best_score - baseline_score,
            "relative_improvement": ((self.best_score - baseline_score) / max(baseline_score, 0.001)) * 100,
            "improvement_ratio": self.best_score / max(baseline_score, 0.001)
        }

    def export_optimized_prompt(self) -> Dict[str, Any]:
        """Export the optimized prompt with metadata."""
        return {
            "prompt": self.optimized_prompt,
            "score": self.best_score,
            "confidence": self.convergence_achieved,
            "few_shot_examples": [
                {
                    "input": ex.input,
                    "output": ex.expected_output,
                    "metadata": ex.metadata
                }
                for ex in self.few_shot_examples
            ],
            "optimization_metadata": {
                "session_id": self.session_id,
                "timestamp": self.timestamp.isoformat(),
                "strategy": self.strategy_used,
                "iterations": self.iterations_completed,
                "improvement": self.improvement
            }
        }

    def get_optimization_report(self) -> str:
        """Generate a human-readable optimization report."""
        summary = self.get_optimization_summary()
        step_analysis = self.get_step_analysis()

        lines = [
            "=== Prompt Optimization Report ===",
            f"Session ID: {self.session_id}",
            f"Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "Results:",
            f"  Success: {'✓' if self.success else '✗'}",
            f"  Final Score: {self.best_score:.3f}",
            f"  Improvement: +{self.improvement:.3f} ({summary['improvement_percentage']:.1f}%)",
            f"  Convergence: {'✓' if self.convergence_achieved else '✗'}",
            "",
            "Execution:",
            f"  Iterations: {self.iterations_completed}",
            f"  Time: {self.total_execution_time:.2f}s",
            f"  API Calls: {self.api_calls}",
            f"  Tokens: {self.total_tokens:,}",
            "",
            "Efficiency:",
            f"  Score/Second: {self.efficiency_score:.3f}",
            f"  Score/API Call: {self.cost_efficiency:.3f}",
            f"  Iterations/Minute: {summary['efficiency']['iterations_per_minute']:.1f}",
            "",
            "Optimization Steps:",
            f"  Total Steps: {step_analysis['total_steps']}",
            f"  Best Step: #{step_analysis.get('best_step', 'N/A')}",
            f"  Avg Improvement/Step: {step_analysis.get('avg_improvement_per_step', 0):.3f}",
        ]

        if self.error_message:
            lines.extend([
                "",
                "Error:",
                f"  {self.error_message}"
            ])

        if step_analysis.get('strategy_effectiveness'):
            lines.extend([
                "",
                "Strategy Effectiveness:"
            ])
            for strategy, stats in step_analysis['strategy_effectiveness'].items():
                lines.append(f"  {strategy}: {stats['avg_score']:.3f} avg ({stats['usage_count']} uses)")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "optimized_prompt": self.optimized_prompt,
            "best_score": self.best_score,
            "improvement": self.improvement,
            "iterations_completed": self.iterations_completed,
            "total_execution_time": self.total_execution_time,
            "convergence_achieved": self.convergence_achieved,
            "api_calls": self.api_calls,
            "total_tokens": self.total_tokens,
            "examples_used": self.examples_used,
            "optimization_history": [step.to_dict() for step in self.optimization_history],
            "few_shot_examples": [ex.to_dict() for ex in self.few_shot_examples],
            "convergence_rate": self.convergence_rate,
            "efficiency_score": self.efficiency_score,
            "cost_efficiency": self.cost_efficiency,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "strategy_used": self.strategy_used,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "summary": self.get_optimization_summary(),
            "step_analysis": self.get_step_analysis()
        }