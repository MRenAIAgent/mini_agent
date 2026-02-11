# Multi-Agent System Quick Start Guide

**Purpose**: Get started with the multi-agent system quickly
**Audience**: Developers implementing or using the system
**Time to read**: 10 minutes

---

## What is This?

A multi-agent system inspired by Claude Code that uses an **orchestrator-worker pattern** to solve complex tasks efficiently. Think of it as having a lead developer (orchestrator) coordinating a team of specialized developers (subagents).

### Key Benefits

- **90%+ faster** on complex research tasks
- **Parallel execution** of independent subtasks
- **Specialized agents** for different task types
- **Context isolation** to handle more work within token limits
- **Resumable execution** with checkpointing

---

## Architecture in 60 Seconds

```
User Query
    ↓
OrchestratorAgent (The Brain)
    ↓
    ├─→ ExploreAgent (Research & Discovery)
    ├─→ PlanAgent (Design & Planning)
    ├─→ ImplementAgent (Code Writing)
    ├─→ ReviewAgent (Quality Assurance)
    └─→ DebugAgent (Troubleshooting)
    ↓
Synthesized Result
```

### How It Works

1. **User** asks a complex question
2. **Orchestrator** analyzes and breaks it down
3. **Subagents** execute tasks in parallel
4. **Orchestrator** synthesizes results
5. **User** gets comprehensive answer

---

## Agent Types Cheat Sheet

| Agent | Use When | Model | Speed |
|-------|----------|-------|-------|
| **Orchestrator** | Always (main agent) | Opus 4 | Slow |
| **Explore** | Need to search codebase | Sonnet 4 | Fast |
| **Plan** | Need to design solution | Sonnet 4 | Fast |
| **Implement** | Need to write code | Sonnet 4 | Fast |
| **Review** | Need to check quality | Sonnet 4 | Fast |
| **Debug** | Need to fix errors | Sonnet 4 | Fast |

---

## Usage Examples

### Example 1: Simple Codebase Search

```python
from multi_agent import OrchestratorAgent
from multi_agent.protocols import AgentTask

# Create orchestrator
orchestrator = OrchestratorAgent(
    model="claude-opus-4",
    memory_backend="redis"
)

# Delegate to ExploreAgent
result = await orchestrator.delegate(
    AgentTask(
        agent_type="explore",
        task_description="Find all authentication code",
        thoroughness="medium"
    )
)

print(result.summary)
# Output: Found 15 files related to authentication...
```

**When to use**: Need to search codebase for specific patterns

**Time**: ~5-10 seconds

**Cost**: ~$0.05

---

### Example 2: Parallel Research

```python
# Launch 3 agents in parallel to research different aspects
tasks = [
    AgentTask("explore", "Find API endpoints"),
    AgentTask("explore", "Find database schema"),
    AgentTask("explore", "Find error handling")
]

results = await orchestrator.delegate_parallel(tasks)

# Synthesize all findings
summary = await orchestrator.synthesize(results)
```

**When to use**: Need information from multiple independent sources

**Time**: ~10-15 seconds (vs 30-45 seconds sequential)

**Cost**: ~$0.15

**Speedup**: 3× faster

---

### Example 3: Plan → Implement → Review Pipeline

```python
# Multi-phase implementation workflow
pipeline = [
    AgentTask("plan", "Design user authentication system"),
    AgentTask("implement", "Implement the auth system"),
    AgentTask("review", "Review for security issues")
]

results = await orchestrator.execute_pipeline(pipeline)

for phase, result in zip(["Plan", "Implement", "Review"], results):
    print(f"{phase}: {result.status}")

# Output:
# Plan: SUCCESS
# Implement: SUCCESS
# Review: SUCCESS (with recommendations)
```

**When to use**: Need complete implementation workflow

**Time**: ~60-120 seconds

**Cost**: ~$1.00

---

### Example 4: Complex Research Task

```python
# User asks: "How does authentication work in this codebase?"

# Orchestrator automatically:
# 1. Launches ExploreAgent to find auth code
# 2. Launches another ExploreAgent to find auth docs
# 3. Launches another ExploreAgent to find tests
# 4. Synthesizes comprehensive answer

result = await orchestrator.process(
    "Explain how authentication works in this codebase"
)

# Orchestrator returns detailed explanation with:
# - Architecture overview
# - Key files and their roles
# - Security considerations
# - Testing approach
```

**When to use**: Complex questions requiring comprehensive research

**Time**: ~30-60 seconds

**Cost**: ~$0.50

---

## Decision Tree: Which Agent?

