# Tests

This directory contains unit tests for the wildbook-python-client package.

## Running Tests

### Install test dependencies

```bash
# Using uv
uv sync --extra dev

# Or with pip
pip install -e ".[dev]"
```

### Run all tests

```bash
# Using uv
uv run pytest

# Or directly
pytest

# With coverage
pytest --cov=wildbook_python_client --cov-report=html
```

### Run specific test files

```bash
pytest tests/test_queries.py
pytest tests/test_client.py
```

### Run with verbose output

```bash
pytest -v
```

## Test Structure

- `test_queries.py` - Tests for query helper functions
- `test_client.py` - Tests for WildbookClient class
- (Future) `test_integration.py` - Integration tests with running server

## Writing Tests

Tests use pytest and follow these conventions:

1. Test classes group related tests
2. Test methods start with `test_`
3. Use descriptive test names that explain what's being tested
4. Use mocking for HTTP requests to avoid needing a running server

## Coverage

To generate a coverage report:

```bash
pytest --cov=wildbook_python_client --cov-report=html
open htmlcov/index.html
```
