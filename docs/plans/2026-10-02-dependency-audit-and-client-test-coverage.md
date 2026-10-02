# Dependency Audit and Client Test Coverage Plan

**Goal:** Triage dependency-update noise with a security-first workflow, enforce authentication at each public search method, then add focused unit coverage for the sighting and encounter client APIs without requiring a running Wildbook server.

**Context:** pywildbook has a small runtime dependency surface (`requests`) and a much larger optional notebook dependency surface. Recent sighting methods were added as user-facing wrappers over the Wildbook occurrence endpoints, but tests do not yet assert their endpoint behavior. All public search methods delegate to `_search()`, which already enforces authentication, but the public methods lack their own `_requires_auth` guard. Encounter methods have similarly thin direct coverage.

**Out of scope for this plan:** Updating README API Reference entries for `search_sightings()` and `get_sighting()`. Track that as a separate documentation activity so dependency/test work remains focused.

---

## Task 1: Dependency Triage and Audit Workflow

**Purpose:** Decide which Dependabot suggestions are security-relevant, which are useful maintenance, and which can be closed as churn.

**Files likely involved:**
- `pyproject.toml`
- `uv.lock`
- `.github/dependabot.yml` if adding or tuning Dependabot configuration
- `.github/workflows/ci.yml` if adding audit to CI

- [x] Inventory current dependency update PRs or alerts.
  - Group them by runtime, dev tooling, notebook extras, and GitHub Actions.
  - Runtime starts with `requests` and its transitive dependencies.
  - Notebook extras include the Jupyter stack and should be treated separately from the importable client library.

- [x] Run `uv audit` locally against the current lockfile.
  - First run the default audit to include extras and dependency groups.
  - Then run narrower audits that exclude notebook extras and/or dev groups if needed to separate runtime risk from optional tooling risk.
  - Record which advisories apply to runtime code versus optional local tooling.

- [x] Decide disposition for each Dependabot item.
  - Keep and merge security fixes that affect runtime or CI.
  - Batch low-risk dev and notebook updates when they reduce repeated Dependabot churn.
  - Close updates that are superseded by a broader lock refresh or do not apply to supported install paths.

- [x] Consider adding a regular audit workflow.
  - Prefer a lightweight CI job or scheduled workflow only if the output is actionable.
  - If audit noise is mostly notebook extras, document how to run focused runtime audits rather than blocking normal CI on optional dependencies.

- [ ] Verify dependency changes.
  - `uv sync`
  - `uv run pytest`
  - `uv run ruff check`
  - `uv audit` after the lockfile is updated

### Task 1 Findings (2026-10-02)

