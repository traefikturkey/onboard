# Development-specific Makefile targets
# This file contains targets that are primarily useful in development environments

# read and include .devcontainer/.env exporting all variables
ifneq (,$(wildcard .devcontainer/.env))
	include .devcontainer/.env
	export
endif

# Initialize development environment
initialize: 
	@echo "Initializing development environment for $(DETECTED_OS)..."
	@echo "HOSTIP: $(HOSTIP)"
	@echo "HOSTIP=$(HOSTIP)" > .devcontainer/.env
	@echo "SEMANTIC_VERSION=$(SEMANTIC_VERSION)" >> .devcontainer/.env
	

# Install development dependencies (only if pyproject.toml changed)
uv.lock:
	uv sync --extra devmake 

# Run ALL tests (including broken ones for debugging)
test: uv.lock
	@echo "Running Behave BDD tests..."
	uv run behave tests/features -f progress --no-capture || exit 1
	@echo "Running ALL tests (excluding disabled tests)..."
	uv run pytest tests/ --ignore=tests/support --cov=app --cov-report=term-missing --cov-report=html:.htmlcov -v

# Run linting
# E203: whitespace before ':' (conflicts with black formatting)
# W503: line break before binary operator (conflicts with black formatting)
# E501: line too long (disabled to match black's line length handling)
lint: uv.lock
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
	rm -rf .coverage .htmlcov/ .pytest_cache/ .venv/
#	@rm -f /tmp/joyride-dns.pid 2>/dev/null || true
	@echo "Clean completed!"


# Start background onboard server
start-app:
	@echo "Starting onboard server in background..."
	@PYTHONPATH=app nohup uv run python run.py > /tmp/onboard.log 2>&1 & echo $$! > /tmp/onboard.pid
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

# Run Flask application locally (foreground)
run:
	@PYTHONPATH=app uv run python run.py


