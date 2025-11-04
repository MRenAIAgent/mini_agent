<!--
Sync Impact Report:
- Version change: 1.0.0 → 1.1.0 (MINOR: New principles added)
- Modified sections: Added "Agent Framework Principles" section
- New principles added:
  6. Async-First Architecture
  7. Memory System Design
  8. Observability & Tracing
  9. Sidecar Pattern for Non-Blocking Operations
- Modified sections:
  - Testing Requirements: Added agent-specific testing patterns
- Templates requiring updates:
  ✅ plan-template.md - Constitution Check updated with new agent framework principles
  ✅ tasks-template.md - Added references to async patterns, memory testing, sidecar testing
  ✅ spec-template.md - No changes needed (business-focused)
  ✅ agent-file-template.md - No changes needed (structure template)
  ✅ Added new command: review-code.md - Code review workflow
- Follow-up TODOs: None - All templates aligned with constitution v1.1.0
-->

# Core Agent System Constitution

## Core Principles

### I. Simplified Design
Every component MUST follow the principle of simplicity. Complex features MUST be broken down into simple, composable parts. No feature shall be added without clear justification and removal of unnecessary complexity. Code readability and maintainability take precedence over clever optimizations.

**Rationale**: Simplified design reduces bugs, improves maintainability, and makes the system accessible to more developers.

### II. Python Design Principles
All code MUST adhere to Python design patterns and the Zen of Python. This includes: explicit is better than implicit, simple is better than complex, flat is better than nested, readability counts. PEP 8 compliance is mandatory. Duck typing and protocol-based interfaces are preferred over rigid inheritance hierarchies.

**Rationale**: Following Python conventions ensures code is idiomatic, maintainable, and familiar to Python developers.

### III. Test-Driven Development (NON-NEGOTIABLE)
TDD is mandatory for all new features and bug fixes. Tests MUST be written before implementation. All code changes require accompanying tests. The testing cycle is: Red (write failing test) → Green (implement minimal solution) → Refactor (improve while keeping tests green). Minimum 90% code coverage required.

**Rationale**: TDD ensures robust, reliable code and prevents regression bugs while maintaining high code quality.

### IV. Performance & Accuracy
The system MUST prioritize both speed and correctness. Performance optimizations cannot sacrifice accuracy. All execution patterns MUST maintain sub-second response times for simple queries. Memory usage MUST be efficient with proper cleanup. LLM calls MUST be optimized to minimize tokens while maintaining output quality.

**Rationale**: Fast and accurate responses are essential for practical AI agent deployment and user satisfaction.

### V. Ease of Use
The public API MUST be intuitive and require minimal configuration for basic usage. Complex functionality MUST be accessible through simple interfaces with sensible defaults. Documentation MUST include working examples. Error messages MUST be clear and actionable.

**Rationale**: Easy-to-use interfaces accelerate adoption and reduce integration complexity for developers.

## Agent Framework Principles

### VI. Async-First Architecture
All I/O operations MUST be async (LLM calls, database access, tool execution). The framework MUST support high concurrency without blocking. Synchronous wrappers MAY be provided for convenience but MUST NOT be the primary interface. Agent lifecycle methods (start, run, stop) MUST be async.

**Rationale**: Async architecture enables scalable agent deployments that can handle multiple concurrent sessions without blocking, essential for production deployments with FastAPI, asyncio frameworks, and persistent agents.

### VII. Memory System Design
Memory MUST be pluggable with support for multiple backends (in-memory, Redis, Memgraph). Memory operations MUST support multiple memory types (episodic, semantic, user profile, interaction). Retrieval MUST use multi-factor ranking (similarity, importance, recency). Memory cleanup and lifecycle management MUST be automatic with configurable policies.

**Rationale**: Flexible memory architecture allows agents to scale from development (in-memory) to production (distributed backends) while maintaining consistent APIs. Multiple memory types enable sophisticated agent behavior and learning.

### VIII. Observability & Tracing
All critical operations MUST be traceable without external dependencies. Tracing MUST work locally with beautiful console output (Rich + StructLog). Performance metrics MUST be automatically collected (timing, token usage, iterations). Error context MUST include full execution state for debugging.

**Rationale**: Local-first observability enables rapid debugging without complex infrastructure. Rich console output provides immediate feedback during development. Automatic metrics collection supports optimization and monitoring.

### IX. Sidecar Pattern for Non-Blocking Operations
Operations that don't affect user-facing responses MUST use sidecars to run in background. Sidecars MUST have configurable timeouts and error handling. Memory storage, analytics, and logging SHOULD be implemented as sidecars. Response latency MUST prioritize user experience over background tasks.

**Rationale**: Sidecar pattern improves perceived performance by decoupling blocking operations from response generation, reducing response times by 100-200ms in typical deployments. Critical for production user experience.

## Architecture Requirements

All components MUST be:
- Modular and independently testable
- Async-first with proper concurrency handling
- Type-hinted with mypy compliance
- Interface-based with clear protocols
- Resource-efficient with proper lifecycle management

Integration points MUST support multiple backends with unified interfaces. Dependencies MUST be minimal and well-justified.

## Development Standards

### Code Quality
- All code MUST pass linting (ruff, black, isort)
- Type hints MUST be comprehensive (mypy --strict)
- Docstrings MUST follow Google style
- Functions MUST be pure when possible
- Side effects MUST be explicit and contained

### Testing Requirements
- Unit tests for all business logic
- Integration tests for component interactions
- Performance benchmarks for critical paths (agent execution, memory retrieval)
- Mock-based testing for external dependencies (LLM providers, memory backends)
- Regression tests for bug fixes
- Agent-specific patterns:
  - Mock LLM providers for deterministic testing
  - In-memory backends for fast test execution
  - Execution pattern testing (ReAct, Chain of Thought, etc.)
  - Sidecar execution and timeout testing
  - Memory retrieval accuracy and ranking tests

### Documentation Standards
- API documentation auto-generated from docstrings
- README with quick start examples
- Architecture decision records for significant changes
- Performance characteristics documented
- Migration guides for breaking changes

## Governance

### Amendment Process
Constitution changes require:
1. Documented proposal with rationale
2. Impact assessment on existing code
3. Template consistency review
4. Team approval for principle changes
5. Migration plan for breaking changes

### Compliance Review
All pull requests MUST verify constitutional compliance. Code reviews MUST check for adherence to core principles. Technical debt that violates principles MUST be prioritized for resolution.

### Versioning Policy
Constitution follows semantic versioning:
- MAJOR: Backward incompatible principle changes
- MINOR: New principles or expanded guidance
- PATCH: Clarifications and refinements

**Version**: 1.1.0 | **Ratified**: 2025-09-20 | **Last Amended**: 2025-11-04