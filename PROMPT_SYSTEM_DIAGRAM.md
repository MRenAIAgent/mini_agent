# Prompt Architecture Diagram

## Overall System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CoreAgent                                   │
│  (agent.py: Lines 87-900)                                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────────┐   │
│  │ system_prompt    │  │ enable_memory    │  │ enable_optimization │   │
│  │ (base prompt)    │  │ (context source) │  │ (prompt refinement) │   │
│  └──────────────────┘  └──────────────────┘  └─────────────────────┘   │
│           │                     │                      │                 │
│           ↓                     ↓                      ↓                 │
│  ┌────────────────────────────────────────────────────────────┐         │
│  │         _build_enhanced_prompt(user_input, context)        │         │
│  │         (Lines 728-805)                                    │         │
│  └────────────────────────────────────────────────────────────┘         │
│           ↓                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    PROMPT ASSEMBLY PIPELINE                     │    │
│  ├─────────────────────────────────────────────────────────────────┤    │
│  │ 1. Base System Prompt (user-provided)                           │    │
│  │    └─ "You are a helpful AI assistant."                         │    │
│  │                                                                  │    │
│  │ 2. Tool Descriptions (from tool_manager)                        │    │
│  │    └─ "You have access to these tools:"                        │    │
│  │       - tool_name: description                                 │    │
│  │                                                                  │    │
│  │ 3. Conversation Context (from memory_manager)                   │    │
│  │    └─ get_relevant_context(session_id, user_input)             │    │
│  │       ├─ conversation_summary                                   │    │
│  │       └─ recent_turns                                           │    │
│  │                                                                  │    │
│  │ 4. Relevant Memories (from memory store)                        │    │
│  │    └─ Top 3 semantic matches                                   │    │
│  │       ├─ episodic_memory                                        │    │
│  │       ├─ semantic_memory                                        │    │
│  │       └─ user_profile_memory                                    │    │
│  │                                                                  │    │
│  │ 5. Example Memories (filtered type="example")                   │    │
│  │    └─ In-context learning examples                             │    │
│  │                                                                  │    │
│  │ 6. Custom Context (from parameters)                             │    │
│  │    └─ key: value pairs                                         │    │
│  │                                                                  │    │
│  │ 7. ReAct Instructions (from executor)                           │    │
│  │    └─ executor.get_react_system_prompt()                       │    │
│  │       "Thought: ... Action: ... Observation: ..."              │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│           ↓                                                               │
│  ┌────────────────────────────────────────────────────────────┐         │
│  │  COMPLETE ENHANCED PROMPT (4000-8000 tokens)               │         │
│  └────────────────────────────────────────────────────────────┘         │
│           ↓                                                               │
│  ┌────────────────────────────────────────────────────────────┐         │
│  │  _enhanced_llm_call(prompt)  (Lines 808-822)               │         │
│  │  (Executes with LiteLLM or custom function)                │         │
│  └────────────────────────────────────────────────────────────┘         │
│           ↓                                                               │
│        Response                                                           │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Prompt Optimization Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      optimize_prompt() Call                              │
│                      (agent.py: Lines 582-634)                           │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│                        CoreOptimizer.optimize()                          │
│              (optimization/core_optimizer.py: Lines 54-110)              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─ Strategy Selection                                                    │
│  │   ├─ Bootstrap (Few-shot generation) [41-195]                         │
│  │   ├─ CoordinateAscent (Prompt variations) [197-301]                   │
│  │   └─ Bayesian (Exploration/Exploitation) [303-430]                    │
│  │                                                                         │
│  ├─ Create OptimizationContext                                            │
│  │   ├─ training_examples                                                 │
│  │   ├─ validation_examples (20% split)                                   │
│  │   └─ best_prompt = initial_prompt                                      │
│  │                                                                         │
│  └─ Optimization Loop (until convergence or max_iterations):              │
│                                                                            │
│     Iteration 1:                                                          │
│     ─────────────                                                         │
│     ├─ strategy.optimize_step()                                           │
│     │  ├─ Generate prompt candidate                                       │
│     │  ├─ Evaluate on validation examples:                                │
│     │  │  └─ For each example:                                            │
│     │  │     ├─ response = agent_evaluator(candidate_prompt, example)    │
│     │  │     └─ score = metric.evaluate(response, expected_output)       │
│     │  ├─ Average validation score                                        │
│     │  └─ Update best_prompt if score > best_score                       │
│     │                                                                      │
│     │  context.add_step(                                                  │
│     │      strategy="bootstrap",                                          │
│     │      prompt_candidate=candidate,                                    │
│     │      evaluation_score=score                                         │
│     │  )                                                                   │
│     │                                                                      │
│     ├─ Check convergence:                                                 │
│     │  └─ best_score >= convergence_threshold?                            │
│     │                                                                      │
│     [Iteration 2, 3, ... if not converged]                               │
│                                                                            │
│  Create OptimizationResult:                                              │
│  ├─ optimized_prompt (best_prompt found)                                  │
│  ├─ best_score (final evaluation score)                                   │
│  ├─ improvement (best_score - initial_score)                              │
│  ├─ optimization_history (all steps)                                      │
│  ├─ efficiency metrics                                                    │
│  └─ few_shot_examples (generated examples)                               │
│                                                                            │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
                    ┌───────────────────────────────┐
                    │  if improvement > 0:          │
                    │    agent.system_prompt =      │
                    │      result.optimized_prompt  │
                    └───────────────────────────────┘
