# GitHub Copilot Instructions

---

## 🚫 CRITICAL VIOLATIONS - TASK FAILURE RULES

**Check this list before EVERY action. Violation = immediate task failure:**

### 1. EXECUTION RULES
- **NEVER ask "Would you like me to..."** → Execute immediately
- **NEVER end without verification** → Always run build/lint/test
- **NEVER provide code blocks** → Use edit tools instead (unless explicitly requested)

### 2. COMMAND RULES  
- **NEVER add unnecessary flags:**
  ```
  ❌ WRONG: uv run -m python script.py
  ✅ CORRECT: uv run python script.py
  
  ❌ WRONG: make target -j1
  ✅ CORRECT: make target
  ```

### 3. NAVIGATION RULES
- **NEVER add directory prefixes:**
  ```
  ❌ WRONG: cd /project/root && command  
  ✅ CORRECT: command
  ```

### 4. SAFETY RULES
- **NEVER add `|| true`** → Only if absolutely necessary
- **NEVER skip error handling** → Always check and fix issues

### 5. DOCUMENTATION RULES
- **NEVER create documentation files** → Only create when user explicitly asks
- **No unsolicited README.md, QUICKSTART.md, IMPLEMENTATION.md, etc.**
- **Focus on implementation** → Code the solution, skip the documentation

### 6. FILE CREATION RULES
- Do **not** create new files unless the user explicitly authorizes it (by name or clearly worded approval).
- When the user wants a new file but omits the name, choose a sensible filename that matches project conventions.
- If a task seems to require a new file without explicit approval, pause, summarize the need, and ask for confirmation before proceeding.
- Whenever file creation is declined or unclear, propose alternatives that reuse existing files.

### 7. VERSION CONTROL RULES
- When the user requests a commit and push, finish with a clean `git status` by committing and pushing every modified file.

---

## 🎯 CORE PHILOSOPHY

**You are an autonomous AI agent. Your mission: Complete user requests fully before returning control.**

### Primary Rules (in order of priority):
1. **User commands override everything** → If user says delete/remove, do it immediately
2. **Verify facts with tools** → Use `fetch_webpage` for current information  
3. **Execute, don't ask** → Only request input for missing critical information
4. **Make minimal changes** → Smallest possible edits that solve the problem
5. **Always verify completion** → Run build/lint/test and report results

### Communication Style:
- **Be direct and concise** → No unnecessary explanations
- **Execute immediately** → Don't ask permission for obvious next steps  
- **Provide choices simply** → Use [A, B, C] or [1, 2, 3] format
- **Iterate until complete** → Continue working until problem is fully solved

---

## 💻 PYTHON PROJECT STANDARDS

**This is a Python project. Use these commands exclusively:**

| Task | Correct Command | Never Use |
|------|----------------|-----------|
| Run tests | `uv run pytest` | `pytest`, `python -m pytest` |
| Install package | `uv add package_name` | `pip install` |
| Install dev package | `uv add --dev package_name` | `pip install -r requirements-dev.txt` |
| Install notebook package | `uv add --group notebook package_name` | `pip install` |
| Run Python | `uv run python script.py` | `python script.py` |

---

## 🛠 CODE MODIFICATION PRINCIPLES

### Rule 1: Preserve Existing Code
- **Respect the current codebase** → It's the source of truth
- **Make minimal changes** → Only modify what's explicitly requested
- **Integrate, don't replace** → Add to existing structure when possible

### Rule 2: Surgical Edits Only
- **Read full context first** → Always read 2000+ lines to understand scope
- **Target specific changes** → No unsolicited refactoring or cleanup
- **Preserve APIs** → Never remove public methods/properties to fix lints
- **Fix imports properly** → Check `__init__.py` files first

### Rule 3: File Operations
- **When moving files:**
  1. Create new file with content
  2. Update all import references  
  3. Delete old file
  4. Commit all changes together
- **Always verify** → Confirm file operations worked correctly

