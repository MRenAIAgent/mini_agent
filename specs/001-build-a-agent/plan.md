
# Implementation Plan: Enhanced Agent Framework (Refactoring)

**Branch**: `001-build-a-agent` | **Date**: 2025-09-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/Users/minren/code/mini_agent/specs/001-build-a-agent/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Refactor and enhance existing agent framework to implement ReAct, planning-execution, auto and simple execution modes. Integrate LiteLLM for unified LLM proxy, add streaming support, redesign system prompt structure. Extend tool/MCP integration for easy extensibility. Upgrade memory system with Memgraph and Redis for knowledge graph and semantic/BM25 search. Implement human-like memory with temporal awareness and extensible algorithms. Apply TDD throughout with comprehensive testing. Add in-context learning and prompt optimization with dynamic examples. Integrate popular agent benchmarks for performance comparison against LangChain/LangGraph.

## Technical Context
**Language/Version**: Python 3.11+ (existing codebase upgrade)
**Primary Dependencies**: LiteLLM (unified LLM proxy), asyncio, pydantic, streaming libs
**Storage**: Memgraph (knowledge graph), Redis (cache/search), existing memory interfaces
**Testing**: pytest, pytest-asyncio, coverage, TDD enforcement, benchmark suites
**Target Platform**: Cross-platform Python (Linux, macOS, Windows)
**Project Type**: single - agent framework library (refactoring existing)
**Performance Goals**: Sub-second response for simple tasks, streaming support, <200ms memory retrieval
**Constraints**: Maintain backward compatibility where possible, <100MB memory baseline
**Scale/Scope**: Extensible architecture, benchmark against LangChain/LangGraph, support multiple execution patterns

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Simplified Design (Principle I)
- [x] Feature is broken into simple, composable parts (modular execution patterns, pluggable memory backends)
- [x] No unnecessary complexity introduced (refactor existing complex parts)
- [x] Code readability prioritized over clever optimizations (existing code review + refactoring)
- [x] Clear justification for any complexity (knowledge graph for human-like memory, benchmarking for validation)

### Python Design Principles (Principle II)
- [x] Follows Pythonic patterns and Zen of Python (async/await, protocols, type hints)
- [x] PEP 8 compliance planned (existing linting + ruff/black enforcement)
- [x] Duck typing and protocols preferred over rigid inheritance (existing Protocol interfaces)
- [x] Explicit interfaces over implicit behavior (LiteLLM, tool protocols, memory interfaces)

### Test-Driven Development (Principle III) - NON-NEGOTIABLE
- [x] TDD approach planned (Red-Green-Refactor for all new features and refactoring)
- [x] Tests written before implementation in Phase 1 (contract tests, benchmark tests)
- [x] 90% code coverage target set (existing coverage + new components)
- [x] Contract tests and integration tests planned (LiteLLM, Memgraph, Redis, benchmarks)

### Performance & Accuracy (Principle IV)
- [x] Sub-second response time targets defined (simple mode, streaming responses)
- [x] Memory usage optimization planned (<100MB baseline, efficient graph operations)
- [x] LLM token optimization considered (LiteLLM proxy, prompt optimization, context compression)
- [x] Performance benchmarks included (LangChain/LangGraph comparison suite)

### Ease of Use (Principle V)
- [x] API design is intuitive with minimal configuration (maintain existing API + improvements)
- [x] Sensible defaults planned (auto execution mode selection, default backends)
- [x] Clear error messages designed (structured error handling improvements)
- [x] Working examples included in documentation (existing quickstart + benchmark examples)

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: Option 1 (Single project) - Existing agent framework structure maintained and enhanced

## Phase 0: Outline & Research
1. **Review existing research.md** - already contains comprehensive technical decisions
2. **Update research gaps** for new requirements:
   - Current implementation analysis and refactoring plan
   - LiteLLM integration specifics for streaming
   - Benchmark suite selection (existing frameworks comparison)
   - System prompt engineering patterns
   - In-context learning implementation approach

3. **Current research status**: ✅ Existing research.md covers:
   - LiteLLM integration strategy
   - Execution patterns (ReAct, Planning, Auto, Simple)
   - Memory architecture (Memgraph + Redis)
   - Tool/MCP integration design
   - Streaming and performance optimization
   - Human-like memory simulation
   - Testing strategy

**Output**: Updated research.md with refactoring analysis and implementation gaps filled

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Review and update existing data-model.md**:
   - ✅ Entities already defined for agent, memory, tools, execution patterns
   - Add LiteLLM integration entities (provider configs, streaming state)
   - Add benchmark entities (test suites, comparison results)
   - Update memory entities for Memgraph/Redis backends

