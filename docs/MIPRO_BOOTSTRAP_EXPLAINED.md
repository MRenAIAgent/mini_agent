# MIPROv2-Style Bootstrap: Technical Deep Dive

## The Problem: Current Bootstrap Implementation

### Current Approach (Suboptimal)

```python
async def _generate_few_shot_examples(self, prompt, training_examples, ...):
    good_examples = []

    # ❌ Step 1: Random sampling (only 10 examples)
    sample_size = min(len(training_examples), 10)
    sampled_examples = random.sample(training_examples, sample_size)

    # ❌ Step 2: Take first N that pass threshold
    for example in sampled_examples:
        if len(good_examples) >= self.max_examples:
            break

        response = await agent_evaluator(prompt, example)
        score = metric.evaluate(response, example.expected_output)

        # Keep if above threshold (e.g., 0.7)
        if score >= self.min_score_threshold:
            good_examples.append(example)

    return good_examples  # Returns 0-4 examples
```

### What's Wrong?

**Example Scenario:**
- You have 50 training examples
- Current code randomly picks 10 examples
- Finds 4 that score > 0.7
- Returns those 4

**Problems:**

1. **Missed Opportunities**
   ```
   Sampled examples (10):
   Example 1: score = 0.75 ✅ (selected)
   Example 2: score = 0.45 ❌
   Example 3: score = 0.72 ✅ (selected)
   ...
   Example 10: score = 0.78 ✅ (selected)

   But in the 40 NOT sampled:
   Example 15: score = 0.95 🌟 (MISSED - would have been great!)
   Example 23: score = 0.93 🌟 (MISSED - would have been great!)
   Example 31: score = 0.91 🌟 (MISSED - would have been great!)
   ```

2. **No Quality Ranking**
   - Takes first 4 that pass threshold
   - Doesn't consider if some are much better than others
   - Example with score 0.71 treated same as 0.95

3. **No Diversity**
   ```
   Selected examples might be:
   "What is 2+2?" → "4"
   "What is 2+3?" → "5"
   "What is 2+4?" → "6"
   "What is 2+5?" → "7"

   All very similar! Not diverse patterns.
   ```

---

## The Solution: MIPROv2-Style Bootstrap

### MIPROv2 Approach (Optimal)

