"""Core optimizer that orchestrates prompt optimization."""

import asyncio
import time
from typing import List, Dict, Any, Optional, Callable, Awaitable, Union

from .optimization_context import OptimizationContext, TrainingExample
from .optimization_result import OptimizationResult
from .optimization_strategies import (
    OptimizationStrategy,
    BootstrapStrategy,
    CoordinateAscentStrategy,
    BayesianStrategy
)
from .mipro_bootstrap import MIPROBootstrapStrategy
from .metrics import OptimizationMetric, AccuracyMetric


class CoreOptimizer:
    """
    Core optimizer that orchestrates prompt optimization.

    This optimizer provides a unified interface for prompt optimization
    using different strategies inspired by DSPy algorithms.
    """

    def __init__(
        self,
        strategy: Union[str, OptimizationStrategy] = "bootstrap",
        metric: Optional[OptimizationMetric] = None,
        max_iterations: int = 10,
        convergence_threshold: float = 0.95,
        timeout_seconds: int = 300
    ):
        """
        Initialize the core optimizer.

        Args:
            strategy: Optimization strategy to use or strategy name
            metric: Metric for evaluating prompt performance
            max_iterations: Maximum optimization iterations
            convergence_threshold: Score threshold for convergence
            timeout_seconds: Maximum optimization time
        """
        self.strategy = self._create_strategy(strategy)
        self.metric = metric or AccuracyMetric()
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.timeout_seconds = timeout_seconds

        # Tracking
        self.total_api_calls = 0
        self.total_tokens = 0

    async def optimize(
        self,
        initial_prompt: str,
        training_examples: List[TrainingExample],
        agent_evaluator: Callable[[str, TrainingExample], Awaitable[str]],
        optimization_target: str = "accuracy"
    ) -> OptimizationResult:
        """
        Optimize a prompt using the configured strategy.

        Args:
            initial_prompt: The initial prompt to optimize
            training_examples: Training data for optimization
            agent_evaluator: Function to evaluate agent with prompts
            optimization_target: Target metric for optimization

        Returns:
            OptimizationResult containing the optimization outcome
        """
        # Create optimization context
        context = OptimizationContext(
            initial_prompt=initial_prompt,
            training_examples=training_examples,
            optimization_target=optimization_target,
            max_iterations=self.max_iterations,
            convergence_threshold=self.convergence_threshold
        )

        start_time = time.time()

        try:
            # Run optimization with timeout
            await asyncio.wait_for(
                self._optimize_loop(context, agent_evaluator),
                timeout=self.timeout_seconds
            )

        except asyncio.TimeoutError:
            context.mark_error(f"Optimization timed out after {self.timeout_seconds} seconds")

        except Exception as e:
            context.mark_error(f"Optimization failed: {str(e)}")

        # Calculate execution time
        execution_time = time.time() - start_time
        context.execution_time = execution_time

        # Update resource tracking
        context.api_calls = self.total_api_calls
        context.total_tokens = self.total_tokens

        # Create and return result
        result = OptimizationResult.from_context(context)
        result.strategy_used = self.strategy.get_name()

        return result

    async def _optimize_loop(
        self,
        context: OptimizationContext,
        agent_evaluator: Callable[[str, TrainingExample], Awaitable[str]]
    ) -> None:
        """Run the main optimization loop."""

        # Evaluate initial prompt
        await self._evaluate_initial_prompt(context, agent_evaluator)

        # Run optimization steps
        while context.should_continue():
            try:
                # Perform optimization step
                should_continue = await self.strategy.optimize_step(
                    context,
                    self._tracked_agent_evaluator(agent_evaluator),
                    self.metric
                )

                if not should_continue:
                    break

            except Exception as e:
                print(f"Error in optimization step: {e}")
                break

        # Mark as complete if successful
        if not context.error:
            context.mark_complete()

    async def _evaluate_initial_prompt(
        self,
        context: OptimizationContext,
        agent_evaluator: Callable[[str, TrainingExample], Awaitable[str]]
    ) -> None:
        """Evaluate the initial prompt to establish baseline."""

        train_examples, validation_examples = context.get_train_validation_split()
        eval_examples = validation_examples or train_examples[-3:]

        if not eval_examples:
            context.add_step(
                strategy="baseline",
                prompt_candidate=context.initial_prompt,
                evaluation_score=0.0,
                examples_used=[]
            )
            return

        total_score = 0.0
        valid_evaluations = 0

        for example in eval_examples:
            try:
                response = await agent_evaluator(context.initial_prompt, example)
                score = self.metric.evaluate(response, example.expected_output)
                total_score += score
                valid_evaluations += 1
                self.total_api_calls += 1
            except Exception:
                continue

        baseline_score = total_score / max(valid_evaluations, 1)

        # Add baseline step
        context.add_step(
            strategy="baseline",
            prompt_candidate=context.initial_prompt,
            evaluation_score=baseline_score,
            examples_used=eval_examples
        )

    def _tracked_agent_evaluator(
        self,
        agent_evaluator: Callable[[str, TrainingExample], Awaitable[str]]
    ) -> Callable[[str, TrainingExample], Awaitable[str]]:
        """Wrap agent evaluator to track API calls."""

        async def wrapped_evaluator(prompt: str, example: TrainingExample) -> str:
            result = await agent_evaluator(prompt, example)
            self.total_api_calls += 1
            # Estimate tokens (rough approximation)
            self.total_tokens += len(prompt.split()) + len(result.split())
            return result

        return wrapped_evaluator

    def _create_strategy(self, strategy: Union[str, OptimizationStrategy]) -> OptimizationStrategy:
        """Create optimization strategy from name or instance."""

        if isinstance(strategy, OptimizationStrategy):
            return strategy

        strategy_map = {
            "bootstrap": BootstrapStrategy(),
            "mipro_bootstrap": MIPROBootstrapStrategy(),  # MIPROv2-style validated bootstrap
            "coordinate_ascent": CoordinateAscentStrategy(),
            "copro": CoordinateAscentStrategy(),  # Alias
            "bayesian": BayesianStrategy(),
            "mipro": MIPROBootstrapStrategy()  # Alias for MIPROv2-style (was simplified Bayesian)
        }

        if strategy in strategy_map:
            return strategy_map[strategy]
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def get_strategy_name(self) -> str:
        """Get the name of the current strategy."""
        return self.strategy.get_name()

    def get_metric_name(self) -> str:
        """Get the name of the current metric."""
        return self.metric.get_name()

    def set_strategy(self, strategy: Union[str, OptimizationStrategy]) -> None:
        """Set the optimization strategy."""
        self.strategy = self._create_strategy(strategy)

    def set_metric(self, metric: OptimizationMetric) -> None:
        """Set the optimization metric."""
        self.metric = metric

    def reset_tracking(self) -> None:
        """Reset API call and token tracking."""
        self.total_api_calls = 0
        self.total_tokens = 0

    def get_tracking_stats(self) -> Dict[str, Any]:
        """Get current tracking statistics."""
        return {
            "total_api_calls": self.total_api_calls,
            "total_tokens": self.total_tokens,
            "strategy": self.strategy.get_name(),
            "metric": self.metric.get_name(),
            "max_iterations": self.max_iterations,
            "convergence_threshold": self.convergence_threshold,
            "timeout_seconds": self.timeout_seconds
        }

    @classmethod
    def create_bootstrap_optimizer(
        cls,
        max_examples: int = 4,
        score_threshold: float = 0.7,
        **kwargs
    ) -> 'CoreOptimizer':
        """Create optimizer with bootstrap strategy."""
        strategy = BootstrapStrategy(
            max_examples=max_examples,
            min_score_threshold=score_threshold
        )
        return cls(strategy=strategy, **kwargs)

    @classmethod
    def create_coordinate_ascent_optimizer(
        cls,
        candidates_per_iteration: int = 3,
        **kwargs
    ) -> 'CoreOptimizer':
        """Create optimizer with coordinate ascent strategy."""
        strategy = CoordinateAscentStrategy(
            candidates_per_iteration=candidates_per_iteration
        )
        return cls(strategy=strategy, **kwargs)

    @classmethod
    def create_bayesian_optimizer(
        cls,
        exploration_factor: float = 0.1,
        **kwargs
    ) -> 'CoreOptimizer':
        """Create optimizer with Bayesian strategy."""
        strategy = BayesianStrategy(
            exploration_factor=exploration_factor
        )
        return cls(strategy=strategy, **kwargs)

    async def quick_optimize(
        self,
        initial_prompt: str,
        examples: List[Dict[str, str]],
        agent_evaluator: Callable[[str, str], Awaitable[str]]
    ) -> str:
        """
        Quick optimization interface for simple use cases.

        Args:
            initial_prompt: Initial prompt
            examples: List of {"input": ..., "output": ...} dicts
            agent_evaluator: Function (prompt, input) -> output

        Returns:
            Optimized prompt
        """
        # Convert examples
        training_examples = [
            TrainingExample(
                input=ex["input"],
                expected_output=ex["output"]
            )
            for ex in examples
        ]

        # Wrap evaluator
        async def wrapped_evaluator(prompt: str, example: TrainingExample) -> str:
            return await agent_evaluator(prompt, example.input)

        # Run optimization
        result = await self.optimize(
            initial_prompt,
            training_examples,
            wrapped_evaluator
        )

        return result.optimized_prompt