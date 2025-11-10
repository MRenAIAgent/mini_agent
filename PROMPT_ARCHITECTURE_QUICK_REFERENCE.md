# Prompt Architecture - Quick Reference Guide

## Key Files At A Glance

### Prompt Definition & Building
- **`agent.py` (lines 728-805)** - `_build_enhanced_prompt()` - Runtime prompt assembly
- **`react_executor.py` (lines 214-238)** - ReAct format instructions
- **`thought_formatter.py`** - Thought and response formatting templates

### Optimization System
- **`optimization/core_optimizer.py`** - Main optimizer orchestration
- **`optimization/optimization_strategies.py`** - Three strategies: Bootstrap, CoordinateAscent, Bayesian
- **`optimization/metrics.py`** - Evaluation metrics (Accuracy, Efficiency, custom)
- **`optimization/optimization_context.py`** - State tracking for optimization
- **`optimization/optimization_result.py`** - Results and reporting

### Memory & Context
- **`memory/memory_manager.py` (lines 245-298)** - `get_relevant_context()` - Context retrieval
- **`memory/core/memory_context.py`** - Conversation and memory context structures

### Execution
- **`execution/execution_context.py`** - ReAct execution state
- **`execution/pattern_executor.py`** - Multi-pattern executor
- **`execution/execution_patterns.py`** - Pattern type definitions

---

## Prompt Building Flow (One-Pager)

```
User Input → _build_enhanced_prompt()
    ↓
1. Start with user's system_prompt
2. Add tool descriptions from tool_manager
3. Retrieve and add conversation context from memory
4. Retrieve and add relevant memories (top 3 semantic matches)
5. Add example-type memories from memory store
6. Add custom context parameters
7. Append ReAct format instructions
    ↓
Complete prompt → LLM Call
    ↓
Response → Agent processes & returns
```

---

## Optimization Strategies Comparison

| Strategy | Best For | Key Features | Location |
|----------|----------|--------------|----------|
| **Bootstrap** | Improving with examples | Few-shot generation, threshold-based filtering | `optimization_strategies.py:41-195` |
| **CoordinateAscent** | Iterative refinement | Pre-defined variations, greedy selection | `optimization_strategies.py:197-301` |
| **Bayesian** | Balancing exploration/exploitation | Performance history, acquisition function | `optimization_strategies.py:303-430` |

---

## How to Use Prompt Optimization

### Basic Usage
```python
agent = CoreAgent(
    llm_config=...,
    system_prompt="Initial prompt",
    enable_optimization=True
)

# Create training data
training_examples = [
    {"input": "What is 2+2?", "output": "4"},
    {"input": "What is 5*3?", "output": "15"},
]

# Run optimization
success = await agent.optimize_prompt(training_examples, strategy="bootstrap")

# Updated system_prompt is now in agent.system_prompt
```

### Optimization Result Contents
```python
result = OptimizationResult(
    optimized_prompt=str,          # Improved prompt
    best_score=float,              # Final score (0-1)
    improvement=float,             # Score improvement
    iterations_completed=int,      # Iterations run
    total_execution_time=float,    # Time in seconds
    convergence_achieved=bool,     # Met threshold?
    api_calls=int,                 # LLM API calls used
    total_tokens=int,              # Tokens consumed
    optimization_history=[...],    # Detailed steps
    few_shot_examples=[...]        # Generated examples
)
```

---

## Metrics & Evaluation

### Available Metrics

1. **AccuracyMetric** (default)
   - Jaccard similarity on words
   - Case-sensitive option
   - Fuzzy threshold: 0.8
   - Use: General purpose

2. **EfficiencyMetric**
   - Combines accuracy + efficiency
   - Configurable weights
   - Default: 70% accuracy, 30% efficiency
   - Use: Balanced optimization

3. **Custom Metrics**
   - Extend `OptimizationMetric`
   - Implement `evaluate(predicted, expected, context)`
   - Use: Task-specific scoring

---

## Configuration Examples

### Agent Configuration
```python
agent = CoreAgent(
    llm_config=LLMConfig(provider="openai", model="gpt-4"),
    system_prompt="You are a helpful assistant.",
    max_iterations=5,
    enable_memory=True,
    enable_optimization=True,
    execution_pattern=ExecutionPatternType.REACT,
    enable_tracing=True
)
```

### Optimizer Configuration
```python
optimizer = CoreOptimizer(
    strategy="bootstrap",          # or "coordinate_ascent", "bayesian"
    metric=AccuracyMetric(fuzzy_threshold=0.8),
    max_iterations=10,
    convergence_threshold=0.95,
    timeout_seconds=300
)
```

---

## Execution Patterns Available

- **SIMPLE** - Direct LLM call, no reasoning
- **REACT** - Thought/Action/Observation cycles
- **PLANNING** - Plan first, then execute
- **CHAIN_OF_THOUGHT** - Step-by-step reasoning
- **TREE_OF_THOUGHTS** - Multiple reasoning paths
- **REFLECTION** - Self-reflection and refinement
- **ANALYTICAL** - Analytical problem solving
- **CREATIVE** - Creative approach
- **CRITICAL** - Critical analysis
- **SOCRATIC** - Socratic questioning method

