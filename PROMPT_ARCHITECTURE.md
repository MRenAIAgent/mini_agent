# Comprehensive Prompt Architecture Analysis

## Executive Summary

The mini_agent codebase implements a sophisticated DSPy-inspired prompt optimization framework integrated with a ReAct-based agent system. The architecture supports multiple prompt types, execution patterns, optimization strategies, and memory-enriched context injection.

---

## 1. Current Prompt Structure and Usage

### 1.1 Base System Prompts

**Location**: `/home/user/mini_agent/agent.py` and `/home/user/mini_agent/execution/react_executor.py`

#### System Prompt Components:

1. **Initial System Prompt** (User-provided)
   - Set during CoreAgent initialization
   - Default: Empty string (can be customized)
   - Example: `"You are a helpful AI assistant."`

2. **ReAct Standard Prompt** (Generated)
   - Location: `ReactExecutor.get_react_system_prompt()` (lines 214-238)
   - Contains structured format instructions:
     ```
     Thought: Your reasoning about what to do next
     Action: The action you want to take
     Action Input: The input for the action
     
     Observation: The result of the action
     Final Answer: Your complete answer to the user's question
     ```

3. **Enhanced System Prompt** (Runtime Generated)
   - Method: `CoreAgent._build_enhanced_prompt()` (lines 728-805)
   - Dynamically composed from multiple sources:
     - Base system prompt
     - Tool descriptions
     - Memory context (conversation history + memories)
     - Examples from memory
     - Custom context parameters
     - ReAct execution instructions

### 1.2 Prompt Building Flow

```
User Input
    ↓
_build_enhanced_prompt()
    ├─ Base system prompt
    ├─ Tool descriptions (if available)
    ├─ Memory context retrieval
    │   ├─ Conversation history summary
    │   ├─ Relevant memories (top 3)
    │   └─ Example memories (filtered by type="example")
    ├─ Custom context
    └─ ReAct system prompt
    ↓
Full enhanced prompt → LLM
```

### 1.3 Prompt Structure Example

```python
# Current structure from _build_enhanced_prompt():
[
    system_prompt,                          # Base prompt
    "You have access to these tools:",      # Tool info
    "- tool_name: description",
    "Conversation context:",                # Memory context
    "conversation_summary",
    "Relevant memories:",
    "- memory_1\n- memory_2",
    "Examples:",
    "Example: ...",
    "Additional context:",
    "key: value pairs",
    "ReAct instructions"                    # Pattern-specific
]
```

---

## 2. Prompt Template Definition Locations

### 2.1 Hard-coded Templates

| Location | Purpose | Status |
|----------|---------|--------|
| `execution/react_executor.py:214-238` | ReAct format instructions | Defined |
| `execution/thought_formatter.py:22-34` | Basic ReAct template | Defined |
| `execution/thought_formatter.py:26-34` | Structured thought template | Defined |
| `execution/thought_formatter.py:193-212` | Thought formatting guidelines | Defined |

### 2.2 Specification Templates (for Framework Development)

Location: `/home/user/mini_agent/.specify/templates/`
- `plan-template.md` - Architecture planning template
- `spec-template.md` - Feature specification template
- `tasks-template.md` - Task breakdown template
- `agent-file-template.md` - Agent file structure template

### 2.3 Dynamically Generated Templates

| Component | Generation Method | Parameters |
|-----------|------------------|-----------|
| Few-shot examples | `BootstrapStrategy._create_few_shot_prompt()` | Base prompt + examples list |
| Prompt candidates | `CoordinateAscentStrategy._generate_prompt_candidates()` | Base prompt + variations |
| Bayesian candidates | `BayesianStrategy._select_next_candidate()` | Template + base prompt |

---

## 3. Agent System Prompt Handling

### 3.1 Architecture Overview

```
CoreAgent (agent.py)
├── system_prompt: str          # User-provided base prompt
├── memory_manager              # Retrieves context
├── tool_manager                # Lists available tools
├── optimizer                   # Optimizes system prompt
├── executor (ReactExecutor)    # Provides ReAct instructions
└── pattern_executor            # Supports multiple patterns
```

