# Persistent Agent Support Review

## Executive Summary

**Status**: ⚠️ **Partial Support** - Works but has **critical race conditions**

Your current `CoreAgent` implementation has the infrastructure for persistent agents (shared sidecar executor, tool manager), but has **critical race conditions** with `session_id` that will cause issues in production with concurrent requests.

## ✅ What Works

### 1. **Sidecar Executor Persistence** ✅
```python
# agent.py:204-212
self.sidecar_executor = SidecarExecutor(
    max_concurrent=50,
    default_timeout=60
)
```

**Status**: ✅ CORRECT
- Executor is created once per agent instance
- `_active_tasks` set persists across requests
- Background tasks stay alive after request completes
- **Works perfectly for persistent agents**

### 2. **Tool Manager Sharing** ✅
```python
# agent.py:163
self.tool_manager = ToolManager()
```

**Status**: ✅ CORRECT
- Single tool manager shared across requests
- Connection pooling works
- No race conditions

### 3. **Memory Manager Architecture** ✅
```python
# agent.py:165-168
if enable_memory:
    self.memory_manager = CoreMemoryManager()
```

**Status**: ✅ CORRECT
- Shared memory manager is fine
- Memory isolation happens via `session_id` parameter
- Sidecars correctly pass `session_id` from context

## ❌ Critical Issues

### Issue #1: **Race Condition in session_id** 🔴 CRITICAL

**Location**: `agent.py:151`
```python
self.session_id = session_id or str(uuid.uuid4())
```

**Problem**:
```python
# Persistent agent
agent = CoreAgent()  # session_id = "default-123"

# Request A (concurrent)
agent.session_id = "user-A"
await agent.run("Hello")  # Uses session "user-A"

# Request B (concurrent, overlaps with A)
agent.session_id = "user-B"  # ❌ OVERWRITES A's session!

# Request A continues...
# Sidecar triggers with context["session_id"] = ???
# Could be "user-B" if B ran after A started but before sidecars triggered!
```

**Timeline**:
```
Time    Request A              Request B              session_id
─────────────────────────────────────────────────────────────────
0ms     session_id = "A"                              "A"
1ms     start run()                                   "A"
2ms                            session_id = "B"       "B" ❌
3ms     trigger sidecars                              "B"
4ms     sidecars use "B"! ❌                          "B"
```

**Impact**:
- User A's conversation stored in User B's session!
- **Data leak between users!** 🔴
- Memory corruption

---

### Issue #2: **Clone Method Creates New Executor** 🔴 CRITICAL

**Location**: `agent.py:884-896`
```python
def clone(self, session_id: Optional[str] = None) -> 'CoreAgent':
    clone = CoreAgent(
        llm_function=self.llm_function,
        system_prompt=self.system_prompt,
        max_iterations=self.max_iterations,
        enable_memory=self.memory_manager is not None,
        enable_optimization=self.optimizer is not None,
        session_id=session_id
    )
    return clone  # ❌ Creates NEW executor!
```

**Problem**:
```python
# Using clone for request isolation
request_agent = agent.clone(session_id="user-123")
response = await request_agent.run("Hello")
# Sidecars triggered on request_agent.sidecar_executor
# BUT this is a NEW executor, not the parent's!

# request_agent goes out of scope...
# request_agent.sidecar_executor destroyed
# Sidecar tasks lose references! ❌
```

**Why it fails**:
- Clone creates a **completely new agent**
- New `SidecarExecutor` created
- New `MemoryManager` created (wasteful!)
- New `ToolManager` created (loses connections!)
- **Defeats the entire purpose of persistent agents!**

---

### Issue #3: **Missing llm_config in Clone** ⚠️ MEDIUM

**Location**: `agent.py:885`
```python
clone = CoreAgent(
    llm_function=self.llm_function,  # ✅ Copied
    # ❌ Missing: llm_config
    system_prompt=self.system_prompt,
    ...
)
```

**Problem**:
- If original agent uses `llm_config`, clone won't have it
- Clone will fail validation check

---

### Issue #4: **No Session Parameter in run()** ⚠️ MEDIUM

**Location**: `agent.py:397-402`
```python
async def run(
    self,
    user_input: str,
    context: Optional[Dict[str, Any]] = None,
    execution_pattern: Optional[ExecutionPatternType] = None
) -> str:
```

**Problem**:
- No `session_id` parameter in `run()`
- Must modify `self.session_id` directly (race condition!)
- No clean way to override session per request

---

## 🔧 Required Fixes

### Fix #1: Add session_id Parameter to run()

**Priority**: 🔴 CRITICAL

```python
async def run(
    self,
    user_input: str,
    context: Optional[Dict[str, Any]] = None,
    execution_pattern: Optional[ExecutionPatternType] = None,
    session_id: Optional[str] = None  # ✅ Add this
) -> str:
    """
    Run the agent on a user input.

    Args:
        user_input: The user's question or request
        context: Optional additional context
        execution_pattern: Optional specific pattern to use
        session_id: Override session_id for this request (thread-safe)

    Returns:
        The agent's response
    """
    # Use provided session_id or fall back to instance session_id
    effective_session = session_id or self.session_id

    print(f"🔧 [AGENT] Session ID: {effective_session}")

    # ... rest of execution ...

    # Build context for sidecars with effective_session
    context = {
        "session_id": effective_session,  # ✅ Use effective session
        "user_input": user_input,
        "response": response,
        ...
    }

    self._trigger_sidecars(...)
```

**Usage (Thread-Safe)**:
```python
# Persistent agent
agent = CoreAgent(...)

# Request A
response_a = await agent.run("Hello", session_id="user-A")  # ✅ Safe

# Request B (concurrent)
response_b = await agent.run("Hi", session_id="user-B")     # ✅ Safe

# No race condition! Each request has its own session.
```

