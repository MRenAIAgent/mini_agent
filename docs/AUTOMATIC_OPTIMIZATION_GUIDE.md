# Automatic Prompt Optimization Guide

**Yes! mini_agent has DSPy-inspired automatic optimization built-in** ✅

This guide shows you how to use the automatic prompt optimization system that's already in the repository.

---

## Quick Answer

**You have 3 automatic optimization strategies available:**

1. **Bootstrap** - Automatic few-shot example generation
2. **Coordinate Ascent (COPRO)** - Iterative prompt refinement
3. **Bayesian** - Exploration/exploitation optimization

---

## Method 1: Agent-Level Optimization (Easiest)

### Basic Usage

```python
from agent import CoreAgent

# Create agent with optimization enabled
agent = CoreAgent(
    llm_function=your_llm_function,
    system_prompt="You are a helpful assistant.",
    enable_optimization=True  # ✅ Enable automatic optimization
)

await agent.start()

# Prepare training examples
training_examples = [
    {"input": "What is 2 + 2?", "output": "The answer is 4."},
    {"input": "Calculate 5 * 3", "output": "The answer is 15."},
    # ... more examples
]

# Run automatic optimization
improved = await agent.optimize_prompt(
    training_examples=training_examples,
    strategy="bootstrap"  # or "coordinate_ascent", "bayesian"
)

if improved:
    print("✅ Prompt optimized successfully!")
    # Agent now uses the optimized prompt automatically
```

### Available Strategies

```python
# Bootstrap: Generate high-quality few-shot examples
await agent.optimize_prompt(training_examples, strategy="bootstrap")

# Coordinate Ascent: Iterative prompt refinement (COPRO-inspired)
await agent.optimize_prompt(training_examples, strategy="coordinate_ascent")

# Bayesian: Smart exploration/exploitation
await agent.optimize_prompt(training_examples, strategy="bayesian")
```

### Check Optimization Results

```python
# After optimization, check the results
if agent.optimization_history:
    last_result = agent.optimization_history[-1]

    print(f"Strategy: {last_result['strategy_used']}")
    print(f"Improvement: {last_result['improvement']:.2%}")
    print(f"Initial Score: {last_result['initial_score']:.2%}")
    print(f"Final Score: {last_result['final_score']:.2%}")
    print(f"Iterations: {last_result['iterations_taken']}")
    print(f"Time: {last_result['execution_time']:.2f}s")
    print(f"\nOptimized Prompt:\n{last_result['optimized_prompt']}")
```

---

## Method 2: Direct CoreOptimizer Usage (Advanced)

### Basic Setup

```python
from optimization import CoreOptimizer, TrainingExample

# Create optimizer with custom settings
optimizer = CoreOptimizer(
    strategy="bootstrap",           # Strategy to use
    max_iterations=10,              # Max optimization iterations
    convergence_threshold=0.95,     # Stop when 95% accuracy reached
    timeout_seconds=300             # 5-minute timeout
)
```

### Prepare Training Data

```python
# Create training examples
training_examples = [
    TrainingExample(
        input="What is 2 + 2?",
        expected_output="The answer is 4.",
        metadata={"difficulty": "easy", "category": "math"}
    ),
    TrainingExample(
        input="Calculate 5 * 3",
        expected_output="The answer is 15.",
        metadata={"difficulty": "easy", "category": "math"}
    ),
    # ... more examples
]
```

### Create Agent Evaluator

```python
async def agent_evaluator(prompt: str, example: TrainingExample) -> str:
    """
    Evaluate agent performance with a specific prompt.

    Args:
        prompt: The candidate prompt to evaluate
        example: Training example to test on

    Returns:
        Agent's response
    """
    # Build full prompt
    full_prompt = f"{prompt}\n\nUser: {example.input}\nAssistant:"

    # Call your LLM
    response = await your_llm_function(full_prompt)

    return response
```

### Run Optimization

```python
# Run optimization
result = await optimizer.optimize(
    initial_prompt="You are a helpful assistant.",
    training_examples=training_examples,
    agent_evaluator=agent_evaluator,
    optimization_target="accuracy"
)

# Check results
if result.success:
    print(f"✅ Optimization successful!")
    print(f"Improvement: {result.improvement:.2%}")
    print(f"Optimized prompt: {result.optimized_prompt}")
else:
    print(f"⚠️ Optimization failed: {result.error}")
```

