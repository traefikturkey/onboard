---
description: "Python coding standards and best practices for Joyride DNS Service"
applyTo: "**/*.py"
---

# Python Development Standards

## Project Tooling (uv-first)

- **Always use uv for Python projects**: `uv run -m pytest`, `uv add <library>`, `uv run`
- **Never use pytest or python directly**
- Package installation:
  - Production: `uv add <library_name>`
  - Development: `uv add --dev <library_name>`
  - Notebook dependencies: `uv add --group notebook <library_name>`
- **Never use direct package installation tools**
- Always verify files exist before suggesting fixes
- When user deletes files: update imports, move skip() before imports in tests, delete unsalvageable tests
- **Never recreate deleted files**

## Code Style and Formatting

- Follow **PEP 8** style guide with Black formatter (line length 88)
- Maintain proper indentation (use 4 spaces for each level of indentation)
- Two blank lines before top-level function definitions
- Use isort with Black profile for imports
- Ensure lines do not exceed 88 characters (Black standard)
- Place function and class docstrings immediately after the `def` or `class` keyword
- Use blank lines to separate functions, classes, and code blocks where appropriate

## Type Safety and Annotations

- **Strong type hints** for all parameters and return values
- Use the `typing` module for type annotations (`List[str]`, `Dict[str, int]`)
- Prefer modern generic types (`list[str]`, `dict[str, Any]`) over legacy forms
- Leverage `typing` module for complex types (`Union`, `Optional`, `Literal`)
- **Use Pydantic** for data validation and serialization whenever possible
- Use dataclasses for simple data containers when Pydantic is overkill

## Naming Conventions

- **CRITICAL: Avoid Test Name Conflicts** - Never name classes with "Test" prefix unless they are actual pytest test classes
- Use descriptive names: `MockComponent`, `HelperClass`, `UtilityFunction` instead of `TestComponent`
- Class names: PascalCase (`UserService`, `DatabaseConnection`)
- Function/variable names: snake_case (`get_user_data`, `connection_pool`)
- Constants: UPPER_SNAKE_CASE (`MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- Private methods: leading underscore (`_internal_method`)
- Python filenames should be the snake_case version of the primary class they contain. For example, `DNSRecordHandler` -> `dns_record_handler.py`, `ComponentFactory` -> `component_factory.py`. If a module intentionally contains multiple classes or is functional-only, name the file for the dominant class or the module purpose, respectively.

## Documentation and Comments

- Write clear and concise comments for each function
- Ensure functions have descriptive names and include type hints
- Provide docstrings following PEP 257 conventions
- For algorithm-related code, include explanations of the approach used
- Handle edge cases and write clear exception handling
- For libraries or external dependencies, mention their usage and purpose in comments
- Always prioritize readability and clarity

## Error Handling

- Use specific exception types
- Provide meaningful error messages
- Use Python's logging module with structured logging
- Handle edge cases and write clear exception handling
- Account for common edge cases like empty inputs, invalid data types, and large datasets
- **Never remove public methods/properties to fix lints - add type hints instead**
- Always mention if behavior might change

## Example Pattern

```python
from pydantic import BaseModel
from typing import Any

class ServiceStatus(BaseModel):
    """
    Represents the status of a service with validation.
    
    Attributes:
        status: Current status of the service
        service: Name of the service
        timestamp: ISO formatted timestamp
        details: Optional additional status details
    """
    status: str
    service: str
    timestamp: str
    details: dict[str, Any] | None = None

def get_service_status(service_name: str) -> ServiceStatus:
    """
    Retrieve the current status of a service.
    
    Parameters:
        service_name (str): The name of the service to check.
    
    Returns:
        ServiceStatus: The current status information for the service.
        
    Raises:
        ServiceError: If the service check fails.
    """
    try:
        return ServiceStatus(
            status="healthy", 
            service=service_name,
            timestamp=datetime.now().isoformat()
        )
    except ServiceError as e:
        logger.error(f"Service check failed: {e}")
        raise
```

## Configuration Management

- Use classes for environment configs
- Load via `python-dotenv` for development
- Use `os.getenv()` with sensible defaults
- Separate development and production configurations
- Validate configuration at startup

## Network Services & Background Processing

- Use threading for background services (DNS server, Docker monitoring)
- Implement proper signal handling for graceful shutdown
- Use threading.Lock for shared resources
- Create PID files for process management in `/tmp/` for development
- Use proper cleanup with `atexit.register()`

### Service Integration Patterns

```python
# Signal handling for services
def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    cleanup_services()
    exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
```

### Web Framework Integration
- Check for JS framework conflicts when links/forms don't work
- Add `data-*-boost='false'` or equivalent to opt out of framework interception

## Flask Application Patterns

### Application Organization
- Structure with `app/` package using `__init__.py` exports
- Main Flask app in `app/main.py`
- Export app instance via `app/__init__.py`
- Use `run.py` as clean entry point
- Blueprint organization for route grouping
- Disable debug mode for background processes (`FLASK_DEBUG=false`)
- Implement health check endpoints (`/health`, `/status`)
- Use Pydantic for API response models

### API Response Format
```python
# Success response
{
    "data": {...},
    "meta": {
        "timestamp": "2025-08-01T12:00:00Z",
        "version": "1.0.0"
    }
}

# Error response
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid request parameters",
        "details": {...}
    }
}
```

## File and Import Management

- Fix imports by checking __init__.py files first
- When moving files: create new, update imports, delete old, commit all together
- Always verify file operations worked
- Keep app as proper Python package with `__init__.py` files
- Import pattern: `from app import app`
- Custom error handlers for consistent API responses
- Validate inputs early, fail fast with clear messages
- Break down complex functions into smaller, more manageable functions

## Testing and Quality

- Always include test cases for critical paths of the application
- Include comments for edge cases and the expected behavior in those cases
- Write unit tests for functions and document them with docstrings explaining the test cases
- Write code with good maintainability practices, including comments on why certain design decisions were made
- Write concise, efficient, and idiomatic code that is also easily understandable

## Code Quality Tools

- Black formatter (88 character line length)
- isort with Black profile
- flake8 linter
- mypy for type checking
- bandit for security scanning
