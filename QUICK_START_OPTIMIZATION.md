# Quick Start: Automatic Prompt Optimization

## ✅ YES! You Have Automatic Optimization Like DSPy

Your mini_agent already has a **DSPy-inspired automatic prompt optimization system** built-in!

---

## 🚀 Quick Start (30 seconds)

```python
from agent import CoreAgent

# 1. Create agent with optimization enabled
agent = CoreAgent(
    llm_function=your_llm,
    system_prompt="You are a helpful assistant.",
    enable_optimization=True  # ✅ This enables automatic optimization
)

await agent.start()

# 2. Prepare training examples
examples = [
    {"input": "Question 1", "output": "Expected answer 1"},
    {"input": "Question 2", "output": "Expected answer 2"},
    # Add 5-10 diverse examples
]

# 3. Run automatic optimization
improved = await agent.optimize_prompt(
    training_examples=examples,
    strategy="bootstrap"  # or "coordinate_ascent", "bayesian"
)

# 4. Done! Agent now uses optimized prompt
if improved:
    print("✅ Prompt automatically optimized!")
```

That's it! The agent will automatically improve its prompt using your training data.

---

## 🎯 What You Have

### Three Optimization Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| **Bootstrap** | Generates few-shot examples | Classification, Q&A, structured tasks |
| **Coordinate Ascent** | Iterative instruction refinement | Quick convergence, instruction-based tasks |
| **Bayesian** | Smart exploration/exploitation | Large search spaces, avoiding local optima |

### Key Features

✅ **Automatic prompt improvement** - No manual prompt engineering
✅ **Multiple strategies** - Bootstrap, Coordinate Ascent, Bayesian
✅ **Custom metrics** - Define your own evaluation criteria
✅ **Result tracking** - Full optimization history and statistics
✅ **Zero dependencies** - Lightweight, no heavy ML libraries
✅ **Async/await** - Modern Python async support

---

## 📚 Resources

### Complete Working Example

```bash
python examples/prompt_optimization_example.py
```

### Documentation

1. **`docs/AUTOMATIC_OPTIMIZATION_GUIDE.md`** - Complete usage guide
   - 4 methods of using optimization
   - Strategy deep-dives
   - Custom metrics and strategies
   - Best practices
   - Troubleshooting

2. **`docs/PROMPT_OPTIMIZATION_PROPOSAL.md`** - Enhancement roadmap
   - Gap analysis vs DSPy 2025
   - Proposed improvements
   - Implementation plan

3. **`examples/prompt_optimization_example.py`** - Working code
   - Basic usage
   - Advanced usage
   - Strategy comparison

---

## 📊 Comparison with DSPy

| Feature | mini_agent | DSPy |
|---------|------------|------|
| Bootstrap Few-Shot | ✅ | ✅ |
| COPRO (Coordinate Ascent) | ✅ | ✅ |
| Bayesian Optimization | ⚠️ Simplified | ✅ |
| MIPROv2 | ❌ Planned | ✅ |
| Signature System | ❌ Planned | ✅ |
| Error Analysis (SIMBA) | ❌ Planned | ✅ |
| Zero Dependencies | ✅ | ❌ |

**You have the core DSPy optimization features!** 🎉
See the proposal doc for planned enhancements to reach full parity.

---

## 💡 Quick Examples

### Try Different Strategies

```python
# Bootstrap (few-shot examples)
await agent.optimize_prompt(examples, strategy="bootstrap")

# Coordinate Ascent (instruction refinement)
await agent.optimize_prompt(examples, strategy="coordinate_ascent")

# Bayesian (smart exploration)
await agent.optimize_prompt(examples, strategy="bayesian")
```

### Check Results

```python
if agent.optimization_history:
    result = agent.optimization_history[-1]
    print(f"Improvement: {result['improvement']:.2%}")
    print(f"Final Score: {result['final_score']:.2%}")
```

### Advanced Usage

```python
from optimization import CoreOptimizer, TrainingExample

optimizer = CoreOptimizer(
    strategy="bootstrap",
    max_iterations=10,
    convergence_threshold=0.95
)

result = await optimizer.optimize(
    initial_prompt="Your prompt",
    training_examples=examples,
    agent_evaluator=your_evaluator
)
```

---

## 🎓 Next Steps

1. ✅ **Run the example**: `python examples/prompt_optimization_example.py`
2. 📖 **Read the guide**: `docs/AUTOMATIC_OPTIMIZATION_GUIDE.md`
3. 🔬 **Try with your agent**: Enable `enable_optimization=True`
4. 📊 **Compare strategies**: See which works best for your task
5. 🚀 **Customize**: Create custom metrics and strategies

---

## ❓ Common Questions

### Q: How many training examples do I need?
**A:** Minimum 5-10 diverse examples. More is better (20-50 ideal).

### Q: Which strategy should I use?
**A:** Start with **bootstrap** - it usually gives best initial results.

### Q: How long does optimization take?
**A:** Depends on:
- Number of examples (5-50)
- Number of iterations (3-20)
- LLM speed
- Strategy used

Typical: 1-5 minutes with 10 examples and 10 iterations.

### Q: Can I use custom evaluation metrics?
**A:** Yes! Create a custom `OptimizationMetric` class. See guide for details.

### Q: Does it work with any LLM?
**A:** Yes! Works with OpenAI, Anthropic, local models, or any LLM function.

---

## 🔥 Pro Tips

1. **Start simple**: Use agent.optimize_prompt() before diving into CoreOptimizer
2. **Diverse examples**: Include easy, medium, and hard examples
3. **Monitor progress**: Check optimization_history for insights
4. **Compare strategies**: Try all three to see which works best
5. **Save results**: Store optimized prompts for reuse

---

## 📦 Files Created

All documentation has been committed to your repo:

```
mini_agent/
├── docs/
│   ├── AUTOMATIC_OPTIMIZATION_GUIDE.md    # Complete usage guide
│   └── PROMPT_OPTIMIZATION_PROPOSAL.md    # Enhancement roadmap
├── examples/
│   └── prompt_optimization_example.py     # Working example
├── optimization/                           # Core implementation
│   ├── core_optimizer.py
│   ├── optimization_strategies.py
│   ├── metrics.py
│   └── ...
└── QUICK_START_OPTIMIZATION.md            # This file
```

---

**Ready to optimize? Run the example!**

```bash
python examples/prompt_optimization_example.py
```

🎉 **You have automatic optimization - start using it today!**