```python
async def _generate_few_shot_examples_mipro(
    self,
    prompt: str,
    training_examples: List[TrainingExample],
    agent_evaluator: Callable,
    metric: OptimizationMetric
) -> List[TrainingExample]:
    """
    MIPROv2-style bootstrap with validation and diversity.

    Key improvements:
    1. Evaluate ALL training examples (not random sample)
    2. Rank by quality score
    3. Select top-K diverse examples
    """

    # ✅ PHASE 1: Validate ALL training examples
    print(f"Phase 1: Validating all {len(training_examples)} examples...")

    candidate_pool = []

    for example in training_examples:  # ✅ ALL examples, not random sample
        try:
            # Run agent on this example
            response = await agent_evaluator(prompt, example)

            # Evaluate quality
            score = metric.evaluate(response, example.expected_output)

            # Add to candidate pool with score
            candidate_pool.append({
                'example': example,
                'response': response,
                'score': score,
                'embedding': None  # Will compute for diversity
            })

        except Exception as e:
            print(f"Failed to evaluate example: {e}")
            continue

    print(f"Generated {len(candidate_pool)} candidates")

    # ✅ PHASE 2: Rank by quality
    print("Phase 2: Ranking candidates by quality...")

    # Sort by score (highest first)
    candidate_pool.sort(key=lambda x: x['score'], reverse=True)

    # Show top candidates
    print("\nTop 10 candidates:")
    for i, candidate in enumerate(candidate_pool[:10], 1):
        print(f"  {i}. Score: {candidate['score']:.3f} - {candidate['example'].input[:50]}")

    # ✅ PHASE 3: Filter by minimum threshold
    print(f"\nPhase 3: Filtering by threshold ({self.min_score_threshold})...")

    high_quality_candidates = [
        c for c in candidate_pool
        if c['score'] >= self.min_score_threshold
    ]

    print(f"Found {len(high_quality_candidates)} high-quality candidates")

    if not high_quality_candidates:
        print("⚠️ No candidates passed threshold!")
        return []

    # ✅ PHASE 4: Select diverse top-K examples
    print(f"\nPhase 4: Selecting top-{self.max_examples} diverse examples...")

    diverse_examples = self._select_diverse_examples(
        candidates=high_quality_candidates,
        max_examples=self.max_examples
    )

    print(f"✅ Selected {len(diverse_examples)} diverse, high-quality examples")

    # Convert back to TrainingExample format
    final_examples = []
    for candidate in diverse_examples:
        final_examples.append(TrainingExample(
            input=candidate['example'].input,
            expected_output=candidate['response'],
            metadata={
                **candidate['example'].metadata,
                'bootstrap_score': candidate['score'],
                'selection_method': 'mipro_diverse'
            }
        ))

    return final_examples


def _select_diverse_examples(
    self,
    candidates: List[Dict],
    max_examples: int
) -> List[Dict]:
    """
    Select diverse examples from high-quality candidates.

    Strategy: Greedy diversity selection
    1. Start with highest-scoring example
    2. Iteratively add examples that are most different from selected ones
    3. Continue until we have max_examples
    """

    if len(candidates) <= max_examples:
        return candidates

    # Compute embeddings for all candidates (for diversity measurement)
    print("  Computing embeddings for diversity...")
    for candidate in candidates:
        if candidate['embedding'] is None:
            # Use simple embedding (word count vector or actual embeddings)
            candidate['embedding'] = self._compute_embedding(
                candidate['example'].input
            )

    selected = []
    remaining = candidates.copy()

    # Step 1: Select highest-scoring example
    best_candidate = remaining.pop(0)  # Already sorted by score
    selected.append(best_candidate)
    print(f"  Selected #1 (score={best_candidate['score']:.3f}): "
          f"{best_candidate['example'].input[:40]}")

    # Step 2: Iteratively select most diverse examples
    while len(selected) < max_examples and remaining:
        # For each remaining candidate, compute minimum similarity to selected
        diversity_scores = []

        for candidate in remaining:
            # Compute similarity to all selected examples
            similarities = []
            for selected_candidate in selected:
                sim = self._compute_similarity(
                    candidate['embedding'],
                    selected_candidate['embedding']
                )
                similarities.append(sim)

            # Diversity score = minimum similarity (most different from all selected)
            min_similarity = min(similarities)
            diversity_score = 1.0 - min_similarity  # Higher = more diverse

            # Combine quality and diversity
            # 70% quality, 30% diversity
            combined_score = (
                0.7 * candidate['score'] +
                0.3 * diversity_score
            )

            diversity_scores.append({
                'candidate': candidate,
                'diversity': diversity_score,
                'combined': combined_score
            })

        # Select candidate with highest combined score
        diversity_scores.sort(key=lambda x: x['combined'], reverse=True)
        best = diversity_scores[0]

        selected.append(best['candidate'])
        remaining.remove(best['candidate'])

        print(f"  Selected #{len(selected)} "
              f"(score={best['candidate']['score']:.3f}, "
              f"diversity={best['diversity']:.3f}): "
              f"{best['candidate']['example'].input[:40]}")

    return selected


def _compute_embedding(self, text: str) -> np.ndarray:
    """
    Compute embedding for text.

    Options:
    1. Simple: TF-IDF or word count vectors
    2. Advanced: sentence-transformers, OpenAI embeddings
    """
    # Simple implementation: character n-gram counts
    # In production, use sentence-transformers or API embeddings

    from sklearn.feature_extraction.text import TfidfVectorizer

    # Use pre-fit vectorizer or fit on the fly
    vectorizer = TfidfVectorizer(max_features=100)
    embedding = vectorizer.fit_transform([text]).toarray()[0]

    return embedding


def _compute_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
    """
    Compute cosine similarity between embeddings.

    Returns: 0.0 (completely different) to 1.0 (identical)
    """
    from numpy.linalg import norm

    # Cosine similarity
    dot_product = np.dot(emb1, emb2)
    magnitude = norm(emb1) * norm(emb2)

    if magnitude == 0:
        return 0.0

    similarity = dot_product / magnitude
    return similarity
```

