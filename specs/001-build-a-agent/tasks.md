# Tasks: Enhanced Agent Framework (Refactoring)

**Input**: Design documents from `/Users/minren/code/mini_agent/specs/001-build-a-agent/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/, implementation-guide.md

## Execution Flow (main)
```
1. Load plan.md from feature directory ✅
   → Extract: Python 3.11+, LiteLLM, Memgraph, Redis, asyncio, pydantic
   → Structure: Single project (existing codebase refactoring)
2. Load design documents ✅
   → data-model.md: Agent, ExecutionContext, MemoryEntry, LLMConfig entities
   → contracts/: agent_core_api.yaml, memory_system_api.yaml, tool_integration_api.yaml
   → research.md: Refactoring strategy, constitutional compliance
3. Generate tasks by category ✅
   → Setup: dependencies, linting, structure validation
   → Tests: contract tests for 3 APIs, integration tests
   → Core: LiteLLM integration, execution patterns, memory backends
   → Integration: streaming, benchmarking, examples
   → Polish: testing, documentation, validation
4. Apply task rules ✅
   → Different files = [P] for parallel execution
   → Same file modifications = sequential
   → Tests before implementation (TDD constitutional requirement)
5. Tasks numbered T001-T030 ✅
6. Constitutional compliance: simplified design, existing file extensions ✅
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- File paths relative to repository root

## Path Conventions
**Single project structure** (existing codebase):
- Core files: `agent.py`, `execution/`, `memory/`, `integrations/`, `tools/`
- New backends: `memory/backends/`
- Tests: `tests/contract/`, `tests/integration/`, `tests/unit/`

## Phase 3.1: Setup
- [x] T001 Validate existing project structure and constitutional compliance per plan.md
- [x] T002 Add LiteLLM dependencies to requirements (litellm>=1.0.0, memgraph>=1.0.0, redis>=4.0.0)
- [x] T003 [P] Update linting configuration for constitutional compliance (ruff, black, isort, mypy)

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation (Constitution Principle III - NON-NEGOTIABLE)**

- [ ] T004 [P] Create contract test for agent core API streaming endpoints in `tests/contract/test_agent_core_streaming.py`
- [ ] T005 [P] Create contract test for LLM provider configuration in `tests/contract/test_llm_config.py`
- [ ] T006 [P] Create contract test for benchmark endpoints in `tests/contract/test_benchmark_api.py`
- [ ] T007 [P] Create contract test for memory backend switching in `tests/contract/test_memory_backends.py`
- [ ] T008 [P] Create integration test for execution pattern switching in `tests/integration/test_execution_patterns.py`
- [ ] T009 [P] Create integration test for backward compatibility in `tests/integration/test_backward_compatibility.py`

## Phase 3.3: Core Implementation
**TDD GATE: All Phase 3.2 tests must exist and FAIL before proceeding**

### Core Agent Refactoring (Sequential - same file)
- [ ] T010 Refactor `agent.py` constructor to support LiteLLM config (line 34, maintain backward compatibility)
- [ ] T011 Add streaming support method `run_stream()` to `agent.py` (constitutional compliance: simple implementation)
- [ ] T012 Update `agent.py` `_enhanced_llm_call` method (line 385) to use LiteLLM

### Execution Pattern Enhancement
- [ ] T013 [P] Extend `execution/execution_patterns.py` enum to add PLANNING, AUTO, SIMPLE modes
- [ ] T014 Add simple pattern implementations to `execution/pattern_executor.py` (constitutional compliance: no new files)

### Memory System Enhancement (Parallel - different backends)
- [ ] T015 [P] Create `memory/backends/memgraph_backend.py` for knowledge graph storage
- [ ] T016 [P] Create `memory/backends/redis_backend.py` for fast cache storage
- [ ] T017 [P] Create `memory/backends/__init__.py` with backend registry
- [ ] T018 Update `memory/memory_manager.py` to support backend switching

### LiteLLM Integration
- [ ] T019 [P] Create `integrations/litellm_provider.py` for unified LLM proxy
- [ ] T020 Update existing LLM interfaces in `integrations/llm_interfaces.py` for LiteLLM compatibility