- GitHub has 12 open Dependabot PRs: `requests` (#4), `pytest` (#5), `notebook` (#10), `urllib3` (#17), `idna` (#20), `tornado` (#22), `bleach` (#23), `jupyter-server` (#24), `soupsieve` (#26), `mistune` (#27), `setuptools` (#28), and `jupyterlab` (#29). No open Dependabot issues or GitHub Actions update PRs were found. There is no checked-in `.github/dependabot.yml`.
- The default `uv audit` reported 120 advisory records across the lockfile. The focused runtime audit (`uv audit --no-extra notebook --no-dev`) reported 14 records in `requests`, `idna`, and `urllib3`. The dev-only audit reported two records for `pytest`. Multiple records are aliases for the same underlying advisories.
- All 12 PRs map to dependencies flagged by the audit, so none should be closed as unneeded churn. Prioritize runtime bumps: `requests` to at least 2.33.0, `idna` to 3.15, and `urllib3` to at least 2.8.0. PR #17 targets 2.7.0 and would leave advisories unresolved.
- `pytest` 9.0.3 and `setuptools` 83.0.0 address the current findings for those packages.
- Notebook stack PR targets need refreshing before they can clear the current findings: `notebook` at least 7.6.3, `jupyter-server` at least 2.21.0, `jupyterlab` at least 4.5.11, `tornado` at least 6.5.9, and `soupsieve` at least 2.9.0. The proposed bumps for `bleach` 6.4.0 and `mistune` 3.3.0 address currently fixable findings, though OSV reports an unfixed Bleach advisory.
- Defer making `uv audit` a blocking CI check until the current findings are resolved and the behavior of the experimental command is better established. After updating dependencies, add a focused runtime audit to CI; assess a scheduled full-lock audit separately so optional notebook findings remain visible without blocking client-only changes.
- No dependency files have been changed as part of task 1; the existing local `uv.lock` modification is untouched. Run the listed sync/test/lint/audit verification after choosing and applying dependency updates.

---

## Task 2: Add Direct Tests for Search Resource Methods

**Purpose:** Cover endpoint routing, request bodies, query parameters, and authentication requirements for search methods. This task should also expose and fix the missing authentication guard on `search_sightings()`.

**Files likely involved:**
- `src/pywildbook/client.py`
- `tests/test_client.py`

- [x] Add tests for unauthenticated search methods.
  - `search_encounters()` raises `NotAuthenticatedError`.
  - `search_individuals()` raises `NotAuthenticatedError`.
  - `search_sightings()` raises `NotAuthenticatedError`.

- [x] Add direct authentication guards to public search methods.
  - Add `@_requires_auth` to all three public search methods. Ordinary unauthenticated calls were already rejected by `_search()`; these guards make the contract explicit at each public entry point.
  - Re-run the focused unauthenticated search tests and confirm they pass.

- [x] Add endpoint and params tests for search methods.
  - `search_encounters()` posts to `/api/v3/search/encounter`.
  - `search_individuals()` posts to `/api/v3/search/individual`.
  - `search_sightings()` posts to `/api/v3/search/occurrence`.
  - All methods pass `from`, `size`, `sort`, and `sortOrder` correctly.
  - Unwrapped queries are wrapped in `{"query": ...}`.
  - Already wrapped queries are not double-wrapped.

- [x] Keep the test setup direct and avoid unnecessary helpers.
  - The endpoint cases share one parameterized test, so extracting a helper would not reduce meaningful duplication.
  - Endpoint expectations remain visible in the test.

- [x] Run focused tests first.
  - `uv run pytest tests/test_client.py -v`

### Task 2 Findings (2026-10-02)

- Added explicit authentication checks to `search_encounters()`, `search_individuals()`, and `search_sightings()`. Because the current `_search()` helper already has the decorator, the unauthenticated request was already blocked in normal use; the public-method tests replace that helper to confirm each entry point enforces its own guard.
- Added parameterized endpoint, wrapped query body, pagination, and sort assertions for all three search methods. Existing tests continue to cover query wrapping and already-wrapped queries.
- The focused client tests pass (24 tests), the full suite passes (60 tests), and `uv run ruff check` passes.

---

## Task 3: Add Direct Tests for Get Resource Methods

**Purpose:** Cover endpoint routing and authentication requirements for individual resource fetches.

**Files likely involved:**
- `tests/test_client.py`

- [ ] Add unauthenticated access tests.
  - `get_encounter()` raises `NotAuthenticatedError`.
  - `get_individual()` raises `NotAuthenticatedError`.
  - `get_sighting()` raises `NotAuthenticatedError`.

- [ ] Add URL construction tests.
  - `get_encounter("enc-123")` gets `/api/v3/encounters/enc-123`.
  - `get_individual("ind-123")` gets `/api/v3/individuals/ind-123`.
  - `get_sighting("sight-123")` gets `/api/v3/occurrences/sight-123`.

- [ ] Add error propagation tests if useful.
  - The existing `get_encounter()` 404 test covers `_handle_response`; add `get_sighting()` 404 only if endpoint-specific behavior is worth locking down.

- [ ] Run focused tests first.
  - `uv run pytest tests/test_client.py -v`

---

## Task 4: Full Verification

**Purpose:** Confirm the dependency and test changes do not break the package.

- [ ] Run the full test suite.
  - `uv run pytest`

- [ ] Run linting.
  - `uv run ruff check`

- [ ] If dependency files changed, run audit again and record the result.
  - `uv audit`

- [ ] Review `git diff` for unrelated churn, especially in `uv.lock`.

---

## Separate Follow-Up: README API Reference Gap

The README includes a "Searching Sightings" section and examples for `get_sighting()`, but the API Reference method list omits:

- `search_sightings(query, from_=0, size=10, sort=None, sort_order=None) -> Dict`
- `get_sighting(sighting_id: str) -> Dict`

Handle this as a separate documentation cleanup activity after the dependency/test plan, or as a small standalone docs-only PR.
