# MCP Security Layer - Quick Start Guide

## Overview

The MCP Security Layer adds intelligent selection and security controls to MCP (Model Context Protocol) integration. It provides:

1. **Intelligent MCP Selection** - Automatically loads only relevant MCPs
   - **Static**: Based on agent system prompt (initialization)
   - **Dynamic**: Based on user queries (runtime hot-loading)
2. **Security Policies** - Fine-grained access control and threat prevention
3. **Input Validation** - Protection against injection attacks
4. **Audit Logging** - Complete trail of all MCP operations

## Architecture

```
Agent → Selection Engine → Security Middleware → MCP Adapter → MCP Servers
```

## Quick Start

### 1. Define MCP Registry

Create `config/mcp_registry.yaml`:

```yaml
mcp_servers:
  calculator:
    description: "Mathematical calculations"
    categories: ["computation", "math"]
    capabilities: ["arithmetic", "statistics"]
    required_permissions: []
    risk_level: "low"
    connection:
      server_path: "/usr/local/bin/mcp-calculator"
      transport: "stdio"
```

### 2. Configure Security Policies

Create `config/security_policies.yaml`:

```yaml
policies:
  - name: "prevent_data_exfiltration"
    enabled: true
    rules:
      - name: "block_sensitive_network"
        condition: "tool_category == 'network' and context.has_data_label('sensitive')"
        action: "deny"
        reason: "Cannot send sensitive data over network"
        priority: 100
```

### 3. Define Agent Roles

Create `config/agent_roles.yaml`:

```yaml
roles:
  analyst:
    description: "Data analyst with read-only access"
    permissions:
      - "read:database"
      - "execute:calculations"
    allowed_mcp_categories:
      - "data"
      - "computation"
    risk_tolerance: "low"
```

### 4. Initialize Selection Engine

```python
from tools.mcp_selection_engine import MCPSelectionEngine
import yaml

# Load configuration
with open('config/mcp_registry.yaml') as f:
    config = yaml.safe_load(f)

# Initialize engine
engine = MCPSelectionEngine(use_embeddings=False)
engine.load_registry_from_config(config)

# Select MCPs for agent
selected_mcps = await engine.select_mcps_for_agent(
    system_prompt="""
    You are a data analyst. You can:
    - Query databases
    - Perform calculations
    - Create visualizations
    """,
    agent_role="analyst",
    agent_permissions={"read:database", "execute:calculations"},
    max_mcps=5
)

print(f"Selected MCPs: {selected_mcps}")
# Output: Selected MCPs: ['calculator', 'database', 'visualization']
```

### 5. Enable Dynamic MCP Selection (NEW!)

**Dynamic selection** allows MCPs to be hot-loaded during conversation based on user queries:

```python
# Create session to track loaded MCPs
session = engine.create_session(
    agent_id="analyst-001",
    session_id="sess-123",
    baseline_mcps=selected_mcps  # MCPs from step 4
)

# Later, during conversation...
user_query = "What's the weather in New York?"

# Dynamically select and load MCPs based on query
new_mcps = await engine.auto_select_for_query(
    user_query=user_query,
    session_id="sess-123",
    agent_permissions={"read:database", "execute:calculations", "read:api"},
    auto_load=True  # Automatically load selected MCPs
)

print(f"Dynamically loaded: {new_mcps}")
# Output: Dynamically loaded: ['weather']

print(f"Total MCPs now: {session.loaded_mcps}")
# Output: Total MCPs now: {'calculator', 'database', 'visualization', 'weather'}
```

**Key Benefits:**
- 🚀 **Hot-loading**: Load MCPs during conversation without restart
- 🎯 **Contextual**: Only loads MCPs relevant to user's question
- 🔒 **Secure**: Still respects permissions and security policies
- 💾 **Efficient**: Doesn't load all MCPs upfront

See [mcp-dynamic-selection.md](mcp-dynamic-selection.md) for detailed documentation.