```

---

## Optimization Strategy Details

### 1. Bootstrap Few-Shot Strategy

```
bootstrap_strategy.optimize_step()
    ├─ Sample training examples (e.g., 5-10 examples)
    │
    ├─ For each sampled example:
    │  ├─ response = agent_evaluator(current_best_prompt, example)
    │  ├─ score = metric.evaluate(response, expected_output)
    │  └─ if score >= min_score_threshold (0.7):
    │     └─ keep as few_shot_example
    │
    ├─ Generate few-shot prompt:
    │  └─ new_prompt = base_prompt + 
    │                  "Here are some examples:\n" +
    │                  examples_text +
    │                  "\nNow solve the following:"
    │
    ├─ Evaluate new prompt on validation set
    │  └─ avg_score = mean([metric.evaluate(...) for ex in validation])
    │
    └─ Update best_prompt if avg_score > current_best_score
```

### 2. Coordinate Ascent Strategy (COPRO-style)

```
coordinate_ascent_strategy.optimize_step()
    ├─ Generate prompt candidates:
    │  ├─ Candidate 1: base_prompt (unchanged)
    │  ├─ Candidate 2: base_prompt + "Be more specific and detailed..."
    │  ├─ Candidate 3: base_prompt + "Think step by step..."
    │  ├─ Candidate 4: base_prompt + "Provide clear reasoning..."
    │  └─ Candidate 5: base_prompt + "Focus on accuracy..."
    │
    ├─ For each candidate:
    │  ├─ score = evaluate_prompt(candidate, validation_examples)
    │  └─ track best_score and best_candidate
    │
    └─ Update best_prompt to best_candidate if score > current_best
```

### 3. Bayesian Strategy

```
bayesian_strategy.optimize_step()
    ├─ Maintain performance_history: [(prompt, score), ...]
    │
    ├─ Select next candidate using acquisition function:
    │  ├─ if random() < exploration_factor (0.1):
    │  │  └─ EXPLORATION: Select random template
    │  │     └─ template.format(base_prompt=current_best)
    │  │
    │  └─ else:
    │     └─ EXPLOITATION: Refine best_known
    │        └─ best_prompt + random(refinement_phrase)
    │
    ├─ Evaluate candidate
    │  └─ score = metric.evaluate(...)
    │
    ├─ Add to performance_history
    │
    └─ Update best_prompt if score > current_best