### Optimization Result Object

```python
class OptimizationResult:
    success: bool                    # Whether optimization succeeded
    initial_prompt: str              # Original prompt
    optimized_prompt: str            # Improved prompt
    initial_score: float             # Baseline score (0.0-1.0)
    final_score: float               # Final score (0.0-1.0)
    improvement: float               # Improvement delta
    iterations_taken: int            # Iterations used
    execution_time: float            # Time in seconds
    api_calls: int                   # Number of LLM calls made
    strategy_used: str               # Strategy name
    optimization_history: List[Dict] # Step-by-step history
    error: Optional[str]             # Error message if failed
```

---

## Method 3: Custom Optimization Strategy

### Create Custom Strategy

```python
from optimization.optimization_strategies import OptimizationStrategy

class CustomStrategy(OptimizationStrategy):
    """Your custom optimization algorithm."""

    async def optimize_step(
        self,
        context: OptimizationContext,
        agent_evaluator: Callable,
        metric: OptimizationMetric
    ) -> bool:
        """Perform one optimization step."""

        # 1. Generate candidate prompts
        candidates = self._generate_candidates(context.best_prompt)

        # 2. Evaluate each candidate
        train_examples, val_examples = context.get_train_validation_split()

        best_score = 0.0
        best_candidate = context.best_prompt

        for candidate in candidates:
            # Evaluate on validation set
            scores = []
            for example in val_examples:
                response = await agent_evaluator(candidate, example)
                score = metric.evaluate(response, example.expected_output)
                scores.append(score)

            avg_score = sum(scores) / len(scores)

            if avg_score > best_score:
                best_score = avg_score
                best_candidate = candidate

            # Log this step
            context.add_step(
                strategy="custom",
                prompt_candidate=candidate,
                evaluation_score=avg_score,
                examples_used=val_examples
            )

        # 3. Continue if not converged
        context.current_iteration += 1
        return context.should_continue()

    def get_name(self) -> str:
        return "custom_strategy"
```

### Use Custom Strategy

```python
# Create optimizer with custom strategy
custom_strategy = CustomStrategy()

optimizer = CoreOptimizer(
    strategy=custom_strategy,
    max_iterations=10
)

result = await optimizer.optimize(...)
```

---

## Method 4: Quick Optimization (Simplified)

For simple use cases, use the quick optimization API:

```python
optimizer = CoreOptimizer(strategy="bootstrap")

# Simple evaluator: (prompt, input) -> output
async def simple_evaluator(prompt: str, input_text: str) -> str:
    return await your_llm(f"{prompt}\n{input_text}")

# Simple examples: list of dicts
examples = [
    {"input": "What is 2+2?", "output": "4"},
    {"input": "What is 5*3?", "output": "15"},
]

# Quick optimize
optimized_prompt = await optimizer.quick_optimize(
    initial_prompt="You are a math assistant.",
    examples=examples,
    agent_evaluator=simple_evaluator
)

print(f"Optimized prompt: {optimized_prompt}")
```

---

## Optimization Strategies Explained

### 1. Bootstrap Strategy

**How it works:**
1. Runs agent on training examples with current prompt
2. Keeps examples where agent performed well (above threshold)
3. Adds successful examples as few-shot demonstrations to prompt
4. Evaluates enhanced prompt on validation set

**Best for:**
- Tasks that benefit from examples (few-shot learning)
- When you have diverse training data
- Classification, Q&A, structured outputs

**Configuration:**
```python
from optimization import BootstrapStrategy

strategy = BootstrapStrategy(
    max_examples=4,              # Max few-shot examples to include
    min_score_threshold=0.7,     # Min score to consider example "good"
    example_selection_rounds=3   # Rounds of example generation
)

optimizer = CoreOptimizer(strategy=strategy)
```

### 2. Coordinate Ascent (COPRO-inspired)

**How it works:**
1. Generates multiple prompt variations (adding instructions)
2. Evaluates each variation on validation set
3. Keeps best-performing variation
4. Repeats for multiple iterations (hill climbing)