---

## Memory Context Injection

### What Gets Injected Into Prompts

1. **Conversation Context**
   - Recent conversation summary
   - Last N turns (configurable)
   - Context size limit: 4000 chars default

2. **Relevant Memories**
   - Top 3 semantic matches
   - Sorted by: importance + recency + similarity
   - Types: episodic, semantic, user profile, interaction

3. **Example Memories**
   - Filtered by metadata type="example"
   - Used for in-context learning
   - Injected before task

4. **Tool Information**
   - Tool names and descriptions
   - Parameters and expected inputs
   - Category organization

---

## Key Classes & Methods

### CoreAgent
- `__init__(llm_config, system_prompt, ...)` - Initialize agent
- `run(message, context)` - Execute agent
- `optimize_prompt(training_examples, strategy)` - Run optimization
- `_build_enhanced_prompt(user_input, context)` - Assemble prompt
- `remember(content, importance)` - Store memory
- `recall(query, limit)` - Retrieve memories

### CoreOptimizer
- `optimize(initial_prompt, training_examples, agent_evaluator)` - Run optimization
- `set_strategy(strategy)` - Change strategy
- `set_metric(metric)` - Change evaluation metric
- `quick_optimize(...)` - Fast optimization mode

### ReactExecutor
- `execute(user_input, system_prompt, context)` - ReAct loop
- `get_react_system_prompt()` - Get format instructions
- `_build_prompt(context)` - Assemble ReAct prompt
- `_generate_response(context)` - Call LLM

### ThoughtFormatter
- `format_react_step(thought, action, input)` - Format step
- `format_structured_thought(...)` - Detailed format
- `format_final_answer(answer, reasoning)` - Final format
- `create_system_prompt_addition()` - Get formatting instructions

---

## Common Patterns

### Optimize System Prompt
```python
training_data = [
    {"input": "...", "output": "..."},
]
success = await agent.optimize_prompt(training_data)
if success:
    print(f"Prompt improved to: {agent.system_prompt}")
```

### Use Memory Context
```python
await agent.remember("Important fact", importance=0.9)
context = await agent.get_context_summary()
response = await agent.run("Question based on memory")
```

### Change Execution Pattern
```python
result = await agent.pattern_executor.execute(
    user_input="Complex question",
    system_prompt=agent.system_prompt,
    pattern=ExecutionPatternType.TREE_OF_THOUGHTS
)
```

### Custom Metric
```python
class MyMetric(OptimizationMetric):
    def evaluate(self, predicted, expected, context=None):
        # Custom scoring logic
        return score_between_0_and_1
    
    def get_name(self):
        return "my_metric"

optimizer.set_metric(MyMetric())
```

---

## Troubleshooting

### Optimization Not Improving
- Check if convergence_threshold is too high (default 0.95)
- Verify training examples are high quality
- Try different strategy ("bootstrap" works best for few-shot)
- Increase max_iterations

### Low Prompt Quality
- Enable memory and add relevant context
- Ensure tool descriptions are clear
- Check ReAct format instructions are included
- Verify agent_evaluator is working correctly

### Memory Context Not Being Used
- Ensure memory is enabled: `enable_memory=True`
- Verify memories are stored: `await agent.remember(...)`
- Check context_size limit not exceeded
- Memory should be retrieved automatically in `_build_enhanced_prompt()`

---

## Extension Points

### Add Custom Optimization Strategy
1. Extend `OptimizationStrategy`
2. Implement `optimize_step()` and `get_name()`
3. Use in: `CoreOptimizer(strategy=MyStrategy())`

### Add Custom Metric
1. Extend `OptimizationMetric`
2. Implement `evaluate()` and `get_name()`
3. Use in: `CoreOptimizer(metric=MyMetric())`

### Add Custom Execution Pattern
1. Extend `ExecutionPattern`
2. Implement `execute()` and `parse_llm_response()`
3. Register in `ExecutionPatternFactory`

### Add Custom Thought Formatter
1. Extend `ThoughtFormatter`
2. Override template strings
3. Use in: Custom execution pattern

---

## Performance Benchmarks

Typical optimization session:
- **Bootstrap**: 3-5 iterations, ~5-15 API calls, 30-60 seconds
- **CoordinateAscent**: 5-10 iterations, ~15-30 API calls, 60-120 seconds
- **Bayesian**: 5-10 iterations, ~15-30 API calls, 60-120 seconds

Token usage:
- Typical prompt: 500-1000 tokens (varies with context)
- Optimization evaluation: 5000-15000 tokens per optimization
- Memory retrieval: 50-200 tokens overhead

Response time:
- Simple query: 100-500ms
- With memory: 150-600ms
- With optimization: 30-120 seconds (one-time)
- ReAct loop (5 iterations): 500ms-2s per iteration

