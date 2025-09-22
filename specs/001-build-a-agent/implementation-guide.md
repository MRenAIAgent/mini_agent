# Implementation Guide: Enhanced Agent Framework Refactoring

## Refactoring Roadmap with Specific File References

### Phase 1: Core Agent LLM Integration Refactoring

#### 1.1 Update Agent Constructor for LiteLLM
**File**: `/agent.py`
**Current**: Line 34 - `llm_function: Callable[[str], Awaitable[str]]`
**Target**: Replace with LiteLLM configuration

```python
# BEFORE (agent.py:32-42)
def __init__(
    self,
    llm_function: Callable[[str], Awaitable[str]],  # <- REPLACE THIS
    system_prompt: str = "",
    max_iterations: int = 5,
    # ...
):

# AFTER - New signature needed
def __init__(
    self,
    llm_config: LLMConfig,  # <- NEW: Use data-model.md LLMProvider entity
    system_prompt: str = "",
    max_iterations: int = 5,
    enable_streaming: bool = False,  # <- NEW: Add streaming support
    # ...
):
```

**Implementation Steps**:
1. Add LiteLLM dependency to requirements
2. Create `integrations/litellm_provider.py` (see data-model.md LLMProvider entity)
3. Modify agent.py constructor
4. Update `_enhanced_llm_call` method (agent.py:385) to use LiteLLM
5. Add streaming support to agent responses

#### 1.2 Add Streaming Support (SIMPLIFIED)
**Files to Modify**:
- `agent.py:385-391` - Modify `_enhanced_llm_call` to support streaming
- `agent.py` - Add simple `run_stream()` method

**Constitutional Compliance**: Keep streaming simple - no separate handler classes

```python
# SIMPLE streaming addition to agent.py
async def run_stream(
    self,
    user_input: str,
    context: Optional[Dict[str, Any]] = None
) -> AsyncIterator[str]:
    """Simple streaming implementation using LiteLLM directly."""
    enhanced_prompt = await self._build_enhanced_prompt(user_input, context)
    async for chunk in litellm.acompletion(
        messages=[{"role": "user", "content": enhanced_prompt}],
        stream=True, **self.llm_config
    ):
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

### Phase 2: Execution Pattern Enhancement

#### 2.1 Extend Execution Patterns
**File**: `/execution/execution_patterns.py`
**Current**: Line 19-30 has enum with REACT, CHAIN_OF_THOUGHT, etc.
**Gap**: Missing PLANNING, AUTO, SIMPLE modes from user requirements

**Action Required**:
```python
# ADD to execution_patterns.py ExecutionPatternType enum:
class ExecutionPatternType(Enum):
    # ... existing patterns ...
    PLANNING = "planning"        # <- ADD: Multi-step planning mode
    AUTO = "auto"               # <- ADD: Intelligent pattern selection
    SIMPLE = "simple"           # <- ADD: Fast response mode
```

#### 2.2 Implement Missing Patterns (SIMPLIFIED)
**Files to Modify** (Not Create):
- `execution/pattern_executor.py` - Add simple pattern logic directly
- `execution/react_executor.py` - Extend for planning and simple modes

**Constitutional Compliance**: Extend existing files instead of creating new modules

**Simple Implementation**:
```python
# ADD to pattern_executor.py instead of separate files
def _execute_simple_pattern(self, user_input: str) -> str:
    """Simple pattern: direct LLM call without reasoning steps."""
    return await self.llm_call(f"Answer concisely: {user_input}")

def _execute_planning_pattern(self, user_input: str) -> str:
    """Planning pattern: plan then execute using existing ReAct."""
    plan = await self.llm_call(f"Create step-by-step plan: {user_input}")
    return await self._execute_react_pattern(f"Execute plan: {plan}")
