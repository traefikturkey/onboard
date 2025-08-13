---
description: "Ignore file management best practices - maintaining .gitignore and .dockerignore synchronization and organization"
applyTo: "**/.{gitignore,dockerignore}"
---

# Ignore Files Management Instructions

Maintain `.gitignore` and `.dockerignore` files with alphabetical ordering and proper synchronization.

## File Organization Rules

### Alphabetical Ordering
- All entries in alphabetical order within sections
- Case-sensitive ordering (uppercase before lowercase)
- Special characters sorted by ASCII value

### Synchronization Rules
**Both files must include:**
- Python bytecode (`*.pyc`, `__pycache__/`)
- Build artifacts (`build/`, `dist/`, `*.egg-info/`)
- Testing outputs (`.coverage`, `.htmlcov/`, `.pytest_cache/`)
- Environment files (`.env.*`)

**Only .gitignore:**
- Editor files (`.vscode/`, `.idea/`)
- Local development files

**Only .dockerignore:**
- Documentation (`README.md`, `docs/`)  
- CI/CD files (`.github/`)
- Git metadata (`.git/`, `.gitignore`)
