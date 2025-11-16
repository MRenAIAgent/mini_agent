# Skills vs Agents: How They Work Together

## Quick Comparison

| Feature | Skills | Agents |
|---------|--------|--------|
| **Execution** | Main conversation | Separate subprocess |
| **Context** | Shared with user chat | Independent context |
| **Purpose** | Guide Claude's behavior | Autonomous task execution |
| **Duration** | Active for rest of conversation | One-time execution |
| **Communication** | Bidirectional (chat continues) | One-way (final report only) |
| **Use Case** | Patterns, standards, expertise | Complex multi-step research |

## Architecture Diagram

```
┌─────────────────────────────────────────────┐
│          Main Conversation (You + Claude)    │
├─────────────────────────────────────────────┤
│                                              │
│  ┌──────────────┐      ┌─────────────────┐ │
│  │   Skill      │      │   Agent         │ │
│  │  (In-line)   │      │  (Subprocess)   │ │
│  └──────────────┘      └─────────────────┘ │
│        │                       │            │
│        ↓                       ↓            │
│  Loads prompt              Spawns new       │
│  into current              process with     │
│  conversation              own context      │
│        │                       │            │
│        ↓                       ↓            │
│  Claude follows            Agent works      │
│  instructions              autonomously     │
│  immediately                   │            │
│                                ↓            │
│                           Returns final     │
│                           report only       │
└─────────────────────────────────────────────┘
```

## When to Use Each

### Use a SKILL when:
✅ You want to enforce patterns/standards
✅ You want to guide Claude's behavior consistently
✅ The task is part of normal conversation flow
✅ You need domain expertise applied to various tasks
✅ You want to customize how Claude works

**Examples:**
- Code review standards (constitutional compliance)
- Testing patterns (TDD, coverage requirements)
- Security best practices (OWASP checks)
- Framework-specific knowledge (mini_agent principles)
- Documentation standards
- Commit message formats

### Use an AGENT when:
✅ Task requires extensive searching/exploration
✅ Multi-step research across many files
✅ You want autonomous task completion
✅ Task might take many iterations to complete
✅ You want to save main conversation context

**Examples:**
- "Find all authentication patterns in the codebase" → Explore agent
- "Search for performance bottlenecks" → general-purpose agent
- "Analyze the entire memory system architecture" → Explore agent
- "Research how error handling works across modules" → Explore agent

## They're Complementary!

**Skills guide Agents:**
When an agent is launched, it can also have access to skills! So your code-reviewer skill can be used by an agent during autonomous work.

**Example Combined Flow:**

```
User: "Review all memory-related code"
↓
Claude launches: Explore agent to find all memory files
↓
Agent finds: memory/, memory_manager.py, etc.
↓
Agent returns: List of files
↓
Claude uses: code-reviewer skill (in main conversation)
↓
Reviews each file following skill instructions
```

## Independence

**Yes, they are independent:**

1. **Skills don't require agents** - Work perfectly in main conversation
2. **Agents don't require skills** - Can work with default behavior
3. **Different activation** - Skills via description matching, Agents via Task tool
4. **Different storage** - Skills in `.claude/skills/`, Agents are built-in

## Your Current Setup

### Skills (Local)
```
.claude/skills/
├── code-reviewer/SKILL.md    ← Auto code review
└── planner/SKILL.md          ← Auto planning
```

### Agents (Built-in)
- Explore - Codebase exploration
- Plan - Planning tasks
- general-purpose - Multi-step tasks

## Creating vs Using

### Skills
**Create**: Add `.claude/skills/name/SKILL.md` files
**Use**: Claude auto-invokes based on description
**Customize**: Fully under your control

### Agents
**Create**: Cannot create custom agents (built-in only)
**Use**: Claude uses Task tool when needed
**Customize**: Cannot modify agent behavior

## Pro Tips

### 1. Skill + Agent Combo
```markdown
---
name: security-auditor
description: Use when auditing security. First use Explore agent to find security-sensitive code, then analyze using security best practices.
---

When auditing security:
1. Ask: Should I use Explore agent to find all auth/security code?
2. Then: Review each file for OWASP vulnerabilities
3. Check: SQL injection, XSS, command injection, etc.
```

### 2. Skill References Agent Results
```markdown
---
name: architecture-reviewer
description: Use when reviewing architecture. Reference Explore agent findings to understand component relationships.
---

When reviewing architecture:
1. If codebase structure unclear, suggest using Explore agent
2. Once files identified, check for proper separation of concerns
3. Verify dependency injection patterns
```

### 3. Let Claude Decide
You don't need to manually invoke agents or skills - Claude will:
- Use skills when description matches
- Launch agents when task requires autonomous work
- Combine them when beneficial

## Testing the Difference

### Test Skill (In-conversation):
```
You: "Review the memory_manager.py file"
Claude: *Uses code-reviewer skill*
        *Reads file*
        *Applies skill instructions*
        *Responds with review in same conversation*
```

### Test Agent (Subprocess):
```
You: "Find all places where we handle errors"
Claude: *Launches Explore agent*
        Agent: [Working autonomously...]
        Agent: [Searching files...]
        Agent: [Found 15 locations]
        *Agent returns report*
Claude: "The agent found error handling in..."
```

## Key Insight

**Skills = How Claude works**
**Agents = What Claude delegates**

Skills modify Claude's behavior in the conversation.
Agents are helpers Claude can call for complex subtasks.

Both make Claude more powerful, but in different ways!
