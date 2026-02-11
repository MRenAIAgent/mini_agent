# Dynamic MCP Selection - Design & Implementation

## Overview

**Problem**: Static MCP selection based only on system prompts is insufficient. Users may ask questions requiring tools not mentioned in the system prompt.

**Solution**: Dynamic MCP selection that analyzes user queries in real-time and hot-loads necessary MCPs during conversation.

---

## Example Scenario

### Without Dynamic Selection ❌

```python
# Agent initialized with system prompt
system_prompt = "You are a data analyst. You analyze databases and create reports."

# Baseline MCPs loaded: [calculator, database, visualization]

# User query
user: "What's the weather in New York?"

# Problem: Weather MCP not loaded!
# Agent response: "I don't have access to weather information."
```

### With Dynamic Selection ✅

```python
# Agent initialized with same system prompt
system_prompt = "You are a data analyst. You analyze databases and create reports."

# Baseline MCPs loaded: [calculator, database, visualization]

# User query
user: "What's the weather in New York?"

# Dynamic selection engine:
# 1. Analyzes query → detects "weather" capability
# 2. Scores all MCPs against query
# 3. Finds weather MCP with high relevance score
# 4. Hot-loads weather MCP during conversation
# 5. Agent can now answer the question!

agent: "The current weather in New York is 72°F and sunny."
```

---

## Architecture

### Two-Phase Selection Model

```
Phase 1: INITIALIZATION (Static)
┌─────────────────────────────────────┐
│  System Prompt Analysis             │
│  "You are a data analyst..."        │
└──────────────┬──────────────────────┘
               ▼
    ┌──────────────────────┐
    │ Baseline MCP Loading │
    │ - calculator         │
    │ - database           │
    │ - visualization      │
    └──────────────────────┘


Phase 2: RUNTIME (Dynamic)
┌─────────────────────────────────────┐
│  User Query Analysis                │
│  "What's the weather in NYC?"       │
└──────────────┬──────────────────────┘
               ▼
    ┌──────────────────────┐
    │ Query MCP Selection  │
    │ Detects: weather     │
    └──────────┬───────────┘
               ▼
    ┌──────────────────────┐
    │ Hot-Load MCP         │
    │ + weather            │
    └──────────────────────┘
```

---

## Implementation

### 1. Session Management

Track which MCPs are loaded for each conversation session:

```python
@dataclass
class MCPSession:
    """Tracks loaded MCPs for an agent session."""

    agent_id: str
    session_id: str
    loaded_mcps: Set[str]          # All currently loaded
    baseline_mcps: Set[str]        # From system prompt
    dynamic_mcps: Set[str]         # From user queries
    query_history: List[str]       # All user queries
    created_at: datetime
    last_updated: datetime
```

**Benefits:**
- Prevents duplicate loading
- Tracks conversation state
- Enables intelligent caching
- Supports session replay

### 2. Query-Based Selection

```python
async def select_mcps_for_query(
    self,
    user_query: str,
    session_id: str,
    agent_permissions: Set[str],
    max_new_mcps: int = 3,
    confidence_threshold: float = 0.3
) -> List[str]:
    """
    Dynamically select MCPs based on user query.

    Steps:
    1. Extract capabilities from query (keywords)
    2. Score all MCPs against query
    3. Filter already-loaded MCPs
    4. Apply permission checks
    5. Return top-K MCPs above confidence threshold
    """
```

**Example Flow:**

```python
# User query: "Send an email to john@example.com with the report"

# Step 1: Extract capabilities
capabilities = {"email", "communication", "send"}

# Step 2: Score MCPs
# email MCP: score = 1.0 (perfect match)
# slack MCP: score = 0.4 (partial match - communication)
# weather MCP: score = 0.0 (no match)

# Step 3: Filter already loaded
# email: not loaded ✓
# slack: not loaded ✓

# Step 4: Check permissions
# email requires: ["send:email"]
# agent has: ["send:email", "read:database"]
# ✓ Permission granted

# Step 5: Return top MCPs above threshold (0.3)
# Returns: ["email"]  (slack below max_new_mcps=3, but email is better match)
```