**Best for:**
- Instruction-based optimization
- Quick convergence
- Tasks where guidance/rules help

**Configuration:**
```python
from optimization import CoordinateAscentStrategy

strategy = CoordinateAscentStrategy(
    candidates_per_iteration=3,  # Prompt variations per iteration
    prompt_variations=[          # Custom instruction variations
        "Be specific and detailed.",
        "Think step by step.",
        "Provide clear reasoning."
    ]
)

optimizer = CoreOptimizer(strategy=strategy)
```

### 3. Bayesian Strategy

**How it works:**
1. Balances exploration (trying new prompts) vs exploitation (refining best)
2. Uses exploration factor to control randomness
3. Gradually refines most promising prompt

**Best for:**
- When search space is large
- Need to avoid local optima
- Uncertain about best approach

**Configuration:**
```python
from optimization import BayesianStrategy

strategy = BayesianStrategy(
    exploration_factor=0.1,      # 10% exploration, 90% exploitation
    prompt_templates=[           # Template variations to try
        "{base_prompt}\n\nBe detailed and accurate.",
        "Task: {base_prompt}\n\nApproach systematically.",
    ]
)

optimizer = CoreOptimizer(strategy=strategy)
```

---

## Custom Metrics

By default, the optimizer uses **AccuracyMetric** (exact match). You can create custom metrics:

```python
from optimization.metrics import OptimizationMetric

class CustomMetric(OptimizationMetric):
    """Custom evaluation metric."""

    def evaluate(self, predicted: str, expected: str) -> float:
        """
        Evaluate prediction quality.

        Args:
            predicted: Agent's response
            expected: Expected output

        Returns:
            Score from 0.0 (worst) to 1.0 (best)
        """
        # Your custom evaluation logic
        # Example: Semantic similarity
        similarity = compute_similarity(predicted, expected)
        return similarity

    def get_name(self) -> str:
        return "custom_metric"

# Use custom metric
optimizer = CoreOptimizer(
    strategy="bootstrap",
    metric=CustomMetric()
)
```

### Built-in Metrics

```python
from optimization.metrics import AccuracyMetric, EfficiencyMetric

# Exact match accuracy
accuracy_metric = AccuracyMetric()

# Efficiency (shorter responses preferred)
efficiency_metric = EfficiencyMetric()

# Use in optimizer
optimizer = CoreOptimizer(metric=accuracy_metric)
```

---

## Best Practices

### 1. Prepare Good Training Data

```python
# ✅ Good: Diverse, representative examples
training_examples = [
    TrainingExample(
        input="Easy question",
        expected_output="Simple answer",
        metadata={"difficulty": "easy"}
    ),
    TrainingExample(
        input="Moderate complexity question",
        expected_output="Detailed answer with reasoning",
        metadata={"difficulty": "medium"}
    ),
    TrainingExample(
        input="Complex multi-step problem",
        expected_output="Comprehensive answer with steps",
        metadata={"difficulty": "hard"}
    )
]

# ❌ Bad: Redundant, not representative
training_examples = [
    TrainingExample(input="What is 2+2?", expected_output="4"),
    TrainingExample(input="What is 2+3?", expected_output="5"),
    TrainingExample(input="What is 2+4?", expected_output="6"),
    # All similar, not diverse
]
```

### 2. Start with Bootstrap

Bootstrap strategy usually gives best initial results:

```python
# Start with bootstrap
result_bootstrap = await optimizer.optimize(
    initial_prompt=initial_prompt,
    training_examples=examples,
    agent_evaluator=evaluator
)

# If not satisfied, try coordinate ascent
optimizer.set_strategy("coordinate_ascent")
result_copro = await optimizer.optimize(...)
```

### 3. Use Appropriate Iteration Limits

```python
# Development: Fast iterations
optimizer = CoreOptimizer(
    max_iterations=3,      # Quick feedback
    timeout_seconds=60     # 1 minute
)

# Production: Thorough optimization
optimizer = CoreOptimizer(
    max_iterations=20,     # More thorough
    timeout_seconds=600    # 10 minutes
)
```

### 4. Monitor Progress