## Phase 3.4: Integration & Features

### Simple Benchmarking (Constitutional Compliance)
- [ ] T021 Add simple benchmark method to `agent.py` (no new modules per constitution)
- [ ] T022 [P] Create benchmark test scenarios in `tests/integration/test_benchmarking.py`

### Simple In-Context Learning (Constitutional Compliance)
- [ ] T023 Enhance `agent.py` `_build_enhanced_prompt` method for example injection
- [ ] T024 Add simple example management using existing memory system

### Tool Integration Enhancement
- [ ] T025 [P] Update `tools/tool_manager.py` for enhanced MCP support
- [ ] T026 [P] Extend `tools/mcp_adapter.py` for improved tool extensibility

## Phase 3.5: Polish & Validation

### Testing & Coverage (Parallel - different test files)
- [ ] T027 [P] Create unit tests for new LiteLLM integration in `tests/unit/test_litellm.py`
- [ ] T028 [P] Create unit tests for memory backends in `tests/unit/test_memory_backends.py`
- [ ] T029 [P] Update existing unit tests for backward compatibility validation

### Documentation & Examples
- [ ] T030 Update examples and documentation to reflect new capabilities (maintain existing API compatibility)

## Dependency Graph

### Sequential Dependencies:
1. **Setup** (T001-T003) → **Tests** (T004-T009) → **Core** (T010-T020) → **Integration** (T021-T026) → **Polish** (T027-T030)
2. **Agent modifications**: T010 → T011 → T012 (sequential, same file)
3. **Memory system**: T015,T016,T017 → T018 (backends before manager)

### Parallel Execution Groups:
- **Setup**: T003 can run parallel with T001-T002
- **Contract Tests**: T004-T009 all parallel (different files)
- **Memory Backends**: T015, T016, T017 parallel (different files)
- **Integration**: T019, T020, T022, T025, T026 parallel (different modules)
- **Unit Tests**: T027, T028, T029 parallel (different test files)

## Task Execution Examples

### Phase 3.2 Parallel Test Creation:
```bash
# All contract tests can run simultaneously
Task 1: "Create tests/contract/test_agent_core_streaming.py with failing streaming endpoint tests"
Task 2: "Create tests/contract/test_llm_config.py with failing LiteLLM configuration tests"
Task 3: "Create tests/contract/test_benchmark_api.py with failing benchmark endpoint tests"
```

### Phase 3.3 Memory Backend Parallel Development:
```bash
# Different backend files can be developed in parallel
Task 1: "Implement memory/backends/memgraph_backend.py with knowledge graph storage"
Task 2: "Implement memory/backends/redis_backend.py with fast cache storage"
Task 3: "Create memory/backends/__init__.py with backend registry and factory"
```

## Constitutional Compliance Notes

- **Simplified Design**: Extending existing files instead of creating new modules
- **TDD**: All tests (T004-T009) MUST be written first and MUST fail
- **Backward Compatibility**: Maintaining existing API while adding new features
- **Minimal Dependencies**: Only essential additions (LiteLLM, Memgraph, Redis)
- **90% Coverage Target**: Unit tests in Phase 3.5 ensure coverage requirements

## Validation Checkpoints

After each phase:
1. **Phase 3.1**: Dependencies installed, linting configured
2. **Phase 3.2**: All contract tests exist and fail (Red phase of TDD)
3. **Phase 3.3**: Core functionality implemented, tests pass (Green phase of TDD)
4. **Phase 3.4**: Integration features working, streaming and benchmarks functional
5. **Phase 3.5**: All tests pass, 90% coverage achieved, documentation updated

## Success Criteria

✅ **All 30 tasks completed**
✅ **All contract tests pass**
✅ **Backward compatibility maintained**
✅ **New features (streaming, patterns, memory backends) functional**
✅ **90% test coverage achieved**
✅ **Constitutional principles followed throughout**

---
*Based on implementation-guide.md and constitutional-compliance-fixes.md*