### 3. Hot-Loading Mechanism

```python
async def load_mcps_dynamically(
    self,
    session_id: str,
    mcp_names: List[str]
) -> Dict[str, bool]:
    """
    Hot-load MCPs during conversation.

    Uses callback pattern to integrate with MCP adapter:
    1. Get MCP metadata from registry
    2. Call loader callback (connects to MCP server)
    3. Update session state
    4. Return success/failure per MCP
    """
```

**Integration Pattern:**

```python
# In agent initialization
selection_engine = MCPSelectionEngine()

# Register loader callback
async def load_mcp(mcp_name: str, metadata: MCPMetadata) -> bool:
    """Connect to MCP server and register tools."""
    return await mcp_adapter.connect_server(
        mcp_name,
        metadata.connection
    )

selection_engine.set_mcp_loader(load_mcp)

# During conversation
new_mcps = await selection_engine.auto_select_for_query(
    user_query="What's the weather?",
    session_id=session.id,
    agent_permissions=agent.permissions,
    auto_load=True  # Automatically load selected MCPs
)

# new_mcps = ["weather"]  → automatically loaded!
```

---

## Configuration

### Enhanced Capability Patterns

Extended keyword patterns for better query detection:

```python
patterns = {
    "weather": [
        r"\bweather\b",
        r"\bforecast\b",
        r"\btemperature\b",
        r"\bclimate\b",
        r"\brain\b",
        r"\bsun\b"
    ],
    "email": [
        r"\bemail\b",
        r"\bsend\b.*\bmessage\b",
        r"\bmail\b",
        r"\bnotify\b"
    ],
    "search": [
        r"\bsearch\b",
        r"\bfind\b",
        r"\blookup\b",
        r"\bgoogle\b",
        r"\bweb\s+search\b"
    ],
    # ... more patterns
}
```

### Confidence Threshold Tuning

```yaml
# config/dynamic_selection.yaml
selection:
  confidence_threshold: 0.3  # Minimum score to trigger loading
  max_new_mcps_per_query: 3  # Limit hot-loads per query
  enable_auto_load: true     # Auto-load or ask for confirmation

  # Conservative (fewer false positives)
  # confidence_threshold: 0.5

  # Aggressive (more helpful, but may load unnecessary MCPs)
  # confidence_threshold: 0.2
```

---

## Usage Examples

### Example 1: Basic Dynamic Loading

```python
import asyncio
from tools.mcp_selection_engine import MCPSelectionEngine

async def main():
    # Initialize
    engine = MCPSelectionEngine()
    engine.load_registry_from_config(config)

    # Phase 1: Initialize agent with baseline MCPs
    baseline = await engine.select_mcps_for_agent(
        system_prompt="You are a data analyst",
        agent_role="analyst",
        agent_permissions={"read:database", "execute:calculations"}
    )
    # baseline = ["calculator", "database", "visualization"]

    # Create session
    session = engine.create_session(
        agent_id="analyst-001",
        session_id="sess-123",
        baseline_mcps=baseline
    )

    # Phase 2: Dynamic loading during conversation
    user_query = "What's the current weather in San Francisco?"

    new_mcps = await engine.select_mcps_for_query(
        user_query=user_query,
        session_id="sess-123",
        agent_permissions={"read:database", "execute:calculations", "read:api"}
    )
    # new_mcps = ["weather"]

    print(f"Dynamically selected: {new_mcps}")
    print(f"Total loaded: {session.loaded_mcps}")
    # Total loaded: {"calculator", "database", "visualization", "weather"}

asyncio.run(main())
```

### Example 2: Multi-Turn Conversation

