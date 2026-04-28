# Contributing to pywildbook

Thank you for your interest in contributing to pywildbook. This project is a
Python client for the Wildbook v3 API and is maintained alongside the companion
R client, RWildbook.

## Getting Help

Use the Wild Me community forum for questions, discussion, and support:

- https://community.wildme.org/

Use GitHub Issues for actionable bug reports, feature requests, and work that
should be tracked by maintainers:

- https://github.com/WildMeOrg/pywildbook/issues

## Before You Start

Before opening a pull request:

1. Check the issue tracker for related work.
2. Open an issue before starting a pull request.
3. Keep pull requests focused on one bug fix, feature, or documentation update.
4. Remember that pywildbook and RWildbook should remain feature-equivalent.

For changes that add or alter public functionality, please consider whether the
same behavior also needs to be added to RWildbook.

## Development Setup

This project uses Python 3.11+, `uv`, `pytest`, and `ruff`.

```bash
git clone https://github.com/YOUR-USERNAME/pywildbook.git
cd pywildbook
git remote add upstream https://github.com/WildMeOrg/pywildbook.git
git fetch upstream
uv sync
```

Contributions should come from a fork of the repository. Create a feature branch
in your fork for each issue you work on.

For development tools:

```bash
uv sync --group dev
```

For notebook examples:

```bash
uv sync --extra notebook
```

If you work on notebooks, install the output-stripping filter once:

```bash
uv run nbstripout install
```

## Running Checks

Run the test suite:

```bash
uv run pytest
```

Run linting:

```bash
uv run ruff check .
```

Run coverage when making larger changes:

```bash
uv run pytest --cov=pywildbook --cov-report=term-missing
```

## Coding Conventions

Follow the existing project style:

- Use Python 3.11+ syntax and type hints where they make public behavior clearer.
- Keep the public API small and consistent with the current `WildbookClient` and
  query helper patterns.
- Use the custom exceptions in `src/pywildbook/exceptions.py` for client and API
  errors.
- Decorate client methods that require authentication with `_requires_auth`.
- Keep query helpers in `src/pywildbook/queries.py` and add tests for new helper
  behavior in `tests/test_queries.py`.
- Mock HTTP requests in unit tests. Do not require a running Wildbook server for
  ordinary unit tests.
- Mark tests that require a running Wildbook instance with
  `@pytest.mark.integration`.
- Avoid committing notebook outputs. The repository uses `nbstripout` for
  `.ipynb` files.

## Testing Expectations

Every behavior change should include tests. In general:

- Add query helper tests in `tests/test_queries.py`.
- Add client behavior tests in `tests/test_client.py`.
- Prefer small, focused tests that do not depend on network access.
- Keep existing tests passing.

## Documentation

Update documentation when user-facing behavior changes. This may include:

- `README.md`
- `TESTING.md`
- Example scripts in `examples/`
- Docstrings for public functions and classes

If a new feature changes the public API, document the same expected behavior in
the companion RWildbook work when that parallel change is made.

## Pull Requests

Pull requests should be opened from your fork against the WildMeOrg pywildbook
repository.

When opening a pull request:

1. Explain what changed and why.
2. Link the related issue.
3. Include the checks you ran, such as `uv run pytest` and
   `uv run ruff check .`.
4. Mention any follow-up needed in RWildbook for feature parity.
5. Keep unrelated formatting or refactoring out of the pull request.

Maintainers may ask for changes before merging. Please keep discussion focused
on the specific issue or pull request.

## Security and Credentials

Do not commit credentials, access tokens, cookies, or local `.env` files.
Wildbook credentials should be supplied with environment variables:

- `WILDBOOK_URL`
- `WILDBOOK_USERNAME`
- `WILDBOOK_PASSWORD`