```

---

## Memory Context Injection Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│  get_relevant_context(session_id, query)                            │
│  (memory_manager.py: Lines 245-298)                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │ 1. CONVERSATION CONTEXT RETRIEVAL                       │        │
│  ├─────────────────────────────────────────────────────────┤        │
│  │ get_context_memory(session_id, query)                   │        │
│  │  └─ Fetch recent conversation turns                     │        │
│  │     └─ Summarize into conversation_summary              │        │
│  │        └─ "User: X, Assistant: Y; User: Z, ..."        │        │
│  └─────────────────────────────────────────────────────────┘        │
│                      ↓                                                │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │ 2. SEMANTIC MEMORY RETRIEVAL                            │        │
│  ├─────────────────────────────────────────────────────────┤        │
│  │ search_memory(query, limit=10)                          │        │
│  │  └─ Semantic search on memory store                     │        │
│  │     └─ Score: similarity(query, memory) * importance    │        │
│  │     └─ Rank by: similarity + importance + recency       │        │
│  │     └─ Return top 3                                     │        │
│  └─────────────────────────────────────────────────────────┘        │
│                      ↓                                                │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │ 3. EXAMPLE MEMORY FILTERING                             │        │
│  ├─────────────────────────────────────────────────────────┤        │
│  │ Filter memories where metadata["type"] == "example"     │        │
│  │  └─ These are used for in-context learning              │        │
│  │     └─ "Example 1: Input: X, Output: Y"                │        │
│  └─────────────────────────────────────────────────────────┘        │
│                      ↓                                                │
│  Return {                                                            │
│      "conversation": {                                               │
│          "summary": "...",                                           │
│          "turns": [...]                                              │
│      },                                                               │
│      "memories": [                                                    │
│          {                                                            │
│              "content": "...",                                       │
│              "importance": 0.9,                                      │
│              "metadata": {...}                                       │
│          },                                                           │
│          ...                                                          │
│      ]                                                                │
│  }                                                                    │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Execution Pattern Architecture

```
┌────────────────────────────────────────────────────────────────┐
│              PatternExecutor (pattern_executor.py)             │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  execute(user_input, system_prompt, pattern=None)              │
│                                                                  │
│  ├─ Select pattern (if not specified):                         │
│  │  └─ _select_pattern(user_input, pattern_params)             │
│  │                                                              │
│  ├─ Create ExecutionContext                                    │
│  │  ├─ user_input                                              │
│  │  ├─ system_prompt (enhanced)                                │
│  │  ├─ max_iterations                                          │
│  │  └─ session_id                                              │
│  │                                                              │
│  ├─ Create pattern instance via ExecutionPatternFactory:       │
│  │  ├─ SIMPLE: Direct LLM call                                │
│  │  ├─ REACT: Thought/Action/Observation (ReactExecutor)      │
│  │  ├─ PLANNING: Plan first, then execute                     │
│  │  ├─ CHAIN_OF_THOUGHT: Step-by-step reasoning               │
│  │  ├─ TREE_OF_THOUGHTS: Multiple reasoning paths             │
│  │  └─ [Other patterns...]                                     │
│  │                                                              │
│  └─ Execute pattern:                                           │
│     └─ result = pattern_instance.execute(...)                 │
│        ├─ Prompt building (pattern-specific)                  │
│        ├─ LLM calls                                            │
│        ├─ Tool execution (if needed)                           │
│        └─ Return ExecutionResult                              │
│                                                                  │
│  Update pattern statistics:                                    │
│  ├─ pattern_usage[pattern] += 1                               │
│  └─ pattern_success_rates[pattern].append(success)            │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## ReAct Execution Loop Detail

```
┌────────────────────────────────────────────────────────────────┐
│              ReactExecutor._execute_loop()                      │
│              (react_executor.py: Lines 97-144)                  │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  While not context.is_complete():                              │
│  ├─ Iteration 1:                                               │
│  │  ├─ _build_prompt(context) [Lines 174-192]                │
│  │  │  ├─ Start with system_prompt                            │
│  │  │  ├─ Add: "\nUser: {user_input}"                         │
│  │  │  ├─ Add: conversation_history                            │
│  │  │  └─ Add: "\nPlease begin by thinking..."                │
│  │  │                                                          │
│  │  ├─ response = await llm_call(prompt)                      │
│  │  │  Example response:                                       │
│  │  │  "Thought: I need to search for information             │
│  │  │   Action: search                                         │
│  │  │   Action Input: {\"query\": \"...\"}"                    │
│  │  │                                                          │
│  │  ├─ parsed_action = action_parser.parse_action(response)   │
│  │  │  └─ Extracts: action="search", action_input={...}       │
│  │  │                                                          │
│  │  ├─ step = context.add_step(thought, action, action_input) │
│  │  │                                                          │
│  │  ├─ observation = await tool_call(action, action_input)    │
│  │  │  └─ Execute tool and capture result                     │
│  │  │                                                          │
│  │  └─ context.update_observation(observation)                │
│  │     └─ "Observation: Search found X results..."            │
│  │                                                              │
│  ├─ Iteration 2:                                               │
│  │  ├─ _build_prompt(context) [SAME WITH HISTORY]            │
│  │  │  ├─ system_prompt                                       │
│  │  │  ├─ "User: {original_input}"                            │
│  │  │  ├─ "Thought: ...\nAction: ...\nObservation: ..."      │
│  │  │  └─ "\nWhat should I do next?"                          │
│  │  │                                                          │
│  │  └─ [Same flow as iteration 1]                            │
│  │                                                              │
│  ├─ [Iterations 3-5 as needed]                                │
│  │                                                              │
│  └─ When agent outputs "Final Answer: ...":                   │
│     ├─ Extract final answer                                    │
│     ├─ context.mark_complete(final_answer)                     │
│     └─ Break from loop                                         │
│                                                                  │
│  Return ExecutionResult:                                        │
│  ├─ final_answer                                                │
│  ├─ iterations_used (e.g., 3)                                  │
│  ├─ steps (list of all iterations)                             │
│  ├─ total_tokens                                                │
│  └─ api_calls                                                   │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## Thought Formatting System

```
┌────────────────────────────────────────────────────────────────┐
│           ThoughtFormatter (thought_formatter.py)               │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  React Format Template (Lines 22-24):                          │
│  ───────────────────────────────────────────────────────────   │
│  "Thought: {thought}                                           │
│   Action: {action}                                             │
│   Action Input: {action_input}"                                │
│                                                                  │
│  Structured Format Template (Lines 26-34):                     │
│  ───────────────────────────────────────────────────────────   │
│  "Thought: Let me analyze this step by step.                  │
│                                                                  │
│   Observation: {observation}                                   │
│   Analysis: {analysis}                                          │
│   Reasoning: {reasoning}                                        │
│   Conclusion: {conclusion}                                      │
│                                                                  │
│   Action: {action}                                             │
│   Action Input: {action_input}"                                │
│                                                                  │
│  System Prompt Addition (Lines 193-212):                       │
│  ───────────────────────────────────────────────────────────   │
│  "When reasoning, structure your thoughts clearly:             │
│                                                                  │
│   1. Observation: What you observe from the situation          │
│   2. Analysis: Break down the problem                          │
│   3. Reasoning: Your logical thought process                   │
│   4. Conclusion: What you've determined                        │
│   5. Action: What you'll do next                               │
│                                                                  │
│   Format your responses as:                                    │
│   Thought: [reasoning]                                         │
│   Action: [action]                                             │
│   Action Input: [parameters]"                                  │
│                                                                  │
│  Methods:                                                       │
│  ├─ format_react_step() - Basic step                          │
│  ├─ format_structured_thought() - Detailed                    │
│  ├─ format_final_answer() - Final response                    │
│  ├─ format_error_recovery() - Error handling                  │
│  ├─ format_context_summary() - Task summary                   │
│  └─ extract_thought_components() - Parse response             │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## Context Integration Points