```python
async def conversation_flow():
    engine = MCPSelectionEngine()

    # Initialize with baseline
    baseline = ["calculator", "database"]
    session = engine.create_session("agent-1", "sess-1", baseline)

    # Turn 1: Data analysis (uses baseline MCPs)
    query1 = "Calculate the average sales from the database"
    new_mcps = await engine.auto_select_for_query(
        query1, "sess-1", permissions, auto_load=True
    )
    # new_mcps = []  (already have calculator and database)

    # Turn 2: Weather question (triggers dynamic load)
    query2 = "What's the weather forecast for tomorrow?"
    new_mcps = await engine.auto_select_for_query(
        query2, "sess-1", permissions, auto_load=True
    )
    # new_mcps = ["weather"]  ✓ Hot-loaded!

    # Turn 3: Send email (triggers another dynamic load)
    query3 = "Email the report to team@company.com"
    new_mcps = await engine.auto_select_for_query(
        query3, "sess-1", permissions, auto_load=True
    )
    # new_mcps = ["email"]  ✓ Hot-loaded!

    # Session state
    print(session.baseline_mcps)  # {"calculator", "database"}
    print(session.dynamic_mcps)   # {"weather", "email"}
    print(session.loaded_mcps)    # All 4 MCPs
```

### Example 3: Permission Enforcement

```python
# Analyst role - limited permissions
analyst_permissions = {"read:database", "execute:calculations"}

# User asks to send email
query = "Send an email to customer@example.com"

new_mcps = await engine.select_mcps_for_query(
    query,
    session_id="sess-1",
    agent_permissions=analyst_permissions
)

# new_mcps = []
# Reason: email MCP requires "send:email" permission
# Analyst doesn't have it → email MCP NOT selected

logger.warning("Email MCP not loaded: missing send:email permission")
```

---

## Performance Optimizations

### 1. Caching

```python
# Selection results cached by query
cache_key = hash(query)
if cache_key in selection_cache:
    return cached_result
```

### 2. Lazy Loading

```python
# Don't actually connect to MCP server until first tool call
# Just mark as "selected" and connect on-demand
```

### 3. Unloading Unused MCPs

```python
def unload_unused_mcps(
    session_id: str,
    keep_recent: int = 5
) -> List[str]:
    """
    Unload MCPs that haven't been used recently.

    Keeps baseline MCPs always loaded.
    Only unloads dynamic MCPs after inactivity.
    """
    session = self.get_session(session_id)

    # Identify unused dynamic MCPs
    recent_queries = session.query_history[-keep_recent:]
    recent_capabilities = set()
    for query in recent_queries:
        recent_capabilities.update(self.extract_capabilities(query))

    to_unload = []
    for mcp_name in session.dynamic_mcps:
        metadata = self.get_mcp_metadata(mcp_name)
        # Check if MCP capabilities match recent queries
        if not any(cap in recent_capabilities
                   for cap in metadata.capabilities):
            to_unload.append(mcp_name)

    return to_unload
```

---

## Monitoring & Metrics

### Key Metrics

```python
metrics = {
    # Selection metrics
    "mcp.selection.query_triggered": Counter(),
    "mcp.selection.mcps_per_query": Histogram(),
    "mcp.selection.confidence_scores": Histogram(),

    # Loading metrics
    "mcp.loading.dynamic_loads": Counter(),
    "mcp.loading.load_success_rate": Gauge(),
    "mcp.loading.load_latency": Histogram(),

    # Session metrics
    "mcp.session.baseline_count": Histogram(),
    "mcp.session.dynamic_count": Histogram(),
    "mcp.session.total_loaded": Histogram(),
}
```

### Logging

```python
logger.info(
    f"Query '{query}' triggered loading of {len(new_mcps)} new MCPs",
    extra={
        "session_id": session_id,
        "new_mcps": new_mcps,
        "confidence_scores": scores,
        "total_loaded": len(session.loaded_mcps)
    }
)
```

---

## Security Considerations

### 1. Permission Checks

Dynamic loading MUST respect agent permissions:

```python
# Even if query triggers email MCP selection,
# it won't load if agent lacks "send:email" permission
```

### 2. Rate Limiting

Prevent abuse through rapid MCP loading:

```python
# config/security_policies.yaml
policies:
  - name: "rate_limit_dynamic_loading"
    rules:
      - condition: "dynamic_mcps_loaded_per_session > 10"
        action: "deny"
        reason: "Too many MCPs loaded in single session"
```