```
Need to understand codebase?
├─ Yes → ExploreAgent
└─ No ↓

Need to design solution?
├─ Yes → PlanAgent
└─ No ↓

Need to write code?
├─ Yes → ImplementAgent
└─ No ↓

Need to review code?
├─ Yes → ReviewAgent
└─ No ↓

Need to fix bugs?
├─ Yes → DebugAgent
└─ No → Handle in Orchestrator
```

---

## Coordination Patterns

### Pattern 1: Simple Delegation (1 → 1)

```python
# One orchestrator, one subagent
result = await orchestrator.delegate(task)
```

**Use for**: Single specialized task

**Example**: "Find all error handling code"

---

### Pattern 2: Parallel Fan-Out (1 → N)

```python
# One orchestrator, multiple parallel subagents
results = await orchestrator.delegate_parallel([task1, task2, task3])
```

**Use for**: Independent research tasks

**Example**: "Find API endpoints, database schema, and error handling"

---

### Pattern 3: Sequential Pipeline (1 → 1 → 1 → 1)

```python
# One orchestrator, sequential subagents
results = await orchestrator.execute_pipeline([plan, implement, review])
```

**Use for**: Multi-phase workflows

**Example**: "Plan → Implement → Review"

---

### Pattern 4: Iterative Refinement (1 ⟲ 1)

```python
# One orchestrator, repeated subagent with feedback
for i in range(max_iterations):
    result = await orchestrator.delegate(task)
    if orchestrator.is_acceptable(result):
        break
    task.context["feedback"] = orchestrator.generate_feedback(result)
```

**Use for**: Tasks requiring refinement

**Example**: "Keep improving until code passes all checks"

---

## Token & Cost Management

### Token Multipliers

- **Single agent chat**: 1× (baseline)
- **Single agent with tools**: 4×
- **Multi-agent system**: 15×

### Cost Estimation Formula

```
Cost = (orchestrator_tokens + Σ subagent_tokens) × price_per_token

Example:
- Orchestrator: 50K tokens
- 3 subagents: 3 × 30K = 90K tokens
- Total: 140K tokens
- Cost: 140K × $0.003 = $0.42
```

### When Is It Worth It?

**Worth the cost**:
- Complex research requiring multiple sources
- Tasks saved developer multiple hours
- High-value decisions
- One-time comprehensive analysis

**Not worth the cost**:
- Simple factual queries
- Single file operations
- Quick lookups
- Repeated simple tasks

---

## Performance Tips

### 1. Choose Right Thoroughness

```python
# Quick: 1-3 operations (~5s, $0.02)
AgentTask("explore", "Find main.py", thoroughness="quick")

# Medium: 5-10 operations (~10s, $0.05)
AgentTask("explore", "Find auth code", thoroughness="medium")

# Thorough: 20+ operations (~30s, $0.15)
AgentTask("explore", "Analyze entire architecture", thoroughness="very thorough")
```

### 2. Use Parallel When Possible

```python
# Slow (sequential): 30 seconds
for task in tasks:
    result = await orchestrator.delegate(task)

# Fast (parallel): 10 seconds
results = await orchestrator.delegate_parallel(tasks)
```

### 3. Prune Context Aggressively

```python
# Bad: Send entire 100K context to subagent
task.context = full_context  # Wastes tokens

# Good: Send only relevant 10K context
task.context = extract_relevant(full_context, task)
```

### 4. Cache Common Prompts

```python
# System prompts and common contexts are cached
# Reduces token usage by 40%+
orchestrator.enable_prompt_caching()
```

---

## Error Handling

### Automatic Retry

```python
# Subagent failures are automatically retried
result = await orchestrator.delegate(task)

# Behind the scenes:
# - Try 1: Fails due to timeout
# - Try 2 (after 2s): Fails due to rate limit
# - Try 3 (after 4s): Success
```

### Checkpoint & Resume

```python
# System automatically checkpoints progress
orchestrator.enable_checkpointing()

# If crash occurs, restore from last checkpoint
if orchestrator.has_checkpoint():
    orchestrator.restore_from_checkpoint()
```

### Graceful Degradation

```python
# If subagent fails, orchestrator adapts
results = await orchestrator.delegate_parallel([task1, task2, task3])

# Even if task2 fails, orchestrator synthesizes from task1 and task3
# User gets partial but useful result
```

---

## Debugging

### Enable Detailed Logging

```python
import structlog

orchestrator = OrchestratorAgent(
    log_level="DEBUG",
    trace_agents=True
)

# Logs show:
# - Agent launches
# - Tool calls
# - Token usage
# - Timing
# - Errors
```

### Visualize Agent Execution