### 6. Use Security Middleware

```python
from security.policy_engine import PolicyEngine, SecurityContext
from security.input_validator import InputValidator

# Initialize security components
policy_engine = PolicyEngine()
input_validator = InputValidator()

# Create security context
context = SecurityContext(
    agent_id="analyst-001",
    agent_role="analyst",
    session_id="sess-123",
    user_id="user-456",
    permissions={"read:database", "execute:calculations"},
    data_labels=set(),
    environment="production",
    rate_limits={}
)

# Validate input
validation_result = input_validator.validate_arguments(
    tool_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "maxLength": 1000}
        },
        "required": ["query"]
    },
    arguments={"query": "SELECT * FROM users"}
)

if not validation_result.is_valid:
    print(f"Validation errors: {validation_result.errors}")

# Evaluate security policy
decision = await policy_engine.evaluate(
    context=context,
    tool_name="database_query",
    tool_category="database",
    tool_permissions=["read:database"],
    tool_risk_level="medium",
    arguments={"query": "SELECT * FROM users"}
)

if decision.action == "deny":
    raise PermissionError(decision.reason)
elif decision.action == "require_approval":
    # Request human approval
    print(f"Approval required: {decision.reason}")
```

## Key Features

### 1. Intelligent MCP Selection

The selection engine uses multiple strategies to match MCPs with agents:

- **Keyword Matching**: Extracts capabilities from system prompt
- **Semantic Similarity**: Uses embeddings for deep matching (optional)
- **Role-Based Filtering**: Respects agent role permissions
- **Risk-Based Ranking**: Prefers lower-risk MCPs

### 2. Security Policies

Policies support flexible conditions:

```python
# Check permissions
"context.has_permission('write:database')"

# Check data labels
"context.has_data_label('sensitive')"

# Check environment
"context.environment == 'production'"

# Check tool properties
"tool_risk_level == 'high'"
"tool_category in ['network', 'communication']"

# Check arguments
"'DROP TABLE' in str(arguments).upper()"
```

### 3. Input Validation

Protects against:

- SQL injection
- Command injection
- Path traversal
- XSS attacks
- Type mismatches
- Schema violations

### 4. Audit Trail

All MCP operations are logged with:

- Timestamp and duration
- Agent ID and role
- Tool name and arguments
- Policy decisions
- Success/failure status
- Error messages

## Example: Complete Integration

