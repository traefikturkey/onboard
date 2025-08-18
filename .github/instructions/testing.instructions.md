---
description: "Testing standards and practices for Joyride DNS Service"
applyTo: "**/tests/**/*.py"
---

# Testing Standards

## Test Execution
- **Always use `uv run -m pytest` for running tests**
- **Never use pytest directly**
- Use `make test` for consistent test execution when available

## Test Strategy
- **Test public APIs only**
- Install missing dependencies with `uv add --dev` instead of adding skips
- If user wants tests deleted, delete them immediately
- When user deletes files: move skip() before imports in tests, delete unsalvageable tests

## Test Organization
- Tests in dedicated `tests/` directory
- Aim for >90% code coverage on critical paths
- Use pytest fixtures and descriptive test names

## Test Structure
```python
def test_health_endpoint_returns_correct_status_when_service_is_running(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'
```

## Import Pattern
```python
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
```

## Test Types
- Unit tests for business logic
- Integration tests for endpoints
- Mock external dependencies
- Use factories or fixtures, avoid hardcoded test data

### Integration Testing
- Test real DNS resolution with `dig` commands
- Use Make targets for complex integration scenarios

## Coverage
- Aim for >90% coverage on critical paths
- Coverage reports in `.htmlcov/`
- Use `make test` for consistent test execution