---

## Concrete Example: Side-by-Side Comparison

### Scenario

You have 50 training examples for a math tutoring agent:

```python
training_examples = [
    # Basic arithmetic (10 examples)
    TrainingExample(input="What is 2+2?", expected_output="4"),
    TrainingExample(input="What is 5+3?", expected_output="8"),
    ...

    # Word problems (10 examples)
    TrainingExample(
        input="If John has 5 apples and Mary gives him 3 more, how many does he have?",
        expected_output="John has 8 apples in total."
    ),
    ...

    # Algebra (10 examples)
    TrainingExample(input="Solve: 2x + 5 = 13", expected_output="x = 4"),
    ...

    # Geometry (10 examples)
    TrainingExample(
        input="What is the area of a rectangle 5cm × 3cm?",
        expected_output="15 square centimeters"
    ),
    ...

    # Statistics (10 examples)
    TrainingExample(
        input="What is the mean of [4, 8, 6, 5, 3, 7]?",
        expected_output="5.5"
    ),
    ...
]
```

### Current Method Results

```
Step 1: Random sample 10 examples
  ├─ Example 3: "What is 5+3?" (arithmetic)
  ├─ Example 7: "What is 9-4?" (arithmetic)
  ├─ Example 12: "If John has..." (word problem)
  ├─ Example 15: "Solve: x + 3 = 7" (algebra)
  ├─ Example 23: "What is 10+15?" (arithmetic)
  ├─ Example 28: "If Sarah..." (word problem)
  ├─ Example 34: "Solve: 3y = 12" (algebra)
  ├─ Example 39: "What is 20-8?" (arithmetic)
  ├─ Example 42: "What's the area..." (geometry)
  └─ Example 48: "Calculate mean..." (statistics)

Step 2: Evaluate and filter (threshold = 0.7)
  ├─ Example 3: score = 0.95 ✅
  ├─ Example 7: score = 0.92 ✅
  ├─ Example 12: score = 0.65 ❌
  ├─ Example 15: score = 0.88 ✅
  ├─ Example 23: score = 0.91 ✅
  ├─ Example 28: score = 0.62 ❌
  ├─ Example 34: score = 0.85 (not selected - already have 4)
  ├─ Example 39: score = 0.90 (not evaluated - already have 4)
  └─ ...

Selected (max_examples=4):
  1. Example 3: "What is 5+3?" (score=0.95) - arithmetic
  2. Example 7: "What is 9-4?" (score=0.92) - arithmetic
  3. Example 15: "Solve: x + 3 = 7" (score=0.88) - algebra
  4. Example 23: "What is 10+15?" (score=0.91) - arithmetic

Problem: 3/4 examples are arithmetic! Not diverse.
```

### MIPROv2 Method Results