2. **Review and update existing API contracts**:
   - ✅ Existing contracts: agent_core_api.yaml, memory_system_api.yaml, tool_integration_api.yaml
   - Add streaming endpoints to agent core API
   - Add benchmark endpoints for framework comparison
   - Add LiteLLM configuration endpoints

3. **Update contract tests** for refactored components:
   - LiteLLM streaming integration tests
   - Benchmark comparison test scenarios
   - Memory backend switching tests (Memgraph/Redis)
   - Execution pattern enhancement tests

4. **Update test scenarios** from refactoring requirements:
   - Streaming response validation
   - Cross-framework benchmark scenarios
   - Memory system migration scenarios

5. **Update agent context file**:
   - Add LiteLLM, Memgraph, Redis dependencies
   - Update recent changes with refactoring scope
   - Add benchmark and streaming capabilities

**Output**: Updated data-model.md, enhanced /contracts/*, refactoring tests, updated quickstart.md, updated CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Reference `implementation-guide.md` for specific file modifications and dependencies
- Generate refactoring tasks from existing codebase analysis with specific file references:

**Core Refactoring Tasks** (Reference: implementation-guide.md Phase 1):
- LiteLLM integration → modify `agent.py:34` constructor, add `integrations/litellm_provider.py` [P]
- Streaming support → add `agent.py:run_stream()` method, modify `_enhanced_llm_call` [P]
- Execution patterns → extend `execution/execution_patterns.py` enum, add missing pattern classes [P]

**Memory Enhancement Tasks** (Reference: implementation-guide.md Phase 3):
- Memory backends → create `memory/backends/memgraph_backend.py`, `redis_backend.py` [P]
- Human-like memory → modify `memory/memory_manager.py` for temporal decay [P]

**New Component Tasks** (Reference: implementation-guide.md Phases 4-5):
- Benchmark suite → create `benchmarks/` module with framework comparison [P]
- In-context learning → create `learning/` module with example management [P]

**Testing Tasks** (Reference: implementation-guide.md Testing section):
- Contract tests for all enhanced APIs (refer to updated contracts/)
- Backward compatibility tests for existing functionality
- Integration tests for new backends and patterns

**Ordering Strategy**:
- **Critical Path**: LiteLLM integration → Streaming → Enhanced patterns → Memory backends → Benchmarks
- **TDD Order**: Contract tests (reference contracts/) → Unit tests → Implementation → Integration tests
- **Parallel Streams** (reference implementation-guide.md dependencies):
  - Stream A: LLM + Streaming (`agent.py`, `integrations/`)
  - Stream B: Memory backends (`memory/backends/`)
  - Stream C: Benchmarking (`benchmarks/` module)
  - Stream D: Execution patterns (`execution/` extensions)

**File-Specific Task Mapping**:
- `agent.py` modifications: 5-6 tasks (constructor, streaming, methods)
- New module creation: 8-10 tasks (backends, benchmarks, learning)
- API contract implementation: 6-8 tasks (refer to contracts/ for endpoints)
- Testing and validation: 8-10 tasks (compatibility, integration, benchmarks)

**Estimated Output**: 25-30 numbered, ordered tasks with specific file references (SIMPLIFIED per Constitution)

**Key Task Categories with File References** (CONSTITUTIONAL COMPLIANCE):
1. **Core Refactoring**: `agent.py` modifications only, simple LiteLLM integration
2. **Pattern Enhancement**: `execution/pattern_executor.py` extensions (no new files)
3. **Memory System**: `memory/backends/` for Memgraph/Redis, reuse existing interfaces
4. **Simple Benchmarking**: `agent.py` benchmark method (no new module)
5. **Simple Examples**: `agent.py` prompt enhancement, reuse memory system
6. **Testing**: Essential contract tests, compatibility validation

**Constitutional Compliance**:
- Simplified design: Extend existing files instead of creating new modules
- Minimal dependencies: Reuse existing infrastructure
- Clear justification: Each addition has specific user requirement

**Implementation Guide Reference**: All tasks should reference specific sections in `implementation-guide.md` for:
- Exact file paths and line numbers to modify
- Before/after code examples
- Integration points between components
- Backward compatibility requirements

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - Updated with refactoring analysis
- [x] Phase 1: Design complete (/plan command) - Enhanced data model and contracts
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS (all refactoring maintains constitutional compliance)
- [x] All NEEDS CLARIFICATION resolved (existing spec clarifications + refactoring decisions)
- [x] Complexity deviations documented (knowledge graph complexity justified, benchmarking adds necessary validation)

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