---

### Fix #2: Fix clone() to Share Resources

**Priority**: 🔴 CRITICAL

```python
def clone(self, session_id: Optional[str] = None) -> 'CoreAgent':
    """
    Create a lightweight clone for a new session.

    Shares: tool_manager, sidecar_executor, memory_manager (thread-safe)
    Isolates: session_id only

    Args:
        session_id: Session ID for the clone

    Returns:
        Lightweight clone that shares resources with parent
    """
    # Create new agent instance
    clone = CoreAgent.__new__(CoreAgent)

    # Copy configuration
    clone.llm_function = self.llm_function
    clone.llm_config = self.llm_config
    clone.system_prompt = self.system_prompt
    clone.max_iterations = self.max_iterations
    clone.enable_tracing = self.enable_tracing
    clone.execution_pattern = self.execution_pattern
    clone.enable_pattern_selection = self.enable_pattern_selection
    clone.enable_sidecars = self.enable_sidecars

    # SHARE managers (thread-safe)
    clone.tool_manager = self.tool_manager                # ✅ Shared
    clone.memory_manager = self.memory_manager            # ✅ Shared
    clone.optimizer = self.optimizer                      # ✅ Shared
    clone.sidecar_registry = self.sidecar_registry        # ✅ Shared
    clone.sidecar_executor = self.sidecar_executor        # ✅ Shared (CRITICAL!)

    # SHARE executors
    clone.executor = self.executor
    clone.pattern_executor = self.pattern_executor

    # ISOLATE session
    clone.session_id = session_id or str(uuid.uuid4())    # ✅ Unique per clone

    # Initialize state
    clone.current_context = None
    clone.optimization_history = []
    clone.current_pattern = self.execution_pattern

    return clone
```

**Why this works**:
- ✅ Shares `sidecar_executor` - background tasks persist!
- ✅ Shares `memory_manager` - no duplication
- ✅ Shares `tool_manager` - connection pooling works
- ✅ Isolates `session_id` - no race conditions
- ✅ Lightweight - no initialization overhead

**Usage**:
```python
# Persistent agent
agent = CoreAgent(...)

@app.post("/chat")
async def chat(request: ChatRequest):
    # Clone with unique session (fast!)
    request_agent = agent.clone(session_id=request.session_id)

    # Run (uses its own session_id)
    response = await request_agent.run(request.message)

    # Sidecars use parent's executor ✅
    # Background tasks persist after request ends ✅

    return {"response": response}
```

---

### Fix #3: Make _build_enhanced_prompt Session-Safe

**Priority**: ⚠️ MEDIUM

```python
async def _build_enhanced_prompt(
    self,
    user_input: str,
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None  # ✅ Add parameter
) -> str:
    """Build enhanced system prompt with context and memory."""
    effective_session = session_id or self.session_id  # ✅ Thread-safe

    prompt_parts = [self.system_prompt]

    # ... tool descriptions ...

    # Add memory context (with explicit session)
    if self.memory_manager:
        relevant_context = await self.memory_manager.get_relevant_context(
            session_id=effective_session,  # ✅ Use parameter
            query=user_input
        )
        # ... rest of logic ...

    return "\n".join(prompt_parts)
```

---

### Fix #4: Thread-Safe Session in Sidecars

**Priority**: 🟡 LOW (Already correct!)

The sidecar implementation is **already thread-safe**:

```python
# sidecars/implementations.py:54-58
await self.memory_manager.add_conversation_turn(
    session_id=context["session_id"],  # ✅ From context, not self
    user_input=context["user_input"],
    agent_response=context["response"],
    execution_result=context["execution_result"]
)
```

✅ No changes needed - already uses `context["session_id"]`

---

## 📋 Implementation Priority

### Phase 1: Critical Fixes (Required for Production)

1. ✅ Add `session_id` parameter to `run()` method
2. ✅ Fix `clone()` to share resources
3. ✅ Update `_build_enhanced_prompt()` to accept session parameter
4. ✅ Pass session through execution chain

### Phase 2: Nice-to-Have

5. Add session validation
6. Add session metrics/tracking
7. Document thread-safety guarantees

---

## ✅ Recommended API Pattern

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Global persistent agent
agent: CoreAgent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent

    # Startup: Create persistent agent
    agent = CoreAgent(
        llm_config=config,
        enable_memory=True,
        enable_sidecars=True
    )
    await agent.start()

    yield

    # Shutdown: Wait for sidecars
    await agent.stop()

app = FastAPI(lifespan=lifespan)

# Option 1: Pass session_id to run() (recommended after Fix #1)
@app.post("/chat")
async def chat(request: ChatRequest):
    response = await agent.run(
        user_input=request.message,
        session_id=request.session_id  # ✅ Thread-safe!
    )
    return {"response": response}

# Option 2: Use clone() (recommended after Fix #2)
@app.post("/chat")
async def chat(request: ChatRequest):
    # Lightweight clone (shares resources)
    request_agent = agent.clone(session_id=request.session_id)
    response = await request_agent.run(request.message)
    return {"response": response}
```

---

## 🎯 Summary

### Current State
- ✅ Sidecar executor persists correctly
- ✅ Background tasks work
- ❌ Race conditions with session_id
- ❌ Clone creates too many new objects

### After Fixes
- ✅ Thread-safe session handling
- ✅ Lightweight clones
- ✅ Resource sharing
- ✅ Production-ready

### Estimated Implementation Time
- Fix #1 (session parameter): 30 minutes
- Fix #2 (clone method): 1 hour
- Fix #3 (prompt building): 20 minutes
- Testing: 1 hour
- **Total**: ~3 hours

**Priority**: 🔴 **Implement before production deployment!**
