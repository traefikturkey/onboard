# Development-specific Makefile targets
# This file contains targets that are primarily useful in development environments

# read and include .devcontainer/.env exporting all variables
ifneq (,$(wildcard .devcontainer/.env))
	include .devcontainer/.env
	export
endif

# GPU detection helper
detect-gpu:
	@if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then \
		echo "true"; \
	elif command -v lspci >/dev/null 2>&1 && lspci 2>/dev/null | grep -i nvidia >/dev/null 2>&1; then \
		echo "true"; \
	else \
		echo "false"; \
	fi

# Initialize development environment
initialize:
	@echo "Initializing development environment for $(DETECTED_OS)..."
	@echo "HOSTIP: $(HOSTIP)"
	@GPU_AVAILABLE=$$($(MAKE) -s detect-gpu); \
	echo "GPU_AVAILABLE: $$GPU_AVAILABLE"; \
	touch .env; \
	touch .devcontainer/.env; \
	echo "HOSTIP=$(HOSTIP)" > .devcontainer/.env; \
	echo "SEMANTIC_VERSION=$(SEMANTIC_VERSION)" >> .devcontainer/.env; \
	echo "GPU_AVAILABLE=$$GPU_AVAILABLE" >> .devcontainer/.env

# One-step container setup invoked by devcontainer postCreateCommand
setup-container:
	@echo "Running entrypoint scripts..."
	@for script in .devcontainer/entrypoint.d/*.sh; do \
			echo "Running $$script"; \
			bash "$$script" || echo "entrypoint script failed: $$script"; \
	done
	@echo "Entrypoint scripts completed."


# Install development dependencies (only if pyproject.toml changed)
uv.lock:
	uv lock
	uv sync --dev --all-packages

# Run Flask application locally (foreground)
run:
	@PYTHONPATH=app uv run gunicorn run:app -b 0.0.0.0:$(ONBOARD_PORT)

# Run ALL tests (including broken ones for debugging)
test: uv.lock
	@echo "Running Behave BDD tests..."
	@if uv run --all-packages python -c 'import behave' >/dev/null 2>&1; then \
		uv run --all-packages behave tests/features -f progress --no-capture || exit 1; \
	else \
		echo "behave not installed in uv environment, skipping BDD tests"; \
	fi
	@echo "Running ALL tests (excluding disabled tests)..."
	# Run pytest but explicitly exclude integration tests during the regular test run
	uv run pytest tests/ --ignore=tests/support --ignore=tests/integration \
		--cov=app --cov-report=term-missing --cov-report=html:.htmlcov -v

# Run full test suite including integration tests. This target depends on the
# regular 'test' target so unit/BDD tests run first, then integration tests run
# afterwards.
test-all: test
	@echo "Running integration tests..."
	uv run pytest -m integration tests/integration

# Run linting
# E203: whitespace before ':' (conflicts with black formatting)
# W503: line break before binary operator (conflicts with black formatting)
# E501: line too long (disabled to match black's line length handling)
lint: format
	uv run flake8 app tests --extend-ignore=E203,W503,E501
	@echo "Linting completed successfully!"

# Format code
format: uv.lock
	@echo "Formatting code with black..."
	uv run black app tests
	@echo "Organizing imports with isort..."
	uv run isort app tests --profile black
	@echo "Removing trailing whitespace..."
	find app tests -name "*.py" -exec sed -i 's/[[:space:]]*$$//' {} \;
	@echo "Code formatting completed!"

# Clean Python cache files
clean:
	@echo "Cleaning Python cache files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage .htmlcov/ .pytest_cache/
	@echo "Clean completed!"

uv-update:
	uv lock --upgrade && uv sync --dev

deptry:
	@echo "Checking for production dependencies issues..."
	@uv run deptry ./app
	@echo "Checking for development dependencies issues..."
	@uv run deptry . --ignore-notebooks

# Start background onboard server
start-app:
	@echo "Starting onboard server in background..."
	@PYTHONPATH=app nohup uv run gunicorn run:app -b 0.0.0.0:$(ONBOARD_PORT) --log-file /tmp/onboard.log 2>&1 & echo $$! > /tmp/onboard.pid
	@echo "Onboard server started with PID: $$(cat /tmp/onboard.pid)"
	@echo "Logs available at: /tmp/onboard.log"

# Stop background onboard server
stop-app:
	@if [ -f /tmp/onboard.pid ]; then \
		echo "Stopping onboard server with PID: $$(cat /tmp/onboard.pid)"; \
		kill -TERM $$(cat /tmp/onboard.pid) 2>/dev/null || true; \
		rm -f /tmp/onboard.pid; \
		echo "Onboard server stopped"; \
	else \
		echo "No onboard server PID file found"; \
	fi

sync-configs:
	unison app/defaults ${UNISON_SSH_URL}//apps/onramp/etc/onboard/ -path bookmarks_bar.json -path layout.yml
	unison app/configs ${UNISON_SSH_URL}//apps/onramp/etc/onboard/ -path bookmarks_bar.json -path layout.yml
