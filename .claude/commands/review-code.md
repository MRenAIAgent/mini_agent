---
description: Review code for quality, constitutional compliance, and best practices specific to the agent framework.
---

You are performing a code review for the mini_agent framework - a lightweight, production-ready agent system with reasoning, memory, optimization, and tool capabilities.

## Project Context

**mini_agent** is an AI agent framework that provides:
- Multiple execution patterns (ReAct, Chain of Thought, Plan & Execute, Reflection, Socratic)
- Multi-backend memory system (in-memory, Redis, Memgraph) with multiple memory types
- Sidecar architecture for non-blocking background operations
- Tool/MCP integration for external capabilities
- Prompt optimization with multiple strategies
- Rich local observability and tracing
- Async-first architecture for high concurrency

## Review Execution Flow

1. **Load Constitution**: Read `.specify/memory/constitution.md` to understand all principles (I-IX)

2. **Identify Review Scope**:
   - If user provided file paths, review those specific files
   - If user provided component name (e.g., "memory system"), find and review related files
   - If no scope provided, perform high-level architecture review

3. **Constitutional Compliance Check**:
   For each file/component, verify:
   - **Principle I (Simplified Design)**: Is code simple and composable? Any unnecessary complexity?
   - **Principle II (Python Design)**: Pythonic patterns? PEP 8 compliance? Proper use of protocols/duck typing?
   - **Principle III (TDD)**: Are there corresponding tests? Coverage adequate (90%+)?
   - **Principle IV (Performance & Accuracy)**: Sub-second performance? Efficient memory usage?
   - **Principle V (Ease of Use)**: Intuitive API? Good defaults? Clear error messages?
   - **Principle VI (Async-First)**: All I/O operations async? Proper concurrency handling?
   - **Principle VII (Memory System)**: Pluggable backends? Multiple memory types? Multi-factor retrieval?
   - **Principle VIII (Observability)**: Tracing in place? Metrics collected? Good error context?
   - **Principle IX (Sidecar Pattern)**: Background operations decoupled? Timeout handling?

4. **Code Quality Analysis**:
   - **Type hints**: Comprehensive? mypy-strict compatible?
   - **Docstrings**: Google style? Complete?
   - **Error handling**: Graceful degradation? Clear error messages?
   - **Testing**: Unit, integration, contract tests present?
   - **Performance**: Any obvious bottlenecks? Proper resource cleanup?

5. **Architecture Patterns Review**:
   - **Dependency Injection**: Components accept dependencies in constructors?
   - **Interface-based Design**: Using protocols and abstract base classes?
   - **Plugin/Strategy Pattern**: Properly implemented for execution patterns, memory backends, tools?
   - **Session Management**: Thread-safe for multi-user deployments?
   - **Graceful Degradation**: Optional features don't break core functionality?

6. **Agent Framework Specifics**:
   - **LLM Integration**: Proper provider abstraction? Streaming support?
   - **Memory Operations**: Importance weighting? Recency tracking? Embeddings support?
   - **Tool Execution**: MCP protocol support? Proper timeout handling?
   - **Execution Patterns**: Pattern selection logic? Iteration limits?
   - **Sidecar Execution**: Concurrent execution? Statistics tracking?

7. **Generate Review Report**:
   ```markdown
   # Code Review Report

   **Scope**: [files/components reviewed]
   **Date**: [current date]

   ## Summary
   [High-level assessment - strengths and concerns]

   ## Constitutional Compliance
   ### ✅ Passing Principles
   - Principle [X]: [why it passes]

   ### ⚠️  Concerns
   - Principle [Y]: [specific issue and location]
     - **File**: [file:line]
     - **Issue**: [description]
     - **Recommendation**: [how to fix]

   ## Code Quality Issues
   ### Critical
   - [Issue description] in [file:line]
     - **Impact**: [why it matters]
     - **Fix**: [how to resolve]

   ### Minor
   - [Issue description] in [file:line]

   ## Architecture Observations
   - [Pattern usage, design decisions, potential improvements]

   ## Testing Gaps
   - [Missing tests, coverage gaps, edge cases not covered]

   ## Performance Notes
   - [Bottlenecks, optimization opportunities]

   ## Recommendations
   1. [Priority 1: Critical fixes]
   2. [Priority 2: Important improvements]
   3. [Priority 3: Nice-to-have enhancements]

   ## Positive Highlights
   - [Well-implemented patterns, good practices to maintain]
   ```

8. **Provide Actionable Next Steps**:
   - If critical issues found: List specific files and fixes needed
   - If minor issues: Suggest priority order for improvements
   - If all good: Acknowledge strengths and suggest potential enhancements

## Review Checklist

**Before completing review, ensure you've checked:**
- [ ] All 9 constitutional principles evaluated
- [ ] Type hints reviewed (mypy --strict compatibility)
- [ ] Tests exist and cover key paths (90%+ target)
- [ ] Async patterns properly used (no blocking I/O)
- [ ] Error handling is graceful and informative
- [ ] Public API is intuitive with good defaults
- [ ] Documentation is clear and includes examples
- [ ] Memory/resource cleanup is proper
- [ ] Performance meets requirements (<1s for simple queries)
- [ ] Agent-specific patterns correctly implemented

## Special Considerations for Agent Framework

When reviewing agent framework code, pay extra attention to:

1. **LLM Call Patterns**: Are prompts constructed efficiently? Token usage optimized?
2. **Memory Retrieval**: Is ranking using all factors (similarity + importance + recency)?
3. **Tool Execution**: Proper timeout and error handling for external tools?
4. **Execution Loops**: Protection against infinite loops? Max iteration limits?
5. **Sidecar Usage**: Are blocking operations properly moved to sidecars?
6. **Session Isolation**: Thread-safe for multiple concurrent users?
7. **Provider Abstraction**: Easy to swap LLM/memory/tool providers?
8. **Observability Hooks**: Tracing decorators in place for debugging?

## Example Usage

```
User: "Review the memory system"
Assistant: [Reviews memory/, memory_manager.py, and related files against all principles]

User: "Review memory/episodic_memory.py for constitutional compliance"
Assistant: [Focused review of that specific file]

User: "Check if the sidecar implementation follows best practices"
Assistant: [Reviews sidecars/ directory against Principle IX and architecture patterns]
```

## Output Format

Always provide:
1. Clear summary of compliance status
2. Specific file:line references for issues
3. Concrete recommendations for fixes
4. Acknowledgment of well-implemented patterns
5. Priority ordering for improvements

Do not:
- Make vague statements without file references
- Ignore constitutional principles
- Skip testing coverage analysis
- Overlook performance implications
- Forget agent-specific patterns

The review should be thorough, actionable, and grounded in the constitution and architectural patterns of the mini_agent framework.
