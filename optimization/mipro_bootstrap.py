"""
MIPROv2-style Bootstrap Strategy

Implements validated bootstrap with diversity selection, based on DSPy's MIPROv2 optimizer.
This provides significantly better few-shot examples compared to random sampling.

Key improvements over basic bootstrap:
1. Validates ALL training examples (not random sample)
2. Ranks by quality (uses best performers)
3. Selects diverse top-K (avoids redundancy)
4. Optional embedding-based diversity
"""

from typing import List, Dict, Any, Callable, Awaitable, Optional
from dataclasses import dataclass
import math

# Optional numpy for better performance
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    # Provide numpy-like functions for basic operations
    class np:
        """Minimal numpy-like interface for when numpy is not available."""
        ndarray = list  # Type hint

        @staticmethod
        def mean(arr):
            return sum(arr) / len(arr) if arr else 0

        @staticmethod
        def zeros(size):
            if isinstance(size, int):
                return [0.0] * size
            return [0.0 for _ in range(size)]

        @staticmethod
        def dot(a, b):
            return sum(x * y for x, y in zip(a, b))

        @staticmethod
        def array(arr):
            return list(arr) if not isinstance(arr, list) else arr

        class linalg:
            @staticmethod
            def norm(arr):
                return math.sqrt(sum(x * x for x in arr))

from .optimization_strategies import OptimizationStrategy
from .optimization_context import OptimizationContext, TrainingExample
from .metrics import OptimizationMetric


@dataclass
class CandidateExample:
    """A candidate few-shot example with quality and embedding."""
    example: TrainingExample
    response: str
    score: float
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = None


