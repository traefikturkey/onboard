# Existing Instructions Summary

## .github/copilot-instructions.md
applyTo: (implicit global via orchestration)
Purpose: Defines autonomous agent workflow, mandates tool usage for research, planning rigor, verbose planning while asking for concision; sets lifecycle (fetch, investigate, plan, implement, test) and todo list protocol.

## devcontainer.instructions.md
applyTo: `**/.devcontainer/**`
Purpose: Best practices for devcontainer config—multi-stage, non-root user, env loading, volumes, post-create commands, tooling.

## dockerfile.instructions.md
applyTo: `**/Dockerfile*`
Purpose: Dockerfile standards—base image choice, multi-stage separation, security, layer and package ordering, caching, health checks, example pattern.

## ignore-files.instructions.md
applyTo: `**/.{gitignore,dockerignore}`
Purpose: Synchronization and ordering rules for ignore files; defines shared vs file-specific entries, ordering conventions.

## makefile.instructions.md
applyTo: `**/Makefile`
Purpose: Makefile structure, variable management, semantic version bumping, background process guidance, devcontainer integration.

## python.instructions.md
applyTo: `**/*.py`
Purpose: Python style, typing, naming, documentation, error handling, configuration, Flask patterns, testing expectations, tooling.

## self-explanatory-code-commenting.instructions.md
applyTo: `**`
Purpose: Promote minimal commenting focused on WHY; enumerates good vs bad comment patterns and annotation tags.

## taming-copilot.instructions.md
applyTo: `**`
Purpose: Governance/constraint overlay—priority of user directives, minimalism, concise answers, code only on request, minimal diffs.

## testing.instructions.md
applyTo: `**/tests/**/*.py`
Purpose: Testing layout, naming, fixtures, coverage goals, integration guidance, sample patterns.

# Common Interaction Issues

## 1. Premature Completion Claims
Description: AI states tasks are complete before verifying builds/tests (e.g., Dockerfile changes, conversion to uv).
Suggested Instruction: "Before declaring a task complete: run required verification (build/lint/test) and explicitly report PASS/FAIL for each. Never claim completion without evidence." 
Placement: `.github/copilot-instructions.md` (workflow enforcement) and `taming-copilot.instructions.md` (concise verification rule).

## 2. Excessive Verbosity / Micro-Step Narration
Description: Over-detailed narration for trivial actions increases noise.
Suggested Instruction: "Batch related minor edits; summarize results in one concise paragraph—avoid step-by-step narration for mechanical fixes." 
Placement: `taming-copilot.instructions.md`.

## 3. Large Rewrites Instead of Minimal Diffs
Description: Performed broad Dockerfile rewrites or code changes when user requested minimal invasive fixes.
Suggested Instruction: "When the user requests a fix, first attempt a surgical diff (limit scope to lines directly causing failure). Provide rationale if a broader refactor is unavoidable." 
Placement: `taming-copilot.instructions.md` (Surgical Code Modification) and reinforce in `.github/copilot-instructions.md`.

## 4. Ignoring Explicit Directives (e.g., Do Not Recreate Deleted Files)
Description: Created shim after instruction that deleted files should not be recreated.
Suggested Instruction: "If user forbids an action (e.g., recreating a file), treat that as a hard constraint—adapt code/tests instead; flag any ambiguity before proceeding." 
Placement: `taming-copilot.instructions.md` (Primacy of User Directives clarification).

## 5. Trial-and-Error Loops Without Holistic Analysis
Description: Repeated incremental Dockerfile changes (PATH/permissions) instead of planning full correct sequence.
Suggested Instruction: "After two consecutive failure iterations in same context, pause and produce a consolidated root-cause analysis and end-state patch plan before further edits." 
Placement: `.github/copilot-instructions.md` (Debugging section) and `dockerfile.instructions.md` (methodical change guidance).

## 6. Overuse of Intermediate Confirmation Questions
Description: Asked for confirmation on obvious next actions.
Suggested Instruction: "Do not request confirmation for clearly implied next steps; proceed unless material ambiguity affects outcome." 
Placement: `taming-copilot.instructions.md`.