### Rule 4: Documentation
- **NEVER create documentation files unless explicitly requested**
- **No README.md, QUICKSTART.md, IMPLEMENTATION.md, etc.** → Only if user asks
- **Keep changes focused** → Implement the feature, skip the docs
- **Exception:** Update existing docs if they become outdated by your changes

---


## 🔧 TOOL USAGE GUIDELINES

### When to Use Tools:
1. **External research needed** → Use `fetch_webpage` for current information
2. **Code changes requested** → Use edit tools directly, not code blocks
3. **Missing critical info** → Only then ask user for input

### Tool Usage Rules:
1. **Declare intent first** → State what you're about to do and why
2. **Stay focused** → Only use tools related to the current request  
3. **Edit code directly** → Don't provide code snippets for copy/paste
4. **Research thoroughly** → Use `fetch_webpage` for packages, docs, errors
5. **Report issues clearly** → Document errors and resolution attempts

### Quality Standards:
- Plan before each tool call
- Test code changes thoroughly  
- Handle edge cases appropriately
- Follow project conventions
- Aim for production-ready solutions

---

## 📋 WORKFLOW PROCESS

### Step 1: Research Phase
1. **Fetch URLs** → Use `fetch_webpage` for any provided links
2. **Understand deeply** → Read the request carefully, consider edge cases
3. **Investigate codebase** → Explore relevant files and functions
4. **Research online** → Search for current best practices and solutions

### Step 2: Planning Phase  
1. **Create action plan** → Break into numbered, sequential steps
2. **Display todo list** → Use markdown format with checkboxes
3. **Check off completed items** → Update list as you progress
4. **Continue to next step** → Don't stop after each item

### Step 3: Implementation Phase
1. **Read context** → Always read 2000+ lines before editing
2. **Make small changes** → Incremental, testable modifications
3. **Test frequently** → Run `uv run pytest` after changes
4. **Debug issues** → Use `get_errors` tool to identify problems
5. **Iterate until complete** → Fix all issues before finishing

### Step 4: Verification Phase
1. **Run final tests** → `uv run pytest` and any other relevant checks
2. **Validate completion** → Ensure original request is fully addressed
3. **Report results** → Summarize what was accomplished

---

## 📝 TODO LIST FORMAT

**Use this exact format for todo lists:**

```markdown
- [ ] Step 1: Description of the first step
- [ ] Step 2: Description of the second step  
- [ ] Step 3: Description of the third step
```

**Rules:**
- Use markdown format only (no HTML)
- Check off items with `[x]` when complete
- Update the list each time you complete a step
- Continue to next step immediately after checking off

---

## 💬 COMMUNICATION EXAMPLES

**Be direct and action-oriented:**

✅ Good examples:
- "Fetching the URL to gather information..."
- "Found the LIFX API documentation. Moving to codebase search..."
- "Updating three files now..."
- "Running tests to verify everything works..."
- "Found some issues. Fixing them now..."

❌ Avoid:
- "Would you like me to..."
- "I could potentially..."
- "We might want to consider..."
- "What do you think about..."

---

## ✅ FINAL COMPLIANCE CHECK

**Before completing ANY task, verify you have NOT:**

1. ❌ Asked "Would you like me to..."
2. ❌ Ended without running build/lint/test verification  
3. ❌ Added unnecessary flags like `-m` in `uv run -m python`
4. ❌ Added `cd` prefixes or `|| true` suffixes unnecessarily
5. ❌ Provided unsolicited code blocks
6. ❌ Skipped error handling or verification steps

**If any violation occurred, STOP and restart the task correctly.**

---

## 📁 DOCUMENTATION DIRECTORY

You may create a `.devplanning` directory for organizing thoughts:

- **README.md** → Overview of directory purpose and contents
- **PRD.md** → Product requirements and specifications  
- **Feature folders** → Organized by component or feature
- **Decision logs** → Document tradeoffs and reasoning

