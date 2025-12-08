# https://docs.docker.com/develop/develop-images/build_enhancements/
# https://www.docker.com/blog/faster-builds-in-compose-thanks-to-buildkit-support/
DOCKER_BUILDKIT := 1
DOCKER_SCAN_SUGGEST := false
COMPOSE_DOCKER_CLI_BUILD := 1

export DOCKER_BUILDKIT
export DOCKER_SCAN_SUGGEST
export COMPOSE_DOCKER_CLI_BUILD

# Force Git Bash on Windows for Unix command compatibility
ifeq ($(OS),Windows_NT)
    SHELL := C:/Program Files/Git/bin/bash.exe
endif

# Default target - must be defined before any includes
.DEFAULT_GOAL := up

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

up: build
	$(CONTAINER_RUNTIME) run --rm --name onboard_prod_run -p 9830:9830 onboard:prod

.env:
	touch .env

build: .env
	$(CONTAINER_RUNTIME) build -t onboard:prod --target production .

build-dev: .env
	$(CONTAINER_RUNTIME) build --target devcontainer -t onboard .

# Build with docker buildx and local cache export/import for cross-host reuse
.PHONY: buildx-setup buildx buildx-dev
buildx-setup:
	@if [ "$(CONTAINER_RUNTIME)" != "docker" ]; then \
		echo "[buildx] Skipping setup: buildx is only available with docker runtime (current: $(CONTAINER_RUNTIME))"; \
		exit 0; \
	fi
	@sh -c 'if docker buildx version >/dev/null 2>&1; then \
	  docker buildx ls | grep -q "onboard-builder" || docker buildx create --name onboard-builder --use >/dev/null; \
	else \
	  echo "[buildx] Plugin not available; will fall back to standard docker build"; \
	fi'
	@mkdir -p .buildcache

buildx: .env buildx-setup
	@if [ "$(CONTAINER_RUNTIME)" != "docker" ] || ! docker buildx version >/dev/null 2>&1; then \
		echo "[buildx] Using standard build since runtime is $(CONTAINER_RUNTIME)"; \
		$(CONTAINER_RUNTIME) build -t onboard:prod --target production .; \
	else \
		echo "[buildx] Building with cache to/from .buildcache and loading image locally"; \
		docker buildx build \
			--target production \
			-t onboard:prod \
			--cache-from=type=local,src=.buildcache \
			--cache-to=type=local,dest=.buildcache,mode=max \
			--load \
			.; \
	fi

buildx-dev: .env buildx-setup
	@if [ "$(CONTAINER_RUNTIME)" != "docker" ] || ! docker buildx version >/dev/null 2>&1; then \
		echo "[buildx] Using standard build since runtime is $(CONTAINER_RUNTIME)"; \
		$(CONTAINER_RUNTIME) build --target devcontainer -t onboard .; \
	else \
		echo "[buildx] Building devcontainer with cache to/from .buildcache and loading image locally"; \
		docker buildx build \
			--target devcontainer \
			-t onboard \
			--cache-from=type=local,src=.buildcache \
			--cache-to=type=local,dest=.buildcache,mode=max \
			--load \
			.; \
	fi

start: buildx
	$(CONTAINER_RUNTIME) run --rm -d --name onboard_prod_run -p 9830:9830 onboard:prod

up: buildx
	$(CONTAINER_RUNTIME) run --rm --name onboard_prod_run -p 9830:9830 onboard:prod

down:
	$(CONTAINER_RUNTIME) stop onboard_prod_run

logs:
	$(CONTAINER_RUNTIME) logs onboard_prod_run -f


restart: buildx down start

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

# Display version and environment info
version:
	@echo "=============================================="
	@echo "Semantic Version: $(SEMANTIC_VERSION)"
	@echo "Host IP: $(HOSTIP)"
	@if [ "$$USER" != "anvil" ]; then echo "Detected OS: $(DETECTED_OS)"; fi
	@if [ "$$USER" != "anvil" ]; then echo "Container Runtime: $(CONTAINER_RUNTIME)"; fi
	@if [ "$$USER" = "anvil" ]; then echo "$(shell python --version 2>&1)"; fi
	@echo ""

integration-test:
	@echo "Running integration tests..."
	uv run pytest tests/integration -q || true

# -------------------------------
# Docker build benchmarking and testing
# -------------------------------
.PHONY: build-bench build-bench-dev test-build test-build-prod test-build-dev

build-bench: .env
	@echo "=== PRODUCTION BUILD BENCHMARK ==="
	@echo "Build context size:"
	@tar -cf - . 2>/dev/null | wc -c | awk '{printf "%.2f MB\n", $$1/1024/1024}'
	@echo ""
	time $(CONTAINER_RUNTIME) build -t onboard:bench-prod --target production .
	@echo ""
	@echo "Production image size: $$($(CONTAINER_RUNTIME) images onboard:bench-prod --format '{{.Size}}')"

build-bench-dev: .env
	@echo "=== DEVCONTAINER BUILD BENCHMARK ==="
	@echo "Build context size:"
	@tar -cf - . 2>/dev/null | wc -c | awk '{printf "%.2f MB\n", $$1/1024/1024}'
	@echo ""
	time $(CONTAINER_RUNTIME) build -t onboard:bench-dev --target devcontainer .
	@echo ""
	@echo "Devcontainer image size: $$($(CONTAINER_RUNTIME) images onboard:bench-dev --format '{{.Size}}')"

test-build-prod: .env
	@echo "=== Testing production build ==="
	$(CONTAINER_RUNTIME) build -t onboard:test-prod --target production .
	$(CONTAINER_RUNTIME) run --rm onboard:test-prod uv --version
	$(CONTAINER_RUNTIME) run --rm onboard:test-prod python --version
	@echo "Production build test PASSED"

test-build-dev: .env
	@echo "=== Testing devcontainer build ==="
	$(CONTAINER_RUNTIME) build -t onboard:test-dev --target devcontainer .
	$(CONTAINER_RUNTIME) run --rm onboard:test-dev uv --version
	$(CONTAINER_RUNTIME) run --rm onboard:test-dev python --version
	$(CONTAINER_RUNTIME) run --rm onboard:test-dev which claude
	$(CONTAINER_RUNTIME) run --rm onboard:test-dev claude --version
	@echo "Devcontainer build test PASSED"

test-build: test-build-prod test-build-dev
	@echo ""
	@echo "=== ALL BUILD TESTS PASSED ==="
