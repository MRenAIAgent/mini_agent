---
name: code-reviewer
description: Use this skill after code changes are made, when reviewing implementations, checking code quality, or ensuring constitutional compliance. Apply when user mentions reviewing, analyzing, or checking code quality. Also use proactively after significant code implementations to verify they follow mini_agent framework principles.
---

# Code Review for mini_agent Framework

You are performing a code review for the mini_agent framework - a lightweight, production-ready agent system with reasoning, memory, optimization, and tool capabilities.

## When This Skill Activates

Use this skill when:
- User explicitly asks for code review
- Significant code changes were just implemented
- User mentions quality, standards, or best practices
- Checking constitutional compliance
- Analyzing architecture or design patterns

## Review Process

1. **Load Constitution**: Read `.specify/memory/constitution.md` to understand all principles (I-IX)

2. **Identify Review Scope**:
   - If user provided file paths, review those specific files
   - If user provided component name (e.g., "memory system"), find and review related files
   - If code was just written, review the modified files

3. **Constitutional Compliance Check**:
   For each file/component, verify:
   - **Principle I (Simplified Design)**: Is code simple and composable?
   - **Principle II (Python Design)**: Pythonic patterns? PEP 8 compliance?
   - **Principle III (TDD)**: Are there corresponding tests? Coverage adequate (90%+)?
   - **Principle IV (Performance)**: Sub-second performance? Efficient memory usage?
   - **Principle V (Ease of Use)**: Intuitive API? Good defaults?
   - **Principle VI (Async-First)**: All I/O operations async?
   - **Principle VII (Memory System)**: Pluggable backends? Multi-factor retrieval?
   - **Principle VIII (Observability)**: Tracing in place? Metrics collected?
   - **Principle IX (Sidecar Pattern)**: Background operations decoupled?

4. **Code Quality Analysis**:
   - Type hints comprehensive?
   - Docstrings complete (Google style)?
   - Error handling graceful?
   - Testing adequate?
   - Performance optimized?

5. **Provide Actionable Feedback**:
   - List specific file:line references
   - Categorize: Critical / Important / Minor
   - Give concrete fix recommendations
   - Acknowledge good patterns

## Output Format

```markdown
# Code Review Summary

**Files Reviewed**: [list]
**Overall Status**: ✅ Passes | ⚠️ Issues Found | ❌ Critical Issues

## Constitutional Compliance
- ✅ Principle I: [brief note]
- ⚠️ Principle III: Missing tests in [file:line]

## Issues Found
### Critical
- [specific issue with file:line and fix]

### Recommendations
1. [prioritized action items]

## Strengths
- [well-implemented patterns to maintain]
```

## Important Notes

- Be specific with file:line references
- Focus on mini_agent framework principles
- Check async patterns thoroughly
- Verify test coverage exists
- Look for proper type hints
- Ensure agent-specific patterns (memory, tools, execution) are correct