```python
result = await optimizer.optimize(...)

# Check optimization history
print(f"\n📈 Optimization Progress:")
for i, step in enumerate(result.optimization_history, 1):
    print(f"Step {i}: {step['evaluation_score']:.2%} "
          f"({step['strategy']})")

# Visualize improvement
import matplotlib.pyplot as plt

scores = [step['evaluation_score'] for step in result.optimization_history]
plt.plot(scores)
plt.xlabel('Iteration')
plt.ylabel('Score')
plt.title('Optimization Progress')
plt.show()
```

### 5. Save Optimization Results

```python
import json

# Save result
result_dict = result.to_dict()

with open('optimization_result.json', 'w') as f:
    json.dump(result_dict, f, indent=2)

# Load result later
with open('optimization_result.json', 'r') as f:
    loaded_result = json.load(f)

optimized_prompt = loaded_result['optimized_prompt']
```

---

## Comparison with DSPy

| Feature | mini_agent | DSPy |
|---------|------------|------|
| **Bootstrap Few-Shot** | ✅ Yes | ✅ Yes |
| **COPRO (Coordinate Ascent)** | ✅ Yes | ✅ Yes |
| **Bayesian Optimization** | ⚠️ Simplified | ✅ Full GP |
| **MIPROv2** | ❌ Not yet | ✅ Yes |
| **Signature System** | ❌ Not yet | ✅ Yes |
| **Error Analysis (SIMBA)** | ❌ Not yet | ✅ Yes |
| **Prompt Compression** | ❌ Not yet | ❌ No |
| **Custom Metrics** | ✅ Yes | ✅ Yes |
| **Async/Await** | ✅ Yes | ⚠️ Limited |
| **Zero Dependencies** | ✅ Yes | ❌ Heavy deps |

**See**: `docs/PROMPT_OPTIMIZATION_PROPOSAL.md` for planned enhancements to reach feature parity with DSPy 2025.

---

## Troubleshooting

### Optimization Not Improving

```python
# 1. Check baseline score
result = await optimizer.optimize(...)
print(f"Baseline: {result.initial_score:.2%}")

# If baseline is already high (>90%), optimization may not help much

# 2. Try different strategy
optimizer.set_strategy("coordinate_ascent")  # Try different approach

# 3. Add more training examples
# Need at least 5-10 diverse examples

# 4. Lower convergence threshold
optimizer = CoreOptimizer(
    convergence_threshold=0.85  # Lower threshold
)
```

### Optimization Too Slow

```python
# 1. Reduce iterations
optimizer = CoreOptimizer(max_iterations=5)

# 2. Use smaller validation set
# Optimization will automatically split train/val

# 3. Use faster LLM for optimization
async def fast_evaluator(prompt, example):
    return await fast_llm(prompt)  # Use smaller model
```

### Out of Memory

```python
# 1. Process examples in batches
# CoreOptimizer automatically handles this

# 2. Reduce max_examples in Bootstrap
strategy = BootstrapStrategy(max_examples=2)  # Fewer examples

# 3. Use streaming evaluation
# (Feature coming in next version)
```

---

## Examples

See **`examples/prompt_optimization_example.py`** for complete working examples:

```bash
# Run the example
cd /home/user/mini_agent
python examples/prompt_optimization_example.py
```

The example demonstrates:
- ✅ Basic agent-level optimization
- ✅ All three strategies (bootstrap, coordinate ascent, bayesian)
- ✅ Advanced CoreOptimizer usage
- ✅ Strategy comparison
- ✅ Results visualization

---

## Next Steps

1. **Try the example**: Run `examples/prompt_optimization_example.py`
2. **Use with your agent**: Enable optimization in your agent
3. **Customize**: Create custom strategies and metrics
4. **Monitor**: Track optimization results and improvements
5. **Contribute**: See `docs/PROMPT_OPTIMIZATION_PROPOSAL.md` for enhancement opportunities

---

## References

- **Core Implementation**: `optimization/core_optimizer.py`
- **Strategies**: `optimization/optimization_strategies.py`
- **Enhancement Proposal**: `docs/PROMPT_OPTIMIZATION_PROPOSAL.md`
- **Agent Integration**: `agent.py:582-634` (optimize_prompt method)
- **DSPy Documentation**: https://dspy.ai/learn/optimization/optimizers/

---

**Questions?** Check the examples or open an issue!
