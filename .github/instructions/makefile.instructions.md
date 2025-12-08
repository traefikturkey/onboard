---
description: "Makefile best practices for Joyride DNS Service build system"
applyTo: "**/Makefile"
---

# Makefile Development Standards

## Command Usage
- **Use make commands without flags unless required for the specific task**
- **Do not add `-s`, `-j1`, or other flags unless the user requests them**
- Adding unnecessary flags causes build system failures

### Target Organization
- Use real file targets instead of `.PHONY` when possible
- Group related targets with comments
- Use `@` prefix to suppress command echo for clean output

### Background Process Management
- Send SIGTERM for graceful shutdown
- Use `--no-print-directory` for nested make calls

### DevContainer Integration
- Separate `.devcontainer/Makefile` for development-specific targets
- Include with `-include .devcontainer/Makefile`
- Use development-friendly paths and settings

### Variable Management
- Export environment variables needed by child processes
- Use conditional assignment (`?=`) for defaults
- Detect platform and runtime automatically
- Define variables at top of file

#### Variable initialization Examples

```makefile
# https://docs.docker.com/develop/develop-images/build_enhancements/
# https://www.docker.com/blog/faster-builds-in-compose-thanks-to-buildkit-support/
export DOCKER_BUILDKIT := 1
export DOCKER_SCAN_SUGGEST := false
export COMPOSE_DOCKER_CLI_BUILD := 1

# Include development targets if available
-include .devcontainer/Makefile

ifneq (,$(wildcard .env))
	include .env
	export
endif

# Cross-platform detection
ifeq ($(OS),Windows_NT)
	DETECTED_OS := windows
	SHELL_CMD := powershell
	ifneq (, $(shell where pwsh))
		SHELL_CMD := pwsh
	endif
else
	UNAME_S := $(shell uname -s)
	ifeq ($(UNAME_S),Linux)
		DETECTED_OS := linux
	endif
	ifeq ($(UNAME_S),Darwin)
		DETECTED_OS := macos
	endif
endif


# Host IP detection (simplified for devcontainer)
ifndef HOSTIP
	ifeq ($(DETECTED_OS),linux)
		# In devcontainer/Docker, get the host gateway IP (Docker host)
		HOSTIP := $(shell ip route get 1 | head -1 | awk '{print $$7}' )
	else ifeq ($(DETECTED_OS),macos)
		HOSTIP := $(shell ifconfig | grep "inet " | grep -Fv 127.0.0.1 | awk '{print $$2}' )
	else ifeq ($(DETECTED_OS),windows)
		HOSTIP := $(shell powershell -noprofile -command '(Get-NetIPConfiguration | Where-Object {$$_.IPv4DefaultGateway -ne $$null -and $$_.NetAdapter.Status -ne "Disconnected"}).IPv4Address.IPAddress' )
	endif
endif

# Container runtime detection
ifndef CONTAINER_RUNTIME
	ifneq (, $(shell which podman 2>/dev/null))
		CONTAINER_RUNTIME := podman
	else
		CONTAINER_RUNTIME := docker
	endif
endif

# Export variables
export HOSTIP
export CONTAINER_RUNTIME
export DETECTED_OS
export SEMANTIC_VERSION
```

### Development Targets
- Should be placed in `.devcontainer/Makefile` if .devcontainer directory exists
- `clean` - Remove generated files and caches
- `test` - Run test suites with coverage
- `lint` - Run code quality checks
- `format` - Apply code formatting
- `run` - Start application locally
- include version management targets

### Docker Build Targets
- `build` / `build-dev` - Standard Docker builds for production/devcontainer
- `buildx` / `buildx-dev` - BuildKit builds with local cache export/import
- `build-bench` / `build-bench-dev` - Benchmarking builds with timing and context size
- `test-build-prod` / `test-build-dev` - Validation builds that verify key binaries work
- `test-build` - Run both production and devcontainer validation

#### Version Management Example

```makefile
# -------------------------------
# Semantic version bumping logic
# -------------------------------
SEMANTIC_VERSION := $(shell git tag --list 'v*.*.*' --sort=-v:refname | head -n 1)
VERSION := $(shell if [ -z "$(SEMANTIC_VERSION)" ]; then echo "0.0.0"; else echo $(SEMANTIC_VERSION) | sed 's/^v//'; fi)

# Export for docker-compose
export SEMANTIC_VERSION

define bump_version
	@echo "Latest version: $(SEMANTIC_VERSION)"
	@NEW_VERSION=$$(echo $(VERSION) | awk -F. -v type="$(1)" 'BEGIN {OFS="."} { \
		if (type == "patch") {$$3+=1} \
		else if (type == "minor") {$$2+=1; $$3=0} \
		else if (type == "major") {$$1+=1; $$2=0; $$3=0} \
		print $$1, $$2, $$3}') && \
	echo "New version: $$NEW_VERSION" && \
	git tag -a "v$$NEW_VERSION" -m "Release v$$NEW_VERSION" && \
	git push --tags && \
	echo "Tagged and pushed as v$$NEW_VERSION"
endef

bump-patch:
	$(call bump_version,patch)

bump-minor:
	$(call bump_version,minor)

bump-major:
	$(call bump_version,major)

publish: bump-patch
	@git push --all
```

