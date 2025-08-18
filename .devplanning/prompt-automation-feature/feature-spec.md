# Feature Specification: Automated Instruction Improvement Prompt

## Feature Description
Create a comprehensive, technology-agnostic prompt that automates the instruction improvement workflow by analyzing conversation history and systematically updating instruction files based on identified patterns, regardless of the project's technology stack.

## Core Components

### 1. Historical Analysis Engine
- **Input**: Conversation history files in `.specstory/history/*.md`
- **Process**: Parse each file for interaction patterns and AI/user issues
- **Output**: Structured analysis of common problems (technology-agnostic)

### 2. Pattern Recognition System
- **Input**: Analysis results from historical review
- **Process**: Identify recurring themes and consolidate into actionable patterns
- **Output**: Prioritized list of instruction improvements adaptable to any project type

### 3. Instruction File Orchestration
- **Input**: Consolidated improvement patterns
- **Process**: Map improvements to appropriate instruction files based on project structure and `applyTo` patterns
- **Output**: Systematic updates across the instruction ecosystem using project-appropriate tools and approaches

### 4. Verification Framework
- **Input**: Updated instruction files
- **Process**: Run project-appropriate tests, builds, and quality checks
- **Output**: Confirmation of successful implementation using project's toolchain

## Technical Requirements

### File Structure
```
.github/
└── prompts/
    └── update-instructions.prompt.md
```

### Dependencies
- Existing instruction files in `.github/instructions/`
- Main copilot instructions in `.github/copilot-instructions.md`
- VERSION timestamp file for tracking analysis points
- Project-appropriate test/build/quality checking tools (varies by project type)

### Integration Points
- Must work with current `.specstory/history/` file structure
- Must respect existing `applyTo` patterns in instruction files
- Must adapt to project's preferred toolchain (uv/npm/cargo/make/etc.)
- Must create/update VERSION timestamp for future analysis

## Functional Requirements

### FR1: Historical Conversation Analysis
The prompt must:
- Identify conversation files newer than VERSION timestamp (incremental) or all files (full analysis)
- Create intermediate `interaction-issues.md` with file-by-file analysis:
  - Header section for each conversation file using filename
  - Very brief content summary for each file
  - Documentation of AI/user interaction issues
  - Problems encountered during request resolution
- Process each conversation file individually before moving to pattern consolidation

### FR2: Pattern Consolidation
The prompt must:
- Review the `interaction-issues.md` file to identify common problem patterns
- Create `determined-issues.md` with systematic analysis:
  - Current Copilot documentation research
  - Existing instruction file analysis with `applyTo` patterns and purposes
  - Numbered common issues derived from interaction-issues.md review
  - Implementation notes with concrete next steps
- Consolidate improvement patterns across technology stacks
- Map improvements to appropriate instruction files based on file types involved in problems

### FR3: Systematic Implementation
The prompt must:
- Update instruction files with consolidated improvements
- Maintain consistent language and formatting
- Ensure project-appropriate tool usage (detect and use project's preferred tools)
- Add comprehensive examples relevant to the project's technology stack

### FR4: Verification and Tracking
The prompt must:
- Run project-appropriate verification commands (tests/builds/lints)
- Create git commit with detailed changelog
- Update VERSION timestamp
- Report success/failure status

## Non-Functional Requirements

### NFR1: Maintainability
- Prompt should be self-documenting
- Include clear step-by-step workflow
- Provide troubleshooting guidance
- Support incremental improvements

### NFR2: Reliability
- Include error handling for missing files
- Graceful degradation when history is limited
- Validation of instruction file updates
- Rollback guidance for failed implementations

### NFR3: Consistency
- Maintain existing instruction file patterns
- Preserve user-specific customizations
- Follow established markdown formatting
- Align with project coding standards

## User Stories

### US1: As a maintainer
I want to run a single prompt that analyzes recent conversations and improves our instruction files for any project type, so that I can systematically enhance AI assistance quality without manual effort regardless of technology stack.

### US2: As a developer
I want the instruction improvements to be tested and verified using my project's tools, so that I can trust the changes won't break existing workflows in Python, JavaScript, Rust, Go, or any other ecosystem.

### US3: As a future user
I want the improvement process to work across different project types and be repeatable and trackable, so that instruction quality continuously improves over time for any technology stack.

## Acceptance Criteria

### AC1: Complete Workflow Automation
- [ ] Single prompt recreates entire manual process
- [ ] No human intervention required for standard cases
- [ ] Clear progress reporting throughout execution

### AC2: Quality Assurance
- [ ] All instruction file updates are syntactically correct
- [ ] Project-appropriate test/build/quality suite passes after implementation  
- [ ] Git commit includes comprehensive changelog
- [ ] Generated `interaction-issues.md` provides file-by-file analysis with clear headers and issue documentation
- [ ] Generated `determined-issues.md` follows correct format:
  - Existing Instructions Summary with applyTo patterns and Purpose descriptions
  - Common Interaction Issues as numbered sections with Description, Key Pattern, Suggested Instruction, and Placement
  - Implementation Notes with concrete next steps and VERSION requirements

### AC3: Future Compatibility and Cross-Project Usage
- [ ] VERSION timestamp enables incremental analysis
- [ ] Prompt can be run repeatedly without conflicts
- [ ] New conversation patterns are automatically incorporated
- [ ] Works effectively across different technology stacks (Python, JavaScript, Go, Rust, etc.)
- [ ] Adapts to different project toolchains and verification approaches

## Implementation Risks

### Risk 1: File Format Changes
**Impact**: Medium
**Mitigation**: Include format validation and graceful handling of unexpected structures

### Risk 2: Instruction File Conflicts
**Impact**: High
**Mitigation**: Backup existing files before changes, provide rollback instructions

### Risk 3: Pattern Recognition Accuracy
**Impact**: Medium
**Mitigation**: Manual review checkpoints, conservative change approach

## Success Metrics
- Successful recreation of our manual improvement process
- 100% test pass rate after implementation
- Clean git commit with no manual fixups required
- Comprehensive instruction file coverage