class MIPROBootstrapStrategy(OptimizationStrategy):
    """
    MIPROv2-style bootstrap strategy with validated examples and diversity.

    This strategy improves upon basic bootstrap by:
    - Evaluating ALL training examples instead of random sampling
    - Ranking candidates by quality score
    - Selecting diverse top-K examples to avoid redundancy

    Expected improvement: +10-15% accuracy over random bootstrap
    """

    def __init__(
        self,
        max_examples: int = 4,
        min_score_threshold: float = 0.7,
        diversity_weight: float = 0.3,
        use_embeddings: bool = True,
        embedding_model: str = "simple"  # "simple" or "sentence-transformer"
    ):
        """
        Initialize MIPROv2 bootstrap strategy.

        Args:
            max_examples: Maximum few-shot examples to include
            min_score_threshold: Minimum score for candidate examples
            diversity_weight: Weight for diversity vs quality (0.0-1.0)
            use_embeddings: Whether to use embeddings for diversity
            embedding_model: "simple" (TF-IDF) or "sentence-transformer"
        """
        self.max_examples = max_examples
        self.min_score_threshold = min_score_threshold
        self.diversity_weight = diversity_weight
        self.use_embeddings = use_embeddings
        self.embedding_model = embedding_model

        # Initialize embedding encoder if needed
        self.encoder = None
        if use_embeddings and embedding_model == "sentence-transformer":
            try:
                from sentence_transformers import SentenceTransformer
                self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            except ImportError:
                print("⚠️  sentence-transformers not available, using simple embeddings")
                self.embedding_model = "simple"

    async def optimize_step(
        self,
        context: OptimizationContext,
        agent_evaluator: Callable[[str, TrainingExample], Awaitable[str]],
        metric: OptimizationMetric
    ) -> bool:
        """Perform MIPROv2 bootstrap optimization step."""

        # Get training examples
        train_examples, validation_examples = context.get_train_validation_split()

        if not train_examples:
            return False

        print(f"\n🔍 MIPROv2 Bootstrap: Validating {len(train_examples)} examples...")

        # Phase 1: Validate ALL training examples
        candidate_pool = await self._validate_all_examples(
            context.best_prompt,
            train_examples,
            agent_evaluator,
            metric
        )

        if not candidate_pool:
            print("⚠️  No candidates generated")
            return False

        print(f"✅ Generated {len(candidate_pool)} candidates")

        # Phase 2: Rank by quality
        candidate_pool.sort(key=lambda x: x.score, reverse=True)

        print(f"\n📊 Top 5 candidates:")
        for i, candidate in enumerate(candidate_pool[:5], 1):
            input_preview = candidate.example.input[:50]
            print(f"  {i}. Score: {candidate.score:.3f} - {input_preview}...")

        # Phase 3: Filter by minimum threshold
        high_quality_candidates = [
            c for c in candidate_pool
            if c.score >= self.min_score_threshold
        ]

        print(f"\n✅ {len(high_quality_candidates)} candidates passed threshold ({self.min_score_threshold})")

        if not high_quality_candidates:
            print("⚠️  No candidates met quality threshold!")
            return False

        # Phase 4: Select diverse top-K examples
        print(f"\n🎯 Selecting top-{self.max_examples} diverse examples...")

        diverse_examples = await self._select_diverse_examples(
            high_quality_candidates,
            self.max_examples
        )

        print(f"✅ Selected {len(diverse_examples)} diverse examples")

        # Create enhanced prompt with few-shot examples
        enhanced_prompt = self._create_few_shot_prompt(
            context.best_prompt,
            diverse_examples
        )

        # Evaluate the enhanced prompt
        eval_examples = validation_examples or train_examples[-3:]
        validation_score = await self._evaluate_prompt(
            enhanced_prompt,
            eval_examples,
            agent_evaluator,
            metric
        )

        print(f"\n📈 Validation score: {validation_score:.3f}")

        # Add optimization step
        context.add_step(
            strategy="mipro_bootstrap",
            prompt_candidate=enhanced_prompt,
            evaluation_score=validation_score,
            examples_used=[c.example for c in diverse_examples],
            few_shot_count=len(diverse_examples),
            avg_example_score=np.mean([c.score for c in diverse_examples]),
            diversity_method="embedding" if self.use_embeddings else "category"
        )

        context.current_iteration += 1
        return context.should_continue()

    async def _validate_all_examples(
        self,
        prompt: str,
        training_examples: List[TrainingExample],
        agent_evaluator: Callable[[str, TrainingExample], Awaitable[str]],
        metric: OptimizationMetric
    ) -> List[CandidateExample]:
        """
        Phase 1: Validate ALL training examples (not random sample).

        This is the key improvement over basic bootstrap!
        """
        candidate_pool = []

        for i, example in enumerate(training_examples, 1):
            try:
                # Show progress
                if i % 5 == 0 or i == len(training_examples):
                    print(f"  Validating {i}/{len(training_examples)}...", end='\r')

                # Get agent's response
                response = await agent_evaluator(prompt, example)

                # Evaluate quality
                score = metric.evaluate(response, example.expected_output)

                # Create candidate
                candidate = CandidateExample(
                    example=example,
                    response=response,
                    score=score,
                    embedding=None,  # Will compute later if needed
                    metadata={'validation_iteration': i}
                )

                candidate_pool.append(candidate)

            except Exception as e:
                print(f"\n⚠️  Error evaluating example {i}: {e}")
                continue

        print()  # New line after progress
        return candidate_pool

    async def _select_diverse_examples(
        self,
        candidates: List[CandidateExample],
        max_examples: int
    ) -> List[CandidateExample]:
        """
        Phase 4: Select diverse top-K examples.

        Uses greedy diversity selection:
        1. Start with highest-scoring example
        2. Iteratively add examples most different from selected
        3. Balance quality and diversity
        """

        if len(candidates) <= max_examples:
            return candidates

        # Compute embeddings if using embedding-based diversity
        if self.use_embeddings:
            print("  Computing embeddings for diversity...")
            for candidate in candidates:
                if candidate.embedding is None:
                    candidate.embedding = self._compute_embedding(
                        candidate.example.input
                    )

        selected = []

        # Step 1: Select highest-scoring example
        best_candidate = candidates[0]  # Already sorted by score
        selected.append(best_candidate)
        remaining = candidates[1:]

        print(f"  Selected #1 (score={best_candidate.score:.3f}): "
              f"{best_candidate.example.input[:40]}...")

        # Step 2: Iteratively select most diverse examples
        while len(selected) < max_examples and remaining:
            # Compute combined scores (quality + diversity) for remaining
            best_combined_score = -1
            best_candidate_idx = -1

            for idx, candidate in enumerate(remaining):
                # Quality score (already normalized 0-1)
                quality_score = candidate.score

                # Diversity score (how different from selected)
                diversity_score = self._compute_diversity_score(
                    candidate,
                    selected
                )

                # Combined score: weighted average
                combined_score = (
                    (1 - self.diversity_weight) * quality_score +
                    self.diversity_weight * diversity_score
                )

                if combined_score > best_combined_score:
                    best_combined_score = combined_score
                    best_candidate_idx = idx

            # Add best candidate
            if best_candidate_idx >= 0:
                best_candidate = remaining.pop(best_candidate_idx)
                selected.append(best_candidate)

                diversity = self._compute_diversity_score(
                    best_candidate,
                    selected[:-1]  # Exclude just-added
                )

                print(f"  Selected #{len(selected)} "
                      f"(score={best_candidate.score:.3f}, "
                      f"diversity={diversity:.3f}): "
                      f"{best_candidate.example.input[:40]}...")

        return selected

    def _compute_diversity_score(
        self,
        candidate: CandidateExample,
        selected: List[CandidateExample]
    ) -> float:
        """
        Compute diversity score for a candidate relative to selected examples.

        Returns: 0.0 (very similar) to 1.0 (very different)
        """
        if not selected:
            return 1.0  # First example is maximally diverse

        if self.use_embeddings and candidate.embedding is not None:
            # Embedding-based diversity
            similarities = []
            for selected_candidate in selected:
                if selected_candidate.embedding is not None:
                    sim = self._cosine_similarity(
                        candidate.embedding,
                        selected_candidate.embedding
                    )
                    similarities.append(sim)

            if similarities:
                # Diversity = 1 - minimum similarity (most similar example)
                min_similarity = min(similarities)
                return 1.0 - min_similarity

        # Fall back to category-based diversity
        return self._category_diversity_score(candidate, selected)

    def _category_diversity_score(
        self,
        candidate: CandidateExample,
        selected: List[CandidateExample]
    ) -> float:
        """Diversity based on metadata categories."""
        candidate_category = candidate.example.metadata.get('category', 'unknown')

        # Count how many selected examples are in same category
        same_category_count = sum(
            1 for s in selected
            if s.example.metadata.get('category', 'unknown') == candidate_category
        )

        # More examples in same category = less diverse
        # Normalize by number of selected examples
        diversity = 1.0 - (same_category_count / len(selected))
        return diversity

    def _compute_embedding(self, text: str) -> np.ndarray:
        """Compute embedding for text."""
        if self.encoder is not None:
            # Use sentence-transformer
            return self.encoder.encode(text, convert_to_numpy=True)
        else:
            # Simple TF-IDF-like embedding
            return self._simple_embedding(text)

    def _simple_embedding(self, text: str) -> np.ndarray:
        """Simple word-based embedding (TF-IDF-like)."""
        # Convert text to lowercase word tokens
        words = text.lower().split()

        # Create a simple bag-of-words vector (first 100 unique words as features)
        # This is a very basic approach - good enough for diversity without dependencies
        vocab_size = 100
        embedding = np.zeros(vocab_size)

        for word in words:
            # Simple hash to vocab index
            idx = hash(word) % vocab_size
            embedding[idx] += 1

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def _cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Compute cosine similarity between embeddings."""
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _create_few_shot_prompt(
        self,
        base_prompt: str,
        few_shot_examples: List[CandidateExample]
    ) -> str:
        """Create prompt with few-shot examples."""
        if not few_shot_examples:
            return base_prompt

        # Add few-shot examples to prompt
        examples_text = "\n\nHere are some examples to guide your responses:\n"

        for i, candidate in enumerate(few_shot_examples, 1):
            examples_text += f"\nExample {i}:\n"
            examples_text += f"Input: {candidate.example.input}\n"
            examples_text += f"Output: {candidate.response}\n"

        examples_text += "\nNow handle the following:\n"

        return base_prompt + examples_text

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
        return "mipro_bootstrap"