```

### Phase 3: Memory System Backend Integration

#### 3.1 Memory Backend Implementation
**Current Structure**: `memory/memory_manager.py` uses abstract interfaces
**Files to Create**:
- `memory/backends/memgraph_backend.py`
- `memory/backends/redis_backend.py`
- `memory/backends/__init__.py`

**Reference**: data-model.md lines 210+ for Knowledge Graph Schema
**Configuration**: Use data-model.md MemoryConfig entity structure

#### 3.2 Human-like Memory Features
**Files to Modify**:
- `memory/memory_manager.py` - Add temporal decay (research.md lines 87-99)
- `memory/memory_store.py` - Add importance scoring
- Add `memory/temporal_decay.py` - Implement decay algorithms

**Reference**: research.md lines 87-99 for memory simulation approach

### Phase 4: Simplified Benchmarking (CONSTITUTIONAL COMPLIANCE)

#### 4.1 Simple Benchmark Integration
**Files to Modify** (Not Create New Module):
- `agent.py` - Add simple benchmark method
- `tools/` - Extend existing tool system for benchmarks

**Constitutional Compliance**: Use existing infrastructure, avoid new modules

```python
# ADD to agent.py - simple benchmark method
async def run_benchmark(self, test_cases: List[str]) -> Dict[str, Any]:
    """Simple benchmark: time responses on test cases."""
    results = []
    for case in test_cases:
        start_time = time.time()
        response = await self.run(case)
        duration = time.time() - start_time
        results.append({"input": case, "response": response, "time": duration})
    return {"framework": "mini_agent", "results": results}
```

### Phase 5: Simplified In-Context Learning (CONSTITUTIONAL COMPLIANCE)

#### 5.1 Simple Example System
**Files to Modify** (Not Create New Module):
- `agent.py:338-383` - Enhance `_build_enhanced_prompt` method
- `memory/memory_manager.py` - Store examples as regular memories

**Constitutional Compliance**: Reuse existing memory system, avoid complexity

```python
# SIMPLE approach: store examples as memories, retrieve by similarity
async def add_example(self, input_text: str, output_text: str):
    """Store example in existing memory system."""
    await self.memory_manager.store_memory(
        content=f"Example: {input_text} -> {output_text}",
        importance=1.0,
        metadata={"type": "example"}
    )

# Enhance existing prompt building
async def _build_enhanced_prompt(self, user_input: str, context=None) -> str:
    # ... existing code ...
    # Add simple example retrieval
    examples = await self.memory_manager.search_memory(
        query=user_input, limit=3, filters={"type": "example"}
    )
    if examples:
        example_text = "\n".join([mem.content for mem in examples])
        prompt_parts.append(f"\nExamples:\n{example_text}")
```

## Configuration Updates Needed

### 5.1 Minimal Dependencies (CONSTITUTIONAL COMPLIANCE)
**File**: `requirements.txt` or `pyproject.toml`
**Add Only Essential**:
```
litellm>=1.0.0  # Core LLM integration
memgraph>=1.0.0  # Memory backend (optional)
redis>=4.0.0     # Cache backend (optional)
```

### 5.2 Simple Configuration
**Modify**: Existing agent configuration
**Keep Simple**:
```python
# Simple LLM config (no complex environment management)
llm_config = {
    "provider": "openai",
    "model": "gpt-4",
    "api_key": "your-key",
    "stream": True
}
agent = CoreAgent(llm_config=llm_config)
```

## Testing Implementation Order

### Contract Tests First (TDD)
1. `tests/contract/test_agent_core_api.py` - Test enhanced agent API
2. `tests/contract/test_streaming_api.py` - Test streaming endpoints
3. `tests/contract/test_benchmark_api.py` - Test benchmark endpoints

### Integration Tests
1. `tests/integration/test_litellm_integration.py`
2. `tests/integration/test_memory_backends.py`
3. `tests/integration/test_execution_patterns.py`

### Backward Compatibility Tests
1. `tests/compatibility/test_existing_api.py` - Ensure existing functionality works
2. `tests/compatibility/test_migration.py` - Test upgrade paths

## Migration Strategy

### Preserving Existing Functionality
**Critical**: Maintain existing `agent.py` public API
**Strategy**: Add new parameters with defaults, deprecate old patterns gradually

```python
# Maintain backward compatibility
def __init__(
    self,
    llm_function: Optional[Callable[[str], Awaitable[str]]] = None,  # DEPRECATED but supported
    llm_config: Optional[LLMConfig] = None,  # NEW preferred way
    # ... existing parameters with same defaults
):
    if llm_function and not llm_config:
        # Wrap legacy function in LiteLLM compatibility layer
        llm_config = LegacyLLMConfig(llm_function)
```

## Implementation Task Dependencies

### Critical Path
1. LiteLLM integration → Streaming support → Enhanced execution patterns
2. Memory backends → Human-like memory features
3. Benchmark framework → Performance comparison
4. All above → In-context learning integration

### Parallel Development Streams
- **Stream A**: LLM integration + Streaming (agent.py, integrations/)
- **Stream B**: Memory backends (memory/, new backends/)
- **Stream C**: Benchmarking (benchmarks/, new module)
- **Stream D**: Execution patterns (execution/, pattern extensions)

This implementation guide provides the specific file references and modification points that were missing from the original plan.