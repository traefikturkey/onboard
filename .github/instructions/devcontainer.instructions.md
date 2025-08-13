---
description: "DevContainer configuration best practices for development environment"
applyTo: "**/.devcontainer/**"
---

# DevContainer Development Standards

### Container Configuration
- Use multi-stage Dockerfile with dedicated development target
- Include Docker-in-Docker feature for container testing
- Mount Docker socket for container integration testing
- Use non-root user (`vscode`) for security

### Environment Management
- Separate `.devcontainer/.env` for development-specific variables
- Load both root `.env` and `.devcontainer/.env` via runArgs
- Initialize environment with `make initialize`

### Development Tools
- Configure zsh with autosuggestions for better developer experience
- Install Python development dependencies automatically
- Set up proper VS Code extensions and settings

### Volume Mounts
- Home directory persistence: `devcontainer-home` volume
- SSH key access for git operations

### Integration Testing Support
- Configure Make targets for comprehensive testing
- Support background service management with PID files

### Post-Create Commands
- Install development dependencies
- Set up dotfiles and shell configuration
- Initialize development environment variables
- Prepare testing infrastructure