## 7. Overwriting Functionality Without Preserving Behavior
Description: Property removed (Widget.name) to satisfy linter without validating design intent.
Suggested Instruction: "When resolving lint/type issues, prefer targeted fixes (type hints, guards) over removing/altering public API—flag potential behavior changes before applying." 
Placement: `python.instructions.md` (Error Handling / Style) and `taming-copilot.instructions.md`.

## 8. Unnecessary Workarounds Before Canonical Fix (behave skip)
Description: Added skip guard instead of installing missing dependency.
Suggested Instruction: "Prefer resolving root cause (install required dependency) before adding conditional skips; only introduce guard if dependency is intentionally optional." 
Placement: `testing.instructions.md`.

## 9. Import Path Confusion and Path Hacks
Description: Multiple sys.path manipulations before structural import review.
Suggested Instruction: "For import errors: first inspect package layout and existing __init__.py files; avoid sys.path hacks unless temporary and documented." 
Placement: `python.instructions.md` and `testing.instructions.md`.

## 10. Dynamic Import Patching Fragility in Tests
Description: Complex patching of internals for Widget.from_dict.
Suggested Instruction: "Favor exercising public API with supplied test doubles over patching function __globals__; refactor for dependency injection when patching becomes brittle." 
Placement: `testing.instructions.md`.

## 11. Redundant Rebuilds Without Caching Strategy
Description: Many Docker builds adjusting uv install path sequentially.
Suggested Instruction: "When iterating on Dockerfile dependency install failures: draft full corrected RUN block locally, then apply once; explain cache implications." 
Placement: `dockerfile.instructions.md`.

## 12. Missing Post-Change Validation Summary
Description: Changes applied without immediate lint/test run summary.
Suggested Instruction: "After any multi-file patch: run lint + focused tests; output concise PASS/FAIL matrix (Lint | Unit | Integration | Build)." 
Placement: `.github/copilot-instructions.md`.

## 13. Scope Creep (Adding Unrequested Abstractions)
Description: Added extra abstractions beyond step scope.
Suggested Instruction: "Limit implementation to explicit scope; list potential enhancements separately under 'Optional Next Steps' instead of implementing." 
Placement: `taming-copilot.instructions.md`.

## 14. Excessive Patch Churn on Single File
Description: Multiple rewrites of test file before stable version.
Suggested Instruction: "Before large test refactor: outline intended final structure (sections/assert focus) in scratch, then apply single patch." 
Placement: `testing.instructions.md`.

## 15. Lack of Early Environment/Context Verification
Description: Suggested fixes (Node missing) without verifying actual installed paths.
Suggested Instruction: "Verify existence/path of referenced binaries or configs before prescribing installation or cleanup actions." 
Placement: `devcontainer.instructions.md` and `.github/copilot-instructions.md`.

## 16. Verbose Repetition of Unchanged Checklists
Description: Reprinted full checklist after each minor update.
Suggested Instruction: "When reporting progress, only show delta (updated steps) unless user explicitly requests full checklist." 
Placement: `.github/copilot-instructions.md`.

## 17. Insufficient Guard Against Removing Needed Features
Description: Removed multi-stage targets inadvertently.
Suggested Instruction: "Before deleting or replacing a build stage/file: enumerate dependents (FROM targets, scripts) and confirm none required; otherwise adapt rather than remove." 
Placement: `dockerfile.instructions.md`.

## 18. Not Flagging Potential Behavioral Regressions in Lint Fixes
Description: Silent behavioral change to satisfy linter.
Suggested Instruction: "If a lint fix alters behavior or API surface, annotate commit note and request confirmation if risk > low." 
Placement: `python.instructions.md`.

## 19. Mixing Planning Philosophy (Verbose vs Concise)
Description: Conflict between expansive planning and mandate for concise output.
Suggested Instruction: "Use concise mode by default; detailed expansion only when ambiguity > medium or on explicit user request." 
Placement: `taming-copilot.instructions.md` & `.github/copilot-instructions.md` (clarify priority of concision when tension arises).

## 20. Failure Recovery Strategy Not Explicit
Description: Sequential failed patches without fallback plan articulation.
Suggested Instruction: "After two failed patch applications: present fallback options (smaller diff, manual segment edit) before retrying." 
Placement: `.github/copilot-instructions.md`.