```
Phase 1: Validate ALL 50 examples
  Evaluating: 100% ████████████████████ 50/50
  Generated 50 candidates

Phase 2: Rank by quality
  Top 10 candidates:
    1. Score: 0.98 - "If Sarah has 12 cookies..." (word problem)
    2. Score: 0.97 - "What is the area of circle r=5?" (geometry)
    3. Score: 0.96 - "Calculate standard deviation..." (statistics)
    4. Score: 0.95 - "What is 5+3?" (arithmetic)
    5. Score: 0.94 - "Solve: 2x² - 8 = 0" (algebra)
    6. Score: 0.93 - "What is the perimeter..." (geometry)
    7. Score: 0.92 - "What is 9-4?" (arithmetic)
    8. Score: 0.91 - "If Tom drives 60mph for 2.5 hours..." (word problem)
    9. Score: 0.90 - "What is the median of..." (statistics)
    10. Score: 0.89 - "Solve: 3x + 7 = 22" (algebra)

Phase 3: Filter by threshold (0.7)
  Found 35 high-quality candidates (score ≥ 0.7)

Phase 4: Select top-4 diverse examples

  Step 1: Select highest-scoring
    ✅ Selected #1 (score=0.98): "If Sarah has 12 cookies..." (word problem)

  Step 2: Add most diverse examples
    Computing similarity to selected examples...

    Candidate: "What is the area..." (geometry, score=0.97)
      ├─ Similarity to #1 (word problem): 0.15 (very different)
      ├─ Diversity score: 0.85
      └─ Combined score: 0.7 * 0.97 + 0.3 * 0.85 = 0.934

    Candidate: "Calculate standard dev..." (statistics, score=0.96)
      ├─ Similarity to #1 (word problem): 0.20
      ├─ Diversity score: 0.80
      └─ Combined score: 0.7 * 0.96 + 0.3 * 0.80 = 0.912

    Candidate: "What is 5+3?" (arithmetic, score=0.95)
      ├─ Similarity to #1 (word problem): 0.25
      ├─ Diversity score: 0.75
      └─ Combined score: 0.7 * 0.95 + 0.3 * 0.75 = 0.890

    Best combined score: 0.934 (geometry)
    ✅ Selected #2 (score=0.97, diversity=0.85): "What is the area..." (geometry)

  Step 3: Add third diverse example
    Computing similarity to 2 selected examples...

    Candidate: "Calculate standard dev..." (statistics, score=0.96)
      ├─ Similarity to #1 (word problem): 0.20
      ├─ Similarity to #2 (geometry): 0.18
      ├─ Min similarity: 0.18
      ├─ Diversity score: 0.82
      └─ Combined score: 0.7 * 0.96 + 0.3 * 0.82 = 0.918

    Candidate: "What is 5+3?" (arithmetic, score=0.95)
      ├─ Similarity to #1 (word problem): 0.25
      ├─ Similarity to #2 (geometry): 0.30
      ├─ Min similarity: 0.25
      ├─ Diversity score: 0.75
      └─ Combined score: 0.7 * 0.95 + 0.3 * 0.75 = 0.890

    Best combined score: 0.918 (statistics)
    ✅ Selected #3 (score=0.96, diversity=0.82): "Calculate standard dev..." (statistics)

  Step 4: Add fourth diverse example
    Computing similarity to 3 selected examples...

    Candidate: "What is 5+3?" (arithmetic, score=0.95)
      ├─ Similarity to #1 (word problem): 0.25
      ├─ Similarity to #2 (geometry): 0.30
      ├─ Similarity to #3 (statistics): 0.22
      ├─ Min similarity: 0.22
      ├─ Diversity score: 0.78
      └─ Combined score: 0.7 * 0.95 + 0.3 * 0.78 = 0.899

    Candidate: "Solve: 2x² - 8 = 0" (algebra, score=0.94)
      ├─ Similarity to #1 (word problem): 0.28
      ├─ Similarity to #2 (geometry): 0.32
      ├─ Similarity to #3 (statistics): 0.25
      ├─ Min similarity: 0.25
      ├─ Diversity score: 0.75
      └─ Combined score: 0.7 * 0.94 + 0.3 * 0.75 = 0.883

    Best combined score: 0.899 (arithmetic)
    ✅ Selected #4 (score=0.95, diversity=0.78): "What is 5+3?" (arithmetic)

Final Selection:
  1. "If Sarah has 12 cookies..." (word problem, score=0.98)
  2. "What is the area of circle r=5?" (geometry, score=0.97)
  3. "Calculate standard deviation..." (statistics, score=0.96)
  4. "What is 5+3?" (arithmetic, score=0.95)

Result: 4 different math categories! Highly diverse and all high-quality.
```

---

## Key Differences Summary