### 3.2 Key Methods for Prompt Handling

| Method | Location | Purpose |
|--------|----------|---------|
| `_build_enhanced_prompt()` | agent.py:728-805 | Creates full runtime prompt |
| `_enhanced_llm_call()` | agent.py:808-822 | Executes LLM with prompt |
| `_build_prompt()` | react_executor.py:174-192 | ReAct-specific prompt building |
| `optimize_prompt()` | agent.py:582-634 | Triggers prompt optimization |

### 3.3 System Prompt Flow

```
initialization: system_prompt = user_input
    ↓
per_request:
    enhanced_prompt = await _build_enhanced_prompt(message, context)
    ↓
    if optimization_enabled:
        candidate_prompt = strategy.generate_candidate()
        score = await evaluate(candidate_prompt)
    ↓
    response = await _enhanced_llm_call(enhanced_prompt)
    ↓
    if optimization_improved:
        system_prompt = optimized_prompt
```

---

## 4. Prompt Optimization and Refinement Mechanisms

### 4.1 Optimization Framework

Location: `/home/user/mini_agent/optimization/`

#### Core Classes:

1. **CoreOptimizer** (core_optimizer.py)
   - Orchestrates prompt optimization
   - Pluggable strategies
   - Metrics-based evaluation
   - Tracks convergence

2. **OptimizationContext** (optimization_context.py)
   - Manages optimization state
   - Tracks training/validation split
   - Records optimization history
   - Calculates efficiency metrics

3. **OptimizationResult** (optimization_result.py)
   - Contains optimized prompt
   - Reports improvement metrics
   - Exports few-shot examples
   - Generates optimization reports

### 4.2 DSPy-Inspired Optimization Strategies

#### 1. Bootstrap Strategy
- **File**: `optimization_strategies.py:41-195`
- **Approach**: Few-shot example generation and inclusion
- **Algorithm**:
  1. Sample training examples
  2. Evaluate each example with current best prompt
  3. Keep examples scoring above threshold (default: 0.7)
  4. Create new prompt with examples included
  5. Validate on test set
  6. Update best prompt if improved

#### 2. Coordinate Ascent Strategy (COPRO-inspired)
- **File**: `optimization_strategies.py:197-301`
- **Approach**: Iterative prompt refinement with variations
- **Algorithm**:
  1. Generate prompt candidates with variations:
     - "Be more specific and detailed in your response."
     - "Think step by step before answering."
     - "Provide clear reasoning for your answer."
     - "Focus on accuracy and precision."
     - "Consider multiple perspectives before responding."
  2. Evaluate each candidate
  3. Select best performer
  4. Iterate

#### 3. Bayesian Strategy
- **File**: `optimization_strategies.py:303-430`
- **Approach**: Exploration/exploitation with acquisition function
- **Algorithm**:
  1. Maintain performance history
  2. Use acquisition function for candidate selection:
     - Exploration: Random template selection
     - Exploitation: Refine best-known prompt
  3. Update history with new evaluation
  4. Continue until convergence

### 4.3 Optimization Metrics

Location: `optimization/metrics.py`

| Metric | Calculation | Use Case |
|--------|-------------|----------|
| AccuracyMetric | Jaccard similarity on words | Exact/fuzzy matching |
| EfficiencyMetric | accuracy_weight * accuracy + efficiency_weight * efficiency | Balanced scoring |
| Custom metrics | User-defined evaluation | Task-specific evaluation |

### 4.4 Optimization Loop

```
optimize_prompt() call
    ↓
CoreOptimizer.optimize()
    ├─ Create OptimizationContext
    ├─ Evaluate initial prompt
    ├─ Loop (until convergence or max iterations):
    │   ├─ strategy.optimize_step()
    │   │   ├─ Generate candidate prompt
    │   │   ├─ Evaluate on validation set
    │   │   ├─ Score = metric.evaluate(response, expected)
    │   │   └─ Update best if improved
    │   └─ Check convergence
    ├─ Create OptimizationResult
    └─ Return result with improvement metrics
    ↓
if improvement > 0:
    agent.system_prompt = result.optimized_prompt
```

---

## 5. Message Construction and Context Injection

