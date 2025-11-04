# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All endpoints implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 3.1: Setup
- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize [language] project with [framework] dependencies
- [ ] T003 [P] Configure linting and formatting tools (ruff, black, isort, mypy per Constitution)

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation (Constitution Principle III - NON-NEGOTIABLE)**
- [ ] T004 [P] Contract test POST /api/users in tests/contract/test_users_post.py
- [ ] T005 [P] Contract test GET /api/users/{id} in tests/contract/test_users_get.py
- [ ] T006 [P] Integration test user registration in tests/integration/test_registration.py
- [ ] T007 [P] Integration test auth flow in tests/integration/test_auth.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T008 [P] User model in src/models/user.py
- [ ] T009 [P] UserService CRUD in src/services/user_service.py
- [ ] T010 [P] CLI --create-user in src/cli/user_commands.py
- [ ] T011 POST /api/users endpoint
- [ ] T012 GET /api/users/{id} endpoint
- [ ] T013 Input validation
- [ ] T014 Error handling and logging

## Phase 3.4: Integration
- [ ] T015 Connect UserService to DB
- [ ] T016 Auth middleware
- [ ] T017 Request/response logging
- [ ] T018 CORS and security headers

## Phase 3.5: Polish
- [ ] T019 [P] Unit tests for validation in tests/unit/test_validation.py (target 90% coverage per Constitution)
- [ ] T020 Performance tests (sub-second response per Constitution Principle IV)
- [ ] T021 [P] Update docs/api.md with working examples (Constitution Principle V)
- [ ] T022 Remove duplication and improve code readability (Constitution Principle I)
- [ ] T023 Run manual-testing.md and verify intuitive API usage

## Dependencies
- Tests (T004-T007) before implementation (T008-T014)
- T008 blocks T009, T015
- T016 blocks T018
- Implementation before polish (T019-T023)

## Parallel Example
```
# Launch T004-T007 together:
Task: "Contract test POST /api/users in tests/contract/test_users_post.py"
Task: "Contract test GET /api/users/{id} in tests/contract/test_users_get.py"
Task: "Integration test registration in tests/integration/test_registration.py"
Task: "Integration test auth in tests/integration/test_auth.py"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- Avoid: vague tasks, same file conflicts

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - Each contract file → contract test task [P]
   - Each endpoint → implementation task
   
2. **From Data Model**:
   - Each entity → model creation task [P]
   - Relationships → service layer tasks
   
3. **From User Stories**:
   - Each story → integration test [P]
   - Quickstart scenarios → validation tasks

4. **Ordering**:
   - Setup → Tests → Models → Services → Endpoints → Polish
   - Dependencies block parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [ ] All contracts have corresponding tests
- [ ] All entities have model tasks
- [ ] All tests come before implementation
- [ ] Parallel tasks truly independent
- [ ] Each task specifies exact file path
- [ ] No task modifies same file as another [P] task

## Agent Framework Specific Task Patterns
*Use when building AI agent features (execution, memory, tools, optimization)*

### Setup Tasks for Agent Components
- Mock LLM provider setup for testing (Constitution Principle III)
- In-memory backend initialization (fast tests)
- Async test fixtures configuration (Constitution Principle VI)

### Testing Patterns for Agents
- **Mock LLM responses**: Create deterministic test cases
- **Memory backend tests**: Test with in-memory, verify pluggability (Constitution Principle VII)
- **Execution pattern tests**: Test ReAct, Chain of Thought, Plan & Execute patterns
- **Sidecar timeout tests**: Verify non-blocking execution and timeout handling (Constitution Principle IX)
- **Tool execution tests**: Mock external tools, test error handling
- **Performance benchmarks**: Agent execution time, memory retrieval speed (Constitution Principle IV)

### Core Implementation for Agent Features
- **Async operations**: All LLM calls, DB access, tool execution async (Constitution Principle VI)
- **Memory operations**: Support similarity + importance + recency ranking (Constitution Principle VII)
- **Tracing hooks**: Add @trace_agent_execution decorators (Constitution Principle VIII)
- **Sidecar registration**: Background ops moved to sidecars (Constitution Principle IX)
- **Provider abstraction**: LLM/memory/tool providers pluggable

### Integration Tasks for Agent Systems
- **Memory backend integration**: Connect Redis/Memgraph with fallback
- **LLM provider integration**: Support OpenAI, Anthropic, local models
- **MCP server integration**: Tool protocol implementation
- **Observability setup**: Rich console tracing configuration

### Polish Tasks for Agent Components
- **Coverage verification**: 90%+ with agent-specific mocking patterns
- **Performance validation**: Sub-second simple queries, benchmark complex reasoning
- **Sidecar metrics**: Verify performance improvements from background execution
- **Example agent creation**: Working examples in docs/ with real use cases
- **Error message clarity**: Test failure modes, ensure actionable errors

### Example Agent Feature Tasks
```
## Setup
- [ ] T001 Create mock LLM provider for deterministic testing
- [ ] T002 [P] Configure async test fixtures with pytest-asyncio
- [ ] T003 [P] Initialize in-memory backend for fast tests

## Tests First (TDD)
- [ ] T004 [P] Test ReAct execution pattern in tests/unit/test_react_pattern.py
- [ ] T005 [P] Test memory retrieval ranking in tests/unit/test_memory_retrieval.py
- [ ] T006 [P] Test sidecar timeout handling in tests/unit/test_sidecar_timeout.py

## Core Implementation
- [ ] T007 Implement async execution pattern base class
- [ ] T008 [P] Add @trace_agent_execution decorators
- [ ] T009 Memory ranking: similarity + importance + recency

## Integration
- [ ] T010 Connect memory backend with fallback logic
- [ ] T011 Register memory storage sidecar

## Polish
- [ ] T012 [P] Performance benchmark: execution under 1s
- [ ] T013 [P] Example: Create working agent with memory and tools
```