```
┌──────────────────────────────────────────────────────────────────┐
│                    CONTEXT SOURCES & INJECTION                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Source 1: User Configuration                                    │
│  ──────────────────────────────────────────────────────────────   │
│  - system_prompt parameter                                       │
│  - custom context dict                                           │
│  - execution_pattern parameter                                   │
│                                                                    │
│  Source 2: Tool System (tool_manager)                            │
│  ──────────────────────────────────────────────────────────────   │
│  - list_available_tools()                                        │
│  - Tool names, descriptions, parameters                         │
│  - Injected as: "You have access to these tools:"               │
│                                                                    │
│  Source 3: Memory System (memory_manager)                        │
│  ──────────────────────────────────────────────────────────────   │
│  - get_relevant_context(session_id, query)                       │
│    - Conversation history summary                                │
│    - Recent turns                                                │
│    - Conversation context                                        │
│                                                                    │
│  - search_memory(query, limit=3)                                 │
│    - Episodic memories                                           │
│    - Semantic memories                                           │
│    - User profile memories                                       │
│    - Ranked by: importance × similarity × recency                │
│                                                                    │
│  - search_memory() filtered for type="example"                   │
│    - Examples for in-context learning                            │
│    - Injected as: "Here are some examples:"                     │
│                                                                    │
│  Source 4: Execution Context                                     │
│  ──────────────────────────────────────────────────────────────   │
│  - ExecutionContext (current iteration state)                    │
│  - Conversation history from steps                               │
│  - Format instructions from pattern                              │
│                                                                    │
│  Injection Order (_build_enhanced_prompt):                       │
│  ──────────────────────────────────────────────────────────────   │
│  1. system_prompt                                                │
│  2. tool_descriptions                                            │
│  3. conversation_summary                                         │
│  4. relevant_memories                                            │
│  5. example_memories                                             │
│  6. custom_context                                               │
│  7. react_system_prompt                                          │
│                                                                    │
│  Final size: ~4000-8000 tokens                                   │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## Key Decision Points

```
┌────────────────────────────────────────────────────────────────┐
│            CRITICAL PROMPT BUILDING DECISIONS                   │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Q: Should optimization be enabled?                             │
│  ├─ NO  → Use system_prompt as-is                              │
│  └─ YES → Run optimization before execution                    │
│          └─ Select strategy: bootstrap, coordinate_ascent,     │
│                              bayesian                           │
│                                                                  │
│  Q: Should memory be included?                                  │
│  ├─ NO  → Skip memory retrieval                                │
│  └─ YES → Inject conversation + relevant memories             │
│           └─ How many: top-3 by relevance                      │
│                                                                  │
│  Q: Which execution pattern?                                    │
│  ├─ REACT (default) → Use ReAct loop                          │
│  ├─ CHAIN_OF_THOUGHT → Direct reasoning                       │
│  ├─ PLANNING → Plan then execute                              │
│  └─ AUTO → Select based on input complexity                   │
│                                                                  │
│  Q: What tools are available?                                   │
│  ├─ Include all tool descriptions in prompt                    │
│  └─ Let agent choose which to use                              │
│                                                                  │
│  Q: When to update system_prompt?                              │
│  ├─ Only after optimization completes                          │
│  └─ Only if improvement > 0                                    │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