```python
import asyncio
import yaml
from tools.mcp_selection_engine import MCPSelectionEngine
from security.policy_engine import PolicyEngine, SecurityContext
from security.input_validator import InputValidator

async def main():
    # 1. Load configuration
    with open('config/mcp_registry.yaml') as f:
        mcp_config = yaml.safe_load(f)

    with open('config/security_policies.yaml') as f:
        policy_config = yaml.safe_load(f)

    # 2. Initialize components
    selection_engine = MCPSelectionEngine()
    selection_engine.load_registry_from_config(mcp_config)

    policy_engine = PolicyEngine()
    policy_engine.load_policies_from_config(policy_config)

    input_validator = InputValidator()

    # 3. Create security context
    context = SecurityContext(
        agent_id="analyst-001",
        agent_role="analyst",
        session_id="sess-123",
        user_id=None,
        permissions={"read:database", "execute:calculations"},
        data_labels=set(),
        environment="production",
        rate_limits={}
    )

    # 4. Select baseline MCPs from system prompt
    baseline_mcps = await selection_engine.select_mcps_for_agent(
        system_prompt="""
        You are a financial analyst. You analyze market data,
        perform statistical calculations, and create reports.
        """,
        agent_role="analyst",
        agent_permissions=context.permissions,
        max_mcps=5
    )

    print(f"Baseline MCPs: {baseline_mcps}")
    # Output: ['calculator', 'database', 'visualization']

    # 4b. Create session for dynamic loading
    session = selection_engine.create_session(
        agent_id="analyst-001",
        session_id="sess-123",
        baseline_mcps=baseline_mcps
    )

    # 4c. Simulate user asking for weather (not in baseline)
    user_query = "What's the weather forecast for tomorrow?"

    # Dynamically select and load weather MCP
    new_mcps = await selection_engine.auto_select_for_query(
        user_query=user_query,
        session_id="sess-123",
        agent_permissions=context.permissions | {"read:api"},  # Add API permission
        auto_load=True
    )

    print(f"Dynamically loaded: {new_mcps}")
    # Output: ['weather']

    # 5. Execute tool with security checks
    tool_name = "calculator_mean"
    tool_metadata = selection_engine.get_mcp_metadata("calculator")

    # Validate input
    validation = input_validator.validate_arguments(
        tool_schema={
            "type": "object",
            "properties": {
                "values": {"type": "array", "items": {"type": "number"}}
            },
            "required": ["values"]
        },
        arguments={"values": [1, 2, 3, 4, 5]}
    )

    if not validation.is_valid:
        print(f"Validation failed: {validation.errors}")
        return

    # Check policy
    decision = await policy_engine.evaluate(
        context=context,
        tool_name=tool_name,
        tool_category="computation",
        tool_permissions=[],
        tool_risk_level="low",
        arguments={"values": [1, 2, 3, 4, 5]}
    )

    if decision.action.value == "allow":
        print("Tool execution allowed")
        # Execute tool here...
    elif decision.action.value == "deny":
        print(f"Tool execution denied: {decision.reason}")
    else:
        print(f"Approval required: {decision.reason}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration Tips

### MCP Registry

- **Description**: Clear, searchable description of capabilities
- **Categories**: Broad groupings (data, computation, communication)
- **Capabilities**: Specific features (sql, math, email)
- **Risk Level**: Conservative assessment (prefer "high" if uncertain)

### Security Policies

- **Priority**: Higher priority rules evaluated first (100 = highest)
- **Conditions**: Keep simple, avoid complex logic
- **Actions**: Use "deny" for hard blocks, "require_approval" for review

### Agent Roles

- **Permissions**: Follow principle of least privilege
- **Categories**: Whitelist only necessary categories
- **Risk Tolerance**: Match to role responsibilities

## Testing

```python
# Test MCP selection
async def test_selection():
    engine = MCPSelectionEngine()
    # ... load config ...

    selected = await engine.select_mcps_for_agent(
        system_prompt="I need to calculate statistics",
        agent_role="analyst",
        agent_permissions={"execute:calculations"},
        max_mcps=3
    )

    assert "calculator" in selected

# Test security policy
async def test_policy():
    policy_engine = PolicyEngine()
    context = SecurityContext(
        agent_id="test",
        agent_role="analyst",
        permissions={"read:database"},
        data_labels={"sensitive"},
        # ...
    )

    decision = await policy_engine.evaluate(
        context=context,
        tool_name="send_email",
        tool_category="communication",
        tool_permissions=[],
        tool_risk_level="high",
        arguments={"to": "external@example.com"}
    )

    assert decision.action == PolicyAction.DENY
```

## Troubleshooting

### No MCPs Selected

- Check agent permissions match MCP requirements
- Verify system prompt contains relevant keywords
- Review MCP descriptions and capabilities

### Policy Always Denies

- Check policy priority order
- Verify condition syntax
- Test conditions in isolation

### Validation Errors

- Review JSON schema definitions
- Check for special characters in inputs
- Verify data types match schema

## Next Steps

1. Review [full design document](mcp-security-layer-design.md)
2. Customize policies for your use case
3. Add audit logging implementation
4. Implement authentication manager
5. Add metrics and monitoring

## Support

For issues or questions:
- Check the [design document](mcp-security-layer-design.md)
- Review configuration examples
- Enable debug logging: `logging.basicConfig(level=logging.DEBUG)`
