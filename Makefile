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


.env:
	touch .env

build: .env
	$(CONTAINER_RUNTIME) build -t onboard:latest . 

build-dev: .env
	$(CONTAINER_RUNTIME) build --target devcontainer -t onboard .

start: build
	$(CONTAINER_RUNTIME) run --rm -d --name onboard -p 9830:9830 onboard

up: build
	$(CONTAINER_RUNTIME) run --rm -it --name onboard -p 9830:9830 onboard


down:
	$(CONTAINER_RUNTIME) stop onboard


restart: build down start

# -------------------------------
# Semantic version bumping logic
# -------------------------------
SEMANTIC_VERSION := $(shell git tag --list 'v*.*.*' --sort=-v:refname | head -n 1)
VERSION := $(shell echo $(SEMANTIC_VERSION) | sed 's/^v//')

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