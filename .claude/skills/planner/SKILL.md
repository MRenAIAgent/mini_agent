---
name: planner
description: Use when planning feature implementations, creating design artifacts, or structuring development tasks. Apply when user mentions planning, designing, architecting new features, or needs to break down complex features into implementation phases. Use proactively when user describes a substantial new feature to implement.
---

# Implementation Planning Workflow

Execute the implementation planning workflow using the plan template to generate design artifacts.

## When This Skill Activates

Use this skill when:
- User describes a new feature to implement
- User asks to "plan", "design", or "architect" something
- User mentions creating specifications or design documents
- A complex feature needs to be broken down into phases
- User asks "how should we implement X?"

## Planning Process

Given the implementation details (from user or arguments):

1. **Setup**: Run `.specify/scripts/bash/setup-plan.sh --json` from repo root and parse JSON for:
   - FEATURE_SPEC
   - IMPL_PLAN
   - SPECS_DIR
   - BRANCH

   All future file paths must be absolute.

2. **Analyze Feature Specification**: Read and understand:
   - Feature requirements and user stories
   - Functional and non-functional requirements
   - Success criteria and acceptance criteria
   - Technical constraints or dependencies

3. **Load Constitutional Requirements**:
   Read `.specify/memory/constitution.md` to ensure plan follows all framework principles.

4. **Execute Implementation Plan Template**:
   - Load `.specify/templates/plan-template.md` (already copied to IMPL_PLAN path)
   - Set Input path to FEATURE_SPEC
   - Run the Execution Flow (main) function steps 1-9
   - The template is self-contained and executable
   - Follow error handling and gate checks as specified
   - Let the template guide artifact generation in $SPECS_DIR:
     * Phase 0 generates research.md
     * Phase 1 generates data-model.md, contracts/, quickstart.md
     * Phase 2 generates tasks.md
   - Incorporate user-provided details from arguments into Technical Context
   - Update Progress Tracking as you complete each phase

5. **Verify Execution Completed**:
   - Check Progress Tracking shows all phases complete
   - Ensure all required artifacts were generated
   - Confirm no ERROR states in execution

6. **Report Results**:
   Provide branch name, file paths, and summary of generated artifacts.

## Important Notes

- Always use absolute paths with repository root for all file operations
- Ensure constitutional compliance throughout planning
- Generate comprehensive design artifacts before implementation
- Break complex features into manageable phases
- Include technical context from user input

## Output Artifacts

Expect to generate:
- research.md (Phase 0)
- data-model.md (Phase 1)
- contracts/ directory (Phase 1)
- quickstart.md (Phase 1)
- tasks.md (Phase 2)
