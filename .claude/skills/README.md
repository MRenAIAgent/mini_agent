# Skills Setup Guide

## What You Have vs What You Need

### Current Setup (Slash Commands)
```
.claude/commands/           ← Manual invocation only
├── plan.md                 ← Must type: /plan
├── review-code.md          ← Must type: /review-code
└── ...
```

### Skills (Auto-Invoked)
```
.claude/skills/             ← Automatic invocation
├── code-reviewer/
│   └── SKILL.md           ← Claude uses automatically
└── planner/
    └── SKILL.md           ← Claude uses when planning
```

## Key Principles for Auto-Invocation

### 1. The Description is CRITICAL

**Bad description** (won't trigger):
```yaml
description: Review code for quality
```

**Good description** (will trigger):
```yaml
description: Use this skill after code changes are made, when reviewing implementations, checking code quality, or ensuring constitutional compliance. Apply when user mentions reviewing, analyzing, or checking code. Also use proactively after significant implementations.
```

The description must include:
- ✅ WHAT the skill does
- ✅ WHEN to use it (triggers/keywords)
- ✅ Optional: "Use proactively" for automatic application

### 2. Include Keywords Users Might Say

Match how users naturally speak:
- "review" → code review skill
- "plan" → planning skill
- "test" → testing skill
- "optimize" → optimization skill
- "security" → security analysis skill

### 3. Structure Template

```markdown
---
name: skill-name
description: Use when [context]. Apply when user mentions [keywords]. Use proactively after [events].
---

# Skill Title

## When This Skill Activates
[Clear list of triggers]

## What This Skill Does
[Detailed instructions]

## Output Format
[Expected results]
```

## Converting Your Commands to Skills

### Example: plan.md → planner skill

```bash
mkdir -p .claude/skills/planner
```

Create `.claude/skills/planner/SKILL.md`:
```markdown
---
name: planner
description: Use when planning feature implementations, creating design artifacts, or structuring complex development tasks. Apply when user mentions planning, designing, or architecting new features. Use proactively when user describes a new feature to implement.
---

[Your plan.md content]
```

### Example: implement.md → implementation-executor skill

```bash
mkdir -p .claude/skills/implementation-executor
```

Create `.claude/skills/implementation-executor/SKILL.md`:
```markdown
---
name: implementation-executor
description: Use when executing implementation plans or working through tasks.md. Apply when user says "implement", "build", or "execute the plan". Use proactively after planning phase completes.
---

[Your implement.md content]
```

## What Should Be a Skill vs Command?

### Make it a SKILL if:
- ✅ You want Claude to use it automatically
- ✅ It applies to common development activities
- ✅ It's a pattern/standard to follow
- ✅ It's domain expertise (framework-specific knowledge)

Examples:
- Code review standards
- Testing patterns
- Security best practices
- Framework-specific patterns (mini_agent principles)
- Architecture patterns

### Keep it a COMMAND if:
- ✅ You want explicit control
- ✅ It requires specific user input/arguments
- ✅ It's a workflow that shouldn't trigger automatically
- ✅ It's a one-time setup task

Examples:
- `/commit` - you control when to commit
- `/pr` - you control when to create PR
- `/specify <details>` - requires specific input
- `/setup-project` - one-time operation

## Testing Your Skills

After creating a skill:

1. **Start a new conversation** (or reload Claude Code)
2. **Use natural language** that matches your description:
   - "Can you review this code?" → triggers code-reviewer
   - "I need to plan this feature" → triggers planner
   - "Let's implement the auth system" → triggers implementation-executor

3. **Check if Claude mentions the skill**:
   ```
   "I'm going to use the code-reviewer skill to analyze this..."
   ```

## Troubleshooting

### Skill not being used?

1. **Check description triggers**: Does it match how you speak?
2. **Be more specific**: Add more trigger keywords
3. **Add "Use proactively"**: Tells Claude to use it without being asked
4. **Check file location**: Must be `.claude/skills/name/SKILL.md`
5. **Restart**: Sometimes need to reload Claude Code

### Skill used too often?

1. **Narrow the description**: Be more specific about when to use
2. **Remove "proactively" keyword**: Only use on request
3. **Add constraints**: "Only when user explicitly asks..."

## Quick Migration Checklist

- [ ] Create `.claude/skills/` directory
- [ ] For each command you want auto-invoked:
  - [ ] Create skill directory: `mkdir -p .claude/skills/skill-name`
  - [ ] Create `SKILL.md` with name + description frontmatter
  - [ ] Write trigger-rich description
  - [ ] Copy command content
  - [ ] Test with natural language
- [ ] Keep original commands in `.claude/commands/` for manual use

## Example: Your Current Commands

Based on your commands, suggested skills:

1. **code-reviewer** ✅ (already created)
   - Triggers: "review", "check code", "quality"

2. **planner**
   - Triggers: "plan", "design", "architecture"

3. **implementation-executor**
   - Triggers: "implement", "build", "execute plan"

4. **spec-writer**
   - Triggers: "specify", "requirements", "feature spec"

5. **task-generator**
   - Triggers: "create tasks", "break down", "task list"

Keep `/constitution` as a command (one-time setup).
