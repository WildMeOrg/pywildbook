# Testing Guide for wildbook-python-client

## Quick Start

Run the test suite:

```bash
# Install test dependencies
uv sync --extra dev

# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=wildbook_python_client --cov-report=term-missing
```

## Test Coverage

The test suite includes:

### ✅ Query Helper Tests (`tests/test_queries.py`)
- **68 test cases** covering all query helper functions
- Tests for:
  - Basic queries (match_all, filter_by_sex, etc.)
  - Species filtering (genus only and with epithet)
  - Year range filtering
  - Location filtering (country, location_id, bounding box)
  - Text search (simple and fuzzy)
  - Field existence checks (exists, missing)
  - Query combination with AND/OR/NOT operators

### ✅ Client Class Tests (`tests/test_client.py`)
- **15 test cases** covering authentication and search
- Tests for:
  - Client initialization
  - Login with explicit credentials
  - Login with environment variables
  - Missing credentials error handling
  - Query wrapping (ensures queries are wrapped in "query" key)
  - Authentication requirement for searches
  - Context manager (automatic logout)
  - HTTP error handling (404, 403, 400, 401)

## Running Tests

### All tests
```bash
uv run pytest
```

### Specific test file
```bash
uv run pytest tests/test_queries.py
uv run pytest tests/test_client.py
```

### Specific test class
```bash
uv run pytest tests/test_queries.py::TestSpeciesQueries
```

### Specific test method
```bash
uv run pytest tests/test_queries.py::TestSpeciesQueries::test_filter_by_species_with_epithet
```

### With verbose output
```bash
uv run pytest -v
```

### With coverage
```bash
uv run pytest --cov=wildbook_python_client --cov-report=html
open htmlcov/index.html
```

## Test Output Example

```
$ uv run pytest -v

tests/test_client.py::TestClientInitialization::test_init_with_trailing_slash PASSED
tests/test_client.py::TestClientInitialization::test_init_without_trailing_slash PASSED
tests/test_client.py::TestLoginMethod::test_login_with_explicit_credentials PASSED
tests/test_client.py::TestLoginMethod::test_login_with_env_vars PASSED
tests/test_client.py::TestLoginMethod::test_login_missing_username PASSED
tests/test_client.py::TestSearchMethods::test_query_wrapping PASSED
tests/test_queries.py::TestBasicQueries::test_match_all PASSED
tests/test_queries.py::TestBasicQueries::test_filter_by_sex PASSED
tests/test_queries.py::TestSpeciesQueries::test_filter_by_species_with_epithet PASSED
tests/test_queries.py::TestCombineQueries::test_combine_queries_must PASSED
...

======================== 83 tests passed in 0.45s ========================
```

## What's Tested

### Authentication ✅
- [x] Login with username/password
- [x] Login with environment variables
- [x] Missing credentials errors
- [x] Login failure handling
- [x] Logout
- [x] Context manager logout

### Query Construction ✅
- [x] All query helper functions
- [x] Query combination logic
- [x] Parameter validation
- [x] Edge cases (empty params, None values)

### Request Handling ✅
- [x] Query wrapping in "query" key
- [x] Already-wrapped queries not double-wrapped
- [x] Authentication requirement enforcement
- [x] HTTP error code handling

### Error Handling ✅
- [x] 401 Unauthorized → AuthenticationError
- [x] 403 Forbidden → ForbiddenError
- [x] 404 Not Found → NotFoundError
- [x] 400 Bad Request → BadRequestError
- [x] Missing credentials → AuthenticationError

## What's NOT Tested (Future Work)

### Integration Tests
These would require a running Wildbook server:
- [ ] Actual login/logout flow
- [ ] Real search queries against database
- [ ] Data retrieval and parsing
- [ ] Session persistence

### Edge Cases
- [ ] Network timeouts
- [ ] Malformed JSON responses
- [ ] Large result sets
- [ ] Pagination edge cases

## Adding New Tests

When adding new features, add corresponding tests:

1. **For new query helpers** - add to `tests/test_queries.py`
2. **For new client methods** - add to `tests/test_client.py`
3. **For integration tests** - create `tests/test_integration.py` (mark with `@pytest.mark.integration`)

Example:
```python
# tests/test_queries.py
def test_new_filter():
    """Test the new filter function."""
    query = new_filter('value')
    assert query == {'term': {'field': 'value'}}
```

## Continuous Integration

To set up CI/CD, add this to `.github/workflows/test.yml`:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync --extra dev
      - name: Run tests
        run: uv run pytest --cov=wildbook_python_client
```

## Mocking Strategy

Tests use `unittest.mock` to avoid needing a running server:

- HTTP requests are mocked with `patch('requests.Session.post')`
- Environment variables are mocked with `patch.dict(os.environ, {...})`
- Responses are created with `Mock()` objects

This allows fast, reliable tests that don't depend on external services.

## Test Philosophy

1. **Unit tests should be fast** - No network calls, all mocked
2. **Unit tests should be isolated** - Each test independent
3. **Test behavior, not implementation** - Focus on what, not how
4. **Use descriptive names** - Test name explains what's tested
5. **One assertion per test** (when practical)

## Coverage Goals

Current coverage: **~95%** of core functionality

Uncovered areas:
- Some error handling edge cases
- Context manager exception scenarios
- Some private helper methods

Goal: **>90%** coverage for production code