```python
from multi_agent.observability import AgentVisualizer

visualizer = AgentVisualizer(orchestrator)
await orchestrator.process(query)

# Shows tree view:
# Orchestrator
# ├─ ExploreAgent (10s, 30K tokens)
# ├─ ExploreAgent (12s, 35K tokens)
# └─ PlanAgent (15s, 40K tokens)
```

### Inspect Agent Results

```python
result = await orchestrator.delegate(task)

print(f"Status: {result.status}")
print(f"Tokens: {result.tokens_used}")
print(f"Time: {result.execution_time}s")
print(f"Tool calls: {len(result.tool_calls)}")
print(f"Summary: {result.summary}")

if result.error:
    print(f"Error: {result.error}")
```

---

## Best Practices

### ✅ DO

- **Start simple**: Try single agent before parallel
- **Set budgets**: Limit tokens per task
- **Monitor costs**: Track token usage
- **Use thoroughness levels**: Don't over-explore
- **Checkpoint expensive operations**: Enable resumability
- **Provide clear task descriptions**: Better results
- **Define success criteria**: Know when done

### ❌ DON'T

- **Over-parallelize**: Don't launch 50 agents
- **Ignore token costs**: Monitor spending
- **Skip error handling**: Always handle failures
- **Send full context**: Prune aggressively
- **Use for simple tasks**: Overkill for "read file"
- **Forget timeouts**: Set reasonable limits
- **Ignore feedback**: Learn from results

---

## Configuration

### Basic Configuration

```python
from multi_agent import OrchestratorAgent
from multi_agent.config import AgentConfig

config = AgentConfig(
    # Models
    orchestrator_model="claude-opus-4",
    subagent_model="claude-sonnet-4",

    # Limits
    max_parallel_agents=5,
    max_tokens_per_agent=50_000,
    timeout_seconds=300,

    # Optimization
    enable_caching=True,
    enable_checkpointing=True,
    context_pruning="aggressive",

    # Budget
    token_budget=1_000_000,
    warn_at_percent=80,

    # Backend
    memory_backend="redis",
    state_backend="redis"
)

orchestrator = OrchestratorAgent(config=config)
```

### Environment Variables

```bash
# .env file
MULTI_AGENT_ORCHESTRATOR_MODEL=claude-opus-4
MULTI_AGENT_SUBAGENT_MODEL=claude-sonnet-4
MULTI_AGENT_MAX_PARALLEL=5
MULTI_AGENT_TOKEN_BUDGET=1000000
REDIS_URL=redis://localhost:6379
```

---

## Troubleshooting

### Problem: Agent too slow

**Solution**:
- Use "quick" thoroughness
- Reduce max iterations
- Use Sonnet instead of Opus for subagents

### Problem: Token costs too high

**Solution**:
- Enable aggressive context pruning
- Set strict token budgets
- Use caching
- Reduce parallel agents

### Problem: Agent gives incomplete results

**Solution**:
- Increase thoroughness level
- Provide more context in task description
- Add explicit success criteria
- Increase token budget

### Problem: Frequent timeouts

**Solution**:
- Increase timeout setting
- Break task into smaller subtasks
- Check network connectivity
- Reduce task complexity

---

## Next Steps

1. **Read** full design doc: `MULTI_AGENT_SYSTEM_DESIGN.md`
2. **Review** implementation roadmap: `MULTI_AGENT_IMPLEMENTATION_ROADMAP.md`
3. **Try** examples in `examples/` directory
4. **Explore** API reference: `MULTI_AGENT_API.md`
5. **Join** development: See `CONTRIBUTING.md`

---

## Quick Reference Card

### Common Operations

```python
# Import
from multi_agent import OrchestratorAgent
from multi_agent.protocols import AgentTask

# Create orchestrator
orch = OrchestratorAgent()

# Single agent
result = await orch.delegate(AgentTask("explore", "Find X"))

# Parallel
results = await orch.delegate_parallel([task1, task2])

# Pipeline
results = await orch.execute_pipeline([plan, impl, review])

# Process query directly (orchestrator decides)
result = await orch.process("How does auth work?")
```

### Agent Types

- `explore` - Search codebase
- `plan` - Design solutions
- `implement` - Write code
- `review` - Check quality
- `debug` - Fix problems

### Thoroughness Levels

- `quick` - Fast, basic (~5s)
- `medium` - Balanced (~10s)
- `very thorough` - Comprehensive (~30s)

---

**Questions?** See full documentation or ask in discussion forum.

**Ready to implement?** See `MULTI_AGENT_IMPLEMENTATION_ROADMAP.md`

