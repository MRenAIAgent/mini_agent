<!--
Sync Impact Report:
- Version change: New constitution (no previous version) → 1.0.0
- Added sections: Core Principles, Architecture Requirements, Development Standards, Governance
- New principles:
  1. Simplified Design
  2. Python Design Principles
  3. Test-Driven Development (NON-NEGOTIABLE)
  4. Performance & Accuracy
  5. Ease of Use
- Templates requiring updates:
  ✅ plan-template.md - Updated Constitution Check section with specific principle checkboxes
  ✅ tasks-template.md - Added constitutional compliance references for TDD, linting, performance targets
  ✅ spec-template.md - No changes needed (business-focused, no technical implementation details)
  ✅ agent-file-template.md - No changes needed (auto-generated structure template)
- Follow-up TODOs: None - All templates aligned with constitution v1.0.0
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
- Performance benchmarks for critical paths
- Mock-based testing for external dependencies
- Regression tests for bug fixes

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

**Version**: 1.0.0 | **Ratified**: 2025-09-20 | **Last Amended**: 2025-09-20