### 5.1 Context Retrieval

**Memory System** (memory/memory_manager.py:245-298)

```python
async def get_relevant_context(session_id, query) -> Dict:
    {
        "conversation": {
            "summary": "...",  # Summarized conversation history
            "turns": [...],     # Recent turns
        },
        "memories": [
            {"content": "...", "importance": 0.9, "metadata": {...}},
            ...
        ]
    }
```

### 5.2 Prompt Assembly Order

From `_build_enhanced_prompt()` (agent.py:728-805):

1. **Base System Prompt** - User-provided foundation
2. **Tool Descriptions** - List of available tools with descriptions
3. **Conversation Context** - Recent conversation summary
4. **Relevant Memories** - Top-3 semantically similar memories
5. **Examples** - Training examples from memory (type="example")
6. **Custom Context** - Additional context parameters
7. **ReAct Instructions** - Execution pattern format rules

### 5.3 Thought Formatting

Location: `execution/thought_formatter.py`

**Structured Thought Format**:
```
Thought: Let me analyze this step by step.

Observation: {observation}
Analysis: {analysis}
Reasoning: {reasoning}
Conclusion: {conclusion}

Action: {action}
Action Input: {action_input}
```

**Methods**:
- `format_react_step()` - Basic format
- `format_structured_thought()` - Detailed format
- `format_final_answer()` - Answer format
- `format_error_recovery()` - Error handling
- `format_context_summary()` - Task summary

---

## 6. Configuration and Customization

### 6.1 Agent Configuration

**CoreAgent Initialization** (agent.py:95-216):

```python
agent = CoreAgent(
    llm_config=LLMConfig(...),           # LLM provider config
    system_prompt="Custom prompt",        # Base system prompt
    max_iterations=5,                     # ReAct max iterations
    enable_memory=True,                   # Memory system
    enable_optimization=False,            # Prompt optimization
    execution_pattern=ExecutionPatternType.REACT,  # Pattern type
    enable_pattern_selection=True,        # Auto pattern selection
    enable_tracing=True,                  # Tracing & observability
    enable_sidecars=True                  # Background tasks
)
```

### 6.2 Execution Patterns

Location: `execution/execution_patterns.py`

**Supported Patterns**:
- SIMPLE - Direct LLM call
- REACT - Reasoning + Acting cycle
- PLANNING - Plan then execute
- AUTO - Automatic pattern selection
- CHAIN_OF_THOUGHT - Step-by-step reasoning
- PLAN_AND_EXECUTE - Plan then execute
- REFLECTION - Self-reflection
- TREE_OF_THOUGHTS - Multiple reasoning paths
- ANALYTICAL - Analytical approach
- CREATIVE - Creative problem solving
- CRITICAL - Critical analysis
- SOCRATIC - Socratic questioning

### 6.3 Optimization Configuration

**CoreOptimizer Initialization** (optimization/core_optimizer.py:26-48):

```python
optimizer = CoreOptimizer(
    strategy="bootstrap",              # "bootstrap", "coordinate_ascent", "bayesian"
    metric=AccuracyMetric(),           # Evaluation metric
    max_iterations=10,                 # Max optimization rounds
    convergence_threshold=0.95,        # Convergence target (0-1)
    timeout_seconds=300                # Timeout
)
```

---

## 7. Existing Optimization Mechanisms

### 7.1 In-Context Learning

**Few-Shot Injection** (optimization_strategies.py:147-165):

```python
def _create_few_shot_prompt(base_prompt, examples):
    return base_prompt + "\n\nHere are some examples:\n" + \
           examples_text + "\n\nNow solve the following:"
```

### 7.2 Prompt Variation

**Variation Templates** (optimization_strategies.py:206-212):

```python
self.prompt_variations = [
    "Be more specific and detailed in your response.",
    "Think step by step before answering.",
    "Provide clear reasoning for your answer.",
    "Focus on accuracy and precision.",
    "Consider multiple perspectives before responding."
]
```

### 7.3 Memory-Based Context

**Semantic Retrieval** (agent.py:758-795):

- Retrieves conversation context
- Fetches relevant memories
- Filters example-type memories
- Includes top-3 matches by relevance

### 7.4 Execution Pattern Selection

**Pattern Executor** (execution/pattern_executor.py:30-145):

- Multiple execution patterns available
- Pattern selection rules (extensible)
- Pattern usage statistics
- Success rate tracking

---

## 8. Architectural Insights and Opportunities

### 8.1 Current Strengths

1. **Modular Design** - Clear separation of concerns
2. **Extensibility** - Pluggable strategies and metrics
3. **Memory-Aware** - Context injection from memory systems
4. **DSPy-Inspired** - Bootstrap, coordinate ascent, and Bayesian strategies
5. **Comprehensive Tracking** - Optimization history and metrics
6. **Multiple Patterns** - Support for different execution approaches

### 8.2 Key Integration Points for DSPy Optimization

1. **Prompt Candidates Generation**
   - `CoordinateAscentStrategy._generate_prompt_candidates()`
   - `BayesianStrategy._select_next_candidate()`

2. **Evaluation Pipeline**
   - `agent_evaluator()` callback in `optimize_prompt()`
   - Metrics in `optimization/metrics.py`

3. **Few-Shot Learning**
   - `BootstrapStrategy._generate_few_shot_examples()`
   - `_create_few_shot_prompt()` method

4. **Memory Context**
   - `_build_enhanced_prompt()` retrieves and injects context
   - Multiple memory types supported

### 8.3 Current Limitations

1. **Static Prompt Template** - ReAct format is hardcoded
2. **Limited Prompt Refinement** - Variations are pre-defined
3. **No Dynamic Few-Shot Selection** - Uses simple random sampling
4. **No Prompt Compression** - Full context always included
5. **No Gradient-Based Optimization** - Only discrete strategy-based
6. **Limited Error Feedback** - No structured error analysis for prompt refinement

---

## 9. File Structure Summary

```
mini_agent/
├── agent.py                          # Core agent with prompt building
├── agent_simple.py                   # Simplified agent
├── execution/
│   ├── react_executor.py             # ReAct implementation
│   ├── pattern_executor.py           # Multi-pattern executor
│   ├── execution_context.py          # Execution state management
│   ├── execution_patterns.py         # Pattern definitions
│   ├── action_parser.py              # Action parsing
│   └── thought_formatter.py          # Thought formatting templates
├── optimization/
│   ├── core_optimizer.py             # Optimizer orchestration
│   ├── optimization_context.py       # Optimization state
│   ├── optimization_result.py        # Results container
│   ├── optimization_strategies.py    # Bootstrap, COPRO, Bayesian
│   └── metrics.py                    # Evaluation metrics
├── memory/
│   ├── memory_manager.py             # Core memory system
│   ├── core/
│   │   └── memory_context.py         # Context management
│   └── [other memory types]
└── tools/
    └── [tool integration]
```

---

## 10. Key Metrics and Tracking

### 10.1 Optimization Metrics

From `optimization_result.py`:

```python
{
    "success": bool,
    "final_score": float,
    "improvement": float,
    "improvement_percentage": float,
    "iterations": int,
    "execution_time": float,
    "convergence_achieved": bool,
    "efficiency": {
        "score_per_second": float,
        "score_per_api_call": float,
        "iterations_per_minute": float
    }
}
```

### 10.2 Execution Metrics

- Total API calls
- Total tokens used
- Execution time
- Convergence rate
- Strategy effectiveness

---

## Conclusion

The mini_agent codebase provides a comprehensive, DSPy-inspired prompt optimization framework with:

1. **Flexible prompt building** from multiple context sources
2. **Multiple optimization strategies** (Bootstrap, COPRO-style, Bayesian)
3. **Memory-aware context injection** for richer prompts
4. **Pluggable metrics** for custom evaluation
5. **Comprehensive tracking** of optimization progress
6. **Support for multiple execution patterns** beyond basic ReAct

The architecture is well-designed for prompt optimization experiments and provides clear extension points for implementing advanced DSPy-style techniques like:
- Signature-based prompt engineering
- Metric-guided optimization
- Dynamic few-shot selection
- Constraint-based prompt refinement

