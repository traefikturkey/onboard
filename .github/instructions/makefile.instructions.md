---
description: "Makefile best practices for Joyride DNS Service build system"
applyTo: "**/Makefile"
---

# Makefile Development Standards

### Target Organization
- Use real file targets instead of `.PHONY` when possible
- Group related targets with comments
- Include help target with clear descriptions
- Use `@` prefix to suppress command echo for clean output

### Variable Management
- Export environment variables needed by child processes
- Use conditional assignment (`?=`) for defaults
- Detect platform and runtime automatically
- Define variables at top of file

### Development Targets
- `clean` - Remove generated files and caches
- `test` - Run test suites with coverage
- `lint` - Run code quality checks
- `format` - Apply code formatting
- `run` - Start application locally

### Background Process Management
- Send SIGTERM for graceful shutdown
- Use `--no-print-directory` for nested make calls

### DevContainer Integration
- Separate `.devcontainer/Makefile` for development-specific targets
- Include with `-include .devcontainer/Makefile`
- Use development-friendly paths and settings
