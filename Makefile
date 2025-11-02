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
	$(CONTAINER_RUNTIME) build -t onboard:prod --target production .

build-dev: .env
	$(CONTAINER_RUNTIME) build --target devcontainer -t onboard .

start: down build
	$(CONTAINER_RUNTIME) run --rm -d --name onboard_prod_run -p 9830:9830 onboard:prod

up: down build
	$(CONTAINER_RUNTIME) run --rm --name onboard_prod_run -p 9830:9830 onboard:prod

down:
	$(CONTAINER_RUNTIME) stop onboard_prod_run

logs:
	$(CONTAINER_RUNTIME) logs onboard_prod_run -f


restart: build down start

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

.PHONY: test-if-py-changed
test-if-py-changed:
	@echo "[tests] Checking for Python changes..."
	@if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then \
	  changed=$$( (git diff --name-only HEAD; git ls-files --others --exclude-standard) | grep -E '\\.py$$' | sort -u ); \
	  if [ -n "$$changed" ]; then \
	    echo "[tests] Python changes detected:"; echo "$$changed"; \
	    uv run pytest; \
	  else \
	    echo "[tests] No Python changes detected; skipping pytest."; \
	  fi; \
	else \
	  echo "[tests] Not a git repo; running pytest to be safe."; \
	  uv run pytest; \
	fi

# -------------------------------
# Personalization utilities
#
# Vector store configuration (CHROMA_URL):
# - If CHROMA_URL starts with http(s)://, it's treated as a remote Chroma server URL.
# - Otherwise it's treated as a filesystem path for local on-disk persistence.
# - If unset, defaults to a local path under app/configs/.
#
# Common flow:
#   make ingest          # parse bookmarks/layout and (re)embed new items
#   make discover        # print a short summary and sample recommendations
#   make sync-clicks     # optional: import legacy CLICK_EVENTS
#   make topics-backfill # optional: update topics from historical clicks
# -------------------------------
.PHONY: ingest
ingest:
	@echo "[ingest] Ingesting bookmarks and layout into SQLite..."
	uv run python -m onboard.jobs.ingest_bookmarks
	@echo "[ingest] Running embedding refresher..."
	uv run python -m onboard.jobs.embed_refresher

.PHONY: discover
discover:
	@echo "[discover] Summarizing ingested data and recommendations..."
	uv run python -m onboard.jobs.discover

.PHONY: ctr-update
ctr-update:
	@echo "[ctr-update] Updating per-source CTR priors from recent clicks..."
	uv run python -m onboard.jobs.ctr_updater

.PHONY: hydrate-clicks
hydrate-clicks:
	@echo "[hydrate-clicks] Adding clicked URLs missing from items and embedding..."
	uv run python -m onboard.jobs.hydrate_clicked_items

.PHONY: topics-seed-bookmarks
topics-seed-bookmarks:
	@echo "[topics] Seeding topics from bookmark titles..."
	uv run python -m onboard.jobs.seed_topics_from_bookmarks

.PHONY: topics-from-titles
topics-from-titles:
	@echo "[topics] Populating topics from all item titles (small bumps)..."
	uv run python -m onboard.jobs.topics_from_titles

.PHONY: prune-topics
prune-topics:
	@echo "[topics] Pruning stopwords and generic terms from topics..."
	uv run python -m onboard.jobs.prune_topics

.PHONY: sync-clicks
sync-clicks:
	@echo "[sync-clicks] Syncing app CLICK_EVENTS to personalization click_events..."
	uv run python -m onboard.jobs.sync_clicks

.PHONY: topics-backfill
topics-backfill:
	@echo "[topics] Backfilling topics from click events..."
	uv run python -m onboard.jobs.topics_backfill
