---
description: "DevContainer configuration best practices for development environment"
applyTo: "**/.devcontainer/**"
---

# DevContainer Development Standards

### Container Configuration
- Use multi-stage Dockerfile with dedicated development target
- Include Docker-in-Docker feature for container testing
- Mount Docker socket for container integration testing
- Use non-root user (`anvil`) for security

### Environment Management
- Load both root `.env` and `.devcontainer/.env` via runArgs
- Initialize environment with `make initialize` using `initializeCommand` devcontainer.json setting
- `.devcontainer/.env` will be created by `make initialize`

### Development Tools
- Configure zsh with autosuggestions for better developer experience
- Install Language development dependencies automatically
- Set up proper VS Code extensions and settings

### Volume Mounts
- Home directory persistence: `${localWorkspaceFolderBasename}-home` volume
- SSH key access for git operations
- Docker socket access for container management

### Integration Testing Support
- Configure Make targets for comprehensive testing
- Support background service management with PID files

### Post-Create Commands
- Use `postCreateCommand` to run `./.devcontainer/setup-dotfiles.sh` and update programming language libraries after container creation
- Initialize development environment variables
- Prepare testing infrastructure
