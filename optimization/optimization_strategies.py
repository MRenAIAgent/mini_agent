"""Core optimization strategies based on DSPy algorithms."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable, Awaitable
import random
import asyncio

from .optimization_context import OptimizationContext, TrainingExample
from .metrics import OptimizationMetric


class OptimizationStrategy(ABC):
    """Abstract base class for optimization strategies."""

    @abstractmethod
    async def optimize_step(
        self,
        context: OptimizationContext,
        agent_evaluator: Callable[[str, TrainingExample], Awaitable[str]],
        metric: OptimizationMetric
    ) -> bool:
        """
        Perform a single optimization step.

        Args:
            context: Current optimization context
            agent_evaluator: Function to evaluate agent with a prompt
            metric: Metric to evaluate performance

        Returns:
            True if optimization should continue, False if done
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this strategy."""
        pass


class BootstrapStrategy(OptimizationStrategy):
    """Bootstrap few-shot example generation strategy."""

    def __init__(
        self,
        max_examples: int = 4,
        min_score_threshold: float = 0.7,
        example_selection_rounds: int = 3
    ):
        self.max_examples = max_examples
        self.min_score_threshold = min_score_threshold
        self.example_selection_rounds = example_selection_rounds

    async def optimize_step(
        self,
        context: OptimizationContext,
        agent_evaluator: Callable[[str, TrainingExample], Awaitable[str]],
        metric: OptimizationMetric
    ) -> bool:
        """Perform bootstrap optimization step."""

        # Get training examples
        train_examples, validation_examples = context.get_train_validation_split()

        if not train_examples:
            return False

        # Generate few-shot examples using current best prompt
        few_shot_examples = await self._generate_few_shot_examples(
            context.best_prompt,
            train_examples,
            agent_evaluator,
            metric
        )

        if not few_shot_examples:
            return False

        # Create new prompt with few-shot examples
        enhanced_prompt = self._create_few_shot_prompt(
            context.best_prompt,
            few_shot_examples
        )

        # Evaluate the enhanced prompt
        validation_score = await self._evaluate_prompt(
            enhanced_prompt,
            validation_examples or train_examples[-2:],
            agent_evaluator,
            metric
        )

        # Add optimization step
        context.add_step(
            strategy="bootstrap_few_shot",
            prompt_candidate=enhanced_prompt,
            evaluation_score=validation_score,
            examples_used=few_shot_examples,
            few_shot_count=len(few_shot_examples)
        )

        context.current_iteration += 1
        return context.should_continue()

    async def _generate_few_shot_examples(
        self,
        prompt: str,
        training_examples: List[TrainingExample],
        agent_evaluator: Callable[[str, TrainingExample], Awaitable[str]],
        metric: OptimizationMetric
    ) -> List[TrainingExample]:
        """Generate high-quality few-shot examples."""

        good_examples = []

        # Randomly sample training examples to evaluate
        sample_size = min(len(training_examples), 10)
        sampled_examples = random.sample(training_examples, sample_size)

        for example in sampled_examples:
            if len(good_examples) >= self.max_examples:
                break

            try:
                # Get agent's response
                response = await agent_evaluator(prompt, example)

                # Evaluate quality
                score = metric.evaluate(response, example.expected_output)

                # Keep if above threshold
                if score >= self.min_score_threshold:
                    # Create new example with agent's response
                    few_shot_example = TrainingExample(
                        input=example.input,
                        expected_output=response,  # Use agent's response
                        metadata={**example.metadata, "bootstrap_score": score}
                    )
                    good_examples.append(few_shot_example)

            except Exception as e:
                print(f"Error evaluating example: {e}")
                continue

        return good_examples

    def _create_few_shot_prompt(
        self,
        base_prompt: str,
        few_shot_examples: List[TrainingExample]
    ) -> str:
        """Create prompt with few-shot examples."""

        if not few_shot_examples:
            return base_prompt

        # Add few-shot examples to prompt
        examples_text = "\n\nHere are some examples:\n"

        for i, example in enumerate(few_shot_examples, 1):
            examples_text += f"\nExample {i}:\n"
            examples_text += f"Input: {example.input}\n"
            examples_text += f"Output: {example.expected_output}\n"

        return base_prompt + examples_text + "\n\nNow solve the following:"

    async def _evaluate_prompt(
        self,
        prompt: str,
        validation_examples: List[TrainingExample],
        agent_evaluator: Callable[[str, TrainingExample], Awaitable[str]],
        metric: OptimizationMetric
    ) -> float:
        """Evaluate prompt performance on validation set."""

        if not validation_examples:
            return 0.0

        total_score = 0.0
        valid_evaluations = 0

        for example in validation_examples:
            try:
                response = await agent_evaluator(prompt, example)
                score = metric.evaluate(response, example.expected_output)
                total_score += score
                valid_evaluations += 1
            except Exception:
                continue

        return total_score / max(valid_evaluations, 1)

    def get_name(self) -> str:
        return "bootstrap_few_shot"


class CoordinateAscentStrategy(OptimizationStrategy):
    """Coordinate ascent optimization strategy (COPRO-inspired)."""

    def __init__(
        self,
        candidates_per_iteration: int = 3,
        prompt_variations: List[str] = None
    ):
        self.candidates_per_iteration = candidates_per_iteration
        self.prompt_variations = prompt_variations or [
            "Be more specific and detailed in your response.",
            "Think step by step before answering.",
            "Provide clear reasoning for your answer.",
            "Focus on accuracy and precision.",
            "Consider multiple perspectives before responding."
        ]

    async def optimize_step(
        self,
        context: OptimizationContext,
        agent_evaluator: Callable[[str, TrainingExample], Awaitable[str]],
        metric: OptimizationMetric
    ) -> bool:
        """Perform coordinate ascent optimization step."""

        # Generate prompt candidates
        candidates = self._generate_prompt_candidates(context.best_prompt)

        # Evaluate each candidate
        train_examples, validation_examples = context.get_train_validation_split()
        eval_examples = validation_examples or train_examples[-3:]

        best_candidate = context.best_prompt
        best_score = 0.0

        for candidate in candidates:
            try:
                score = await self._evaluate_prompt(
                    candidate,
                    eval_examples,
                    agent_evaluator,
                    metric
                )

                if score > best_score:
                    best_score = score
                    best_candidate = candidate

                # Add step for this candidate
                context.add_step(
                    strategy="coordinate_ascent",
                    prompt_candidate=candidate,
                    evaluation_score=score,
                    examples_used=[],
                    is_best=score > context.best_score
                )

            except Exception as e:
                print(f"Error evaluating candidate: {e}")
                continue

        context.current_iteration += 1
        return context.should_continue()

    def _generate_prompt_candidates(self, base_prompt: str) -> List[str]:
        """Generate prompt candidates using various strategies."""

        candidates = [base_prompt]  # Include current prompt

        # Add instruction variations
        for variation in self.prompt_variations[:self.candidates_per_iteration - 1]:
            candidate = f"{base_prompt}\n\n{variation}"
            candidates.append(candidate)

        return candidates

    async def _evaluate_prompt(
        self,
        prompt: str,
        validation_examples: List[TrainingExample],
        agent_evaluator: Callable[[str, TrainingExample], Awaitable[str]],
        metric: OptimizationMetric
    ) -> float:
        """Evaluate prompt performance."""

        if not validation_examples:
            return 0.0

        total_score = 0.0
        valid_evaluations = 0

        for example in validation_examples:
            try:
                response = await agent_evaluator(prompt, example)
                score = metric.evaluate(response, example.expected_output)
                total_score += score
                valid_evaluations += 1
            except Exception:
                continue

        return total_score / max(valid_evaluations, 1)

    def get_name(self) -> str:
        return "coordinate_ascent"


class BayesianStrategy(OptimizationStrategy):
    """Simple Bayesian optimization strategy."""

    def __init__(
        self,
        exploration_factor: float = 0.1,
        prompt_templates: List[str] = None
    ):
        self.exploration_factor = exploration_factor
        self.prompt_templates = prompt_templates or [
            "{base_prompt}\n\nPlease provide a detailed and accurate response.",
            "{base_prompt}\n\nThink carefully and respond step by step.",
            "{base_prompt}\n\nConsider all relevant factors before answering.",
            "Task: {base_prompt}\n\nApproach this systematically and provide a clear answer.",
            "Question: {base_prompt}\n\nAnalyze this carefully and give your best response."
        ]
        self.performance_history = []

    async def optimize_step(
        self,
        context: OptimizationContext,
        agent_evaluator: Callable[[str, TrainingExample], Awaitable[str]],
        metric: OptimizationMetric
    ) -> bool:
        """Perform Bayesian optimization step."""

        # Select next prompt to try using acquisition function
        candidate_prompt = self._select_next_candidate(context)

        # Evaluate the candidate
        train_examples, validation_examples = context.get_train_validation_split()
        eval_examples = validation_examples or train_examples[-3:]

        try:
            score = await self._evaluate_prompt(
                candidate_prompt,
                eval_examples,
                agent_evaluator,
                metric
            )

            # Update performance history
            self.performance_history.append((candidate_prompt, score))

            # Add optimization step
            context.add_step(
                strategy="bayesian",
                prompt_candidate=candidate_prompt,
                evaluation_score=score,
                examples_used=[],
                exploration_factor=self.exploration_factor
            )

        except Exception as e:
            print(f"Error in Bayesian optimization: {e}")
            return False

        context.current_iteration += 1
        return context.should_continue()

    def _select_next_candidate(self, context: OptimizationContext) -> str:
        """Select next candidate using simple acquisition function."""

        # Simple exploration vs exploitation
        if random.random() < self.exploration_factor or not self.performance_history:
            # Exploration: try a random template
            template = random.choice(self.prompt_templates)
            return template.format(base_prompt=context.best_prompt)
        else:
            # Exploitation: refine the best known prompt
            return self._refine_best_prompt(context.best_prompt)

    def _refine_best_prompt(self, best_prompt: str) -> str:
        """Refine the best known prompt."""

        refinements = [
            "\n\nBe precise and thorough in your response.",
            "\n\nEnsure your answer is accurate and well-reasoned.",
            "\n\nProvide specific details to support your answer.",
            "\n\nDouble-check your reasoning before responding."
        ]

        refinement = random.choice(refinements)
        return best_prompt + refinement

    async def _evaluate_prompt(
        self,
        prompt: str,
        validation_examples: List[TrainingExample],
        agent_evaluator: Callable[[str, TrainingExample], Awaitable[str]],
        metric: OptimizationMetric
    ) -> float:
        """Evaluate prompt performance."""

        if not validation_examples:
            return 0.0

        total_score = 0.0
        valid_evaluations = 0

        for example in validation_examples:
            try:
                response = await agent_evaluator(prompt, example)
                score = metric.evaluate(response, example.expected_output)
                total_score += score
                valid_evaluations += 1
            except Exception:
                continue

        return total_score / max(valid_evaluations, 1)

    def get_name(self) -> str:
        return "bayesian"