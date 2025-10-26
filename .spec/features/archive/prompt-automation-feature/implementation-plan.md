# Implementation Plan: Automated Instruction Improvement Prompt

## Phase 1: Analysis and Planning

### Step 1: Review Current Implementation
- [x] Analyze recent commit changes (07dcdbd)
- [x] Document the 14 improvement patterns we implemented
- [x] Map changes to instruction files
- [x] Understand VERSION timestamp usage

### Step 2: Extract Workflow Patterns
- [x] Document the exact sequence of operations we performed
- [x] Identify decision points and branching logic
- [x] Capture file selection criteria
- [x] Document verification steps

### Step 3: Create Prompt Structure
- [x] Design main workflow sections
- [x] Define input/output formats
- [x] Plan error handling approaches
- [x] Structure verification checkpoints

## Phase 2: Prompt Development

### Step 4: Core Workflow Implementation
- [x] Historical analysis section
- [x] Pattern recognition logic
- [x] File mapping strategies
- [x] Implementation sequencing

### Step 5: Instruction File Templates
- [x] Python instruction patterns
- [x] Docker/container patterns
- [x] Testing framework patterns
- [x] Makefile patterns
- [x] Core copilot instruction patterns

### Step 6: Verification Framework
- [x] Test execution commands
- [x] Git operation sequences
- [x] Error detection patterns
- [x] Success validation criteria

## Phase 3: Testing and Refinement

### Step 7: Prompt Validation
- [x] Dry-run simulation
- [x] Test against current state
- [x] Verify all file paths and commands
- [x] Check instruction file syntax

### Step 8: Documentation
- [x] Usage instructions
- [x] Troubleshooting guide
- [x] Example scenarios
- [x] Maintenance procedures

### Step 9: Integration
- [x] Place prompt in `.github/prompts/`
- [x] Update project documentation
- [x] Create usage examples
- [x] Document for future maintainers

## Detailed Task Breakdown

### Task 1: Workflow Extraction
**Inputs**: 
- Git commit 07dcdbd changes
- `.devplanning/prompt-improvements-2025-09-14/` analysis
- Current instruction file state

**Process**:
1. Map each instruction file change to improvement pattern
2. Document the decision logic for file selection
3. Extract the exact text replacement patterns used
4. Identify the verification commands executed
5. **Generalize patterns to work across technology stacks**

**Outputs**:
- Generic workflow sequence document
- Technology-agnostic decision matrix for file updates
- Universal template patterns for common changes

### Task 2: Pattern Codification
**Inputs**:
- 14 improvement patterns from determined-issues.md
- Instruction file mapping logic
- **Generic implementation examples for multiple technology stacks**

**Process**:
1. Convert each pattern into technology-agnostic prompt instructions
2. Create conditional logic for pattern application across project types
3. Define project-adaptive customization rules
4. Build verification checkpoints that work with any toolchain

**Outputs**:
- Universal pattern application rules
- Technology-adaptable instruction templates
- Generic verification command sequences

### Task 3: Prompt Assembly
**Inputs**:
- Generic workflow sequence
- Universal pattern application rules
- Cross-technology verification framework
- Technology-agnostic error handling strategies

**Process**:
1. Structure main prompt sections for any project type
2. Integrate decision logic that adapts to different toolchains
3. Add verification checkpoints that work across technologies
4. Include error recovery procedures for various project types

**Outputs**:
- Complete generic prompt file
- Cross-technology usage documentation
- Universal test validation plan

## Success Criteria Checklist

### Functional Completeness
- [x] Prompt recreates exact workflow principles from commit 07dcdbd in generic form
- [x] All 14 improvement patterns are abstracted into universal principles
- [x] File mapping logic is comprehensive and technology-agnostic
- [x] Verification steps work across different technology stacks

### Technical Quality
- [x] All file paths are correct and adaptable
- [x] Command sequences are parameterized for different toolchains
- [x] Error handling works across project types
- [x] Git operations are safe and universal

### Cross-Technology Usability
- [x] Clear step-by-step instructions for any project type
- [x] Progress reporting works with any verification approach
- [x] Error messages are actionable across technologies
- [x] Documentation covers multiple technology examples

### Maintainability
- [x] Prompt structure is modular and technology-agnostic
- [x] Easy to extend with new patterns from any technology stack
- [x] Version tracking is maintained universally
- [x] Future compatibility across evolving toolchains is ensured

## Timeline Estimate
- Phase 1: 30 minutes (analysis and planning)
- Phase 2: 45 minutes (prompt development)
- Phase 3: 15 minutes (testing and refinement)
- **Total**: ~90 minutes

## Dependencies
- Access to current instruction files
- Understanding of git workflow
- Knowledge of uv command patterns
- Test suite availability

## Risk Mitigation
1. **Pattern Accuracy**: Cross-reference with actual changes made
2. **File Conflicts**: Include backup/rollback procedures
3. **Command Errors**: Validate all shell commands before inclusion
4. **Version Tracking**: Ensure VERSION file logic is correct