### 3. Audit Trail

Log all dynamic MCP loads:

```python
audit_logger.log_event(
    event_type="mcp_dynamic_load",
    agent_id=session.agent_id,
    session_id=session.session_id,
    mcp_name=mcp_name,
    triggered_by_query=user_query,
    timestamp=datetime.now()
)
```

---

## Testing

### Test Cases

```python
async def test_dynamic_selection():
    """Test MCP selection from user query."""
    engine = MCPSelectionEngine()
    engine.load_registry_from_config(test_config)

    session = engine.create_session("test", "sess-1", ["calculator"])

    # Query should trigger weather MCP
    new_mcps = await engine.select_mcps_for_query(
        "What's the weather?",
        "sess-1",
        {"read:api"}
    )

    assert "weather" in new_mcps
    assert "calculator" not in new_mcps  # Already loaded

async def test_permission_enforcement():
    """Test that permissions block unauthorized MCPs."""
    engine = MCPSelectionEngine()

    # Agent without email permission
    new_mcps = await engine.select_mcps_for_query(
        "Send an email",
        "sess-1",
        {"read:database"}  # No send:email
    )

    assert "email" not in new_mcps  # Blocked by permissions

async def test_confidence_threshold():
    """Test that low-confidence matches are filtered."""
    engine = MCPSelectionEngine()

    new_mcps = await engine.select_mcps_for_query(
        "Hello, how are you?",  # Generic greeting
        "sess-1",
        {"*"},
        confidence_threshold=0.3
    )

    assert len(new_mcps) == 0  # No MCPs match generic greeting
```

---

## Migration Path

### For Existing Agents

```python
# Before (static only)
class OldAgent:
    def __init__(self, system_prompt):
        mcps = select_mcps_for_agent(system_prompt)
        load_mcps(mcps)  # Load once at initialization

# After (static + dynamic)
class NewAgent:
    def __init__(self, system_prompt):
        # Phase 1: Static baseline
        baseline = select_mcps_for_agent(system_prompt)
        load_mcps(baseline)

        # Phase 2: Enable dynamic loading
        self.session = engine.create_session(
            self.id,
            session_id,
            baseline
        )

    async def handle_query(self, user_query):
        # Auto-select and load MCPs based on query
        new_mcps = await engine.auto_select_for_query(
            user_query,
            self.session.session_id,
            self.permissions
        )

        # Continue with query processing...
```

---

## Future Enhancements

### 1. Learning from Usage

```python
# Track which MCPs are actually used after loading
# Learn patterns: "weather query" → "weather MCP used 95% of time"
# Improve future selections
```

### 2. Predictive Loading

```python
# Analyze conversation context
# "User asked about data, then visualization"
# Pattern suggests: next might ask for email/sharing
# Preemptively load email MCP
```

### 3. Multi-Query Context

```python
# Consider last N queries, not just current one
# "Tell me about NYC" + "What's the weather there?"
# → Combine context for better selection
```

### 4. User Feedback Loop

```python
# After loading MCP, ask user:
# "I loaded the weather tool to answer your question. Was this helpful?"
# Use feedback to tune confidence thresholds
```

---

## Summary

**Dynamic MCP Selection** solves the critical limitation of static selection by:

✅ **Analyzing user queries in real-time**
✅ **Hot-loading MCPs during conversation**
✅ **Tracking session state** (baseline vs dynamic)
✅ **Respecting security policies** (permissions, rate limits)
✅ **Optimizing resource usage** (only load what's needed)

**Key Benefits:**
- More capable agents (can handle diverse queries)
- Better user experience (no "I can't do that" responses)
- Efficient resource usage (lazy loading)
- Maintains security (permission checks)

**Integration:**
- Backward compatible with static selection
- Simple API: `auto_select_for_query()`
- Flexible configuration (thresholds, limits)
- Comprehensive monitoring

This completes the MCP security layer with full dynamic selection support!