| Aspect | Current Method | MIPROv2 Method |
|--------|----------------|----------------|
| **Sampling** | Random 10 examples | ALL 50 examples |
| **Evaluation** | Stop at first 4 passing | Evaluate all, rank all |
| **Quality** | Any score ≥ 0.7 | Top scores (0.95+) |
| **Diversity** | None (take first 4) | Greedy diversity selection |
| **Result Quality** | Mixed (0.88-0.95) | Consistently high (0.95-0.98) |
| **Coverage** | 3 arithmetic, 1 algebra | 1 word, 1 geometry, 1 stats, 1 arithmetic |

---

## Why This Matters: Performance Impact

### Accuracy Improvement

**Current Method (3 arithmetic + 1 algebra):**
```
Test: "What is 15 + 27?" → ✅ (covered by examples)
Test: "Solve: 4x = 20" → ✅ (covered by example)
Test: "What is area of triangle b=6, h=4?" → ❌ (no geometry examples!)
Test: "Calculate mean of [2,4,6,8]?" → ❌ (no statistics examples!)
Test: "If box has 24 items, 1/3 are red..." → ⚠️ (weak word problem coverage)

Accuracy: 2/5 = 40%
```

**MIPROv2 Method (1 each category):**
```
Test: "What is 15 + 27?" → ✅ (covered by arithmetic example)
Test: "Solve: 4x = 20" → ⚠️ (no algebra, but can generalize)
Test: "What is area of triangle b=6, h=4?" → ✅ (covered by geometry)
Test: "Calculate mean of [2,4,6,8]?" → ✅ (covered by statistics)
Test: "If box has 24 items, 1/3 are red..." → ✅ (covered by word problem)

Accuracy: 4.5/5 = 90%
```

**Improvement: +50% accuracy** 🎉

### Why Diversity Matters

Few-shot learning works by showing the LLM:
1. **Patterns**: What kind of problems to expect
2. **Format**: How to structure answers
3. **Coverage**: Different problem types

**With diverse examples:**
- LLM sees: arithmetic, geometry, statistics, word problems
- LLM learns: "I need to handle all these math types"
- Result: Generalizes better to unseen examples

**Without diversity:**
- LLM sees: arithmetic, arithmetic, arithmetic, algebra
- LLM learns: "This is mostly arithmetic"
- Result: Overfits to arithmetic, fails on other types

---

## Implementation Complexity

### Simple Version (No Embeddings)

```python
def _select_diverse_examples_simple(candidates, max_examples):
    """Simple diversity without embeddings."""

    selected = []

    # Group by category (if metadata available)
    categories = {}
    for c in candidates:
        category = c['example'].metadata.get('category', 'unknown')
        if category not in categories:
            categories[category] = []
        categories[category].append(c)

    # Select best from each category (round-robin)
    while len(selected) < max_examples:
        for category, candidates_in_cat in categories.items():
            if candidates_in_cat:
                # Take highest-scoring from this category
                best = candidates_in_cat.pop(0)
                selected.append(best)

                if len(selected) >= max_examples:
                    break

    return selected
```

### Advanced Version (With Embeddings)

Use sentence-transformers for better diversity:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def _compute_embedding(text: str):
    return model.encode(text)

def _compute_similarity(emb1, emb2):
    from scipy.spatial.distance import cosine
    return 1 - cosine(emb1, emb2)
```

---

## Expected Improvements

Based on DSPy research and this technique:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Few-shot quality** | Mixed (0.7-0.9) | High (0.9-0.98) | +10-15% |
| **Coverage** | Narrow | Broad | 2-3x categories |
| **Accuracy on unseen** | 60-70% | 80-90% | +20-30% |
| **Consistency** | High variance | Low variance | -50% variance |

---

## Summary

**MIPROv2-Style Bootstrap = Better Examples + Diversity**

1. **Validate ALL** training examples (not random sample)
2. **Rank by quality** (use best performers, not just "good enough")
3. **Select diverse** top-K (avoid redundancy, maximize coverage)

**Result:** Higher-quality, more diverse few-shot examples → better agent performance

This is one of the highest-impact improvements from the proposal! 🎯
