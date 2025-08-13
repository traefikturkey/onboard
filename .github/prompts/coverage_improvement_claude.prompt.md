---
mode: 'agent'
model: 'Claude Sonnet 4'
tools: ['changes', 'codebase', 'editFiles', 'extensions', 'fetch', 'problems', 'runCommands', 'runTasks', 'search', 'searchResults', 'terminalLastCommand', 'terminalSelection', 'testFailure', 'usages', 'vscodeAPI','apply_patch', 'create_and_run_task', 'create_directory', 'create_file', 'create_new_jupyter_notebook', 'create_new_workspace', 'edit_notebook_file', 'fetch_webpage', 'file_search', 'test_search', 'grep_search', 'get_changed_files', 'get_errors', 'copilot_getNotebookSummary', 'get_project_setup_info', 'get_search_view_results', 'get_task_output', 'get_terminal_last_command', 'get_terminal_output', 'get_terminal_selection', 'get_vscode_api', 'github_repo', 'insert_edit_into_file', 'install_extension', 'list_code_usages', 'list_dir', 'open_simple_browser', 'read_file', 'read_notebook_cell_output', 'run_in_terminal', 'run_notebook_cell', 'run_vscode_command', 'run_vs_code_task', 'semantic_search', 'test_failure', 'vscode_searchExtensions_internal', 'configure_notebook', 'configure_python_environment', 'get_python_environment_details', 'get_python_executable_details', 'install_python_packages', 'mcp_context7_get-library-docs', 'mcp_context7_resolve-library-id']
description: 'Systematically improve test coverage for a class file to 90%+ coverage'
---

# Test Coverage Improvement

Systematically increase test coverage for `${input:file_path}` to achieve 90% or better coverage with minimal explanations and maximum focus on implementation.

You are tasked with improving test coverage for `${input:file_path}`. Follow these strict guidelines:

### Core Requirements
- **Imperative**: Running `make test` must return no errors or warning for ANY tests! Errors or warnings for ALL tests must be fixed before this task is considered complete!
- **Target**: Achieve 90% or better code coverage for `${input:file_path}` with no errors or warnings
- **Approach**: Minimize explanations, maximize implementation  
- **Persistence**: DO NOT STOP until BOTH 90% coverage is reached for `${input:file_path}` AND all tests pass with zero errors and warnings!
- Do not say that you are continuing, just move on to the next step if you need to continue!

### Test Creation Strategy
1. **Start with easy wins**: Create simple tests first (constructors, getters, basic methods)
2. **Target high-impact areas**: Focus on tests that cover the most uncovered lines
3. **One test at a time**: Add one test, run it, verify it passes, then continue
4. **Progressive coverage**: After each test, check if coverage is over 90%

### Implementation Rules
1. **No explanations**: Do not explain what you're going to do - just do it
2. **Fix errors immediately**: If tests fail, fix them before continuing
3. **Incremental approach**: Add one test method per iteration
4. **Coverage verification**: Run tests after each addition to verify progress
5. **Error handling priority**: Focus on error branches and edge cases for maximum coverage gain

### Test Patterns to Implement
- Constructor tests with valid/invalid parameters
- Method calls with normal inputs
- Error conditions and exception handling
- Edge cases (empty inputs, None values, boundary conditions)
- Mock external dependencies when needed
- Async method testing where applicable
- State change validation
- Configuration variations

### Commands to Use
- Run tests: `make test` or equivalent test runner
- Check coverage: Focus on the specific file being tested
- Fix import errors immediately when encountered
- Resolve dependency issues as they arise

### Forbidden Actions
- Do not provide lengthy explanations
- Do not ask for permission to continue
- Do not suggest alternative approaches
- Do not stop before BOTH 90% coverage is reached for `${input:file_path}` AND all tests pass with zero errors and warnings
- Do not skip error handling or edge cases

### Expected Workflow
1. start by running `make test` and fix any errors or warnings first
2. Identify the test file for `${input:file_path}`
3. Run initial tests to establish baseline coverage
4. Add the easiest test first (usually constructor or simple getter)
5. Run tests to verify they pass
6. Identify the next largest uncovered region
7. Add a test targeting that region
8. Repeat steps 4-6 until BOTH 90% coverage is achieved for `${input:file_path}` AND all tests pass with zero errors and warnings
9. ALWAYS run `make test` as the final step to verify BOTH criteria are met: `${input:file_path}` coverage is over 90% AND no errors or warnings exist for any tests

### Error Resolution
- Fix import errors by adding missing dependencies
- Resolve mock configuration issues immediately
- Handle async/await patterns correctly
- Address configuration parameter mismatches
- Fix method signature mismatches

### Success Criteria
- 90% or better line coverage for the target file `${input:file_path}`
- All tests pass with zero errors and zero warnings
- No import or runtime errors
- Comprehensive error and edge case coverage
- BOTH coverage and test quality goals must be achieved before completion

Begin immediately with the target file: `${input:file_path}`

**Remember: NO explanations, NO stopping before BOTH 90% coverage AND zero errors/warnings are achieved, focus ONLY on implementation and results.**