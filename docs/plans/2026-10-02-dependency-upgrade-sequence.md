# Dependency Upgrade Sequence

**Goal:** Resolve actionable dependency advisories in small, reviewable batches, prioritizing runtime dependencies while containing compatibility risk in the optional notebook stack.

**Scope:** This plan sequences dependency updates identified in the dependency audit. It does not authorize applying the upgrades as part of this planning task. Each implementation task is to be handled separately, with user review before proceeding to the next task.

**Baseline:** Targets below reflect the latest releases/advisory fixes checked on 2026-10-02. Use the applicable target when it remains within the risk category described; do not jump major versions or unrelated dependency ranges as part of these updates.

## Risk Summary

| Risk | Dependencies | Target | Rationale |
| --- | --- | --- | --- |
| Low | `requests` | `2.34.2` | Latest patch/minor line target; exercise the client request and response paths. |
| Low | `idna` | `3.20` | Fixes the reported denial-of-service advisory without a major-version change. |
| Low | `pytest` | `9.0.3` | Fixes the reported advisory while staying on the existing 9.0 line; do not combine with a move to 9.1. |
| Low | `anyio` | `4.14.2` on Python `<3.14`; `4.15.1` on Python `>=3.14` | Resolver-selected 4.x releases resolve the audited findings; transitive/optional, with no corresponding Dependabot PR. |
| Medium | `urllib3` | `2.8.0` | Resolves current findings, but includes HTTPS forwarding-proxy TLS behavior changes. Verify configured proxy behavior where applicable. |
| Medium | `mistune` | `3.3.4` | Current 3.x release addresses findings in the optional notebook/parser graph; exercise notebook rendering/import paths. |
| Medium | `soupsieve` | `2.10` | Current 2.x release covers the current audit findings, including newer ReDoS advisories; optional HTML/parser dependency. |
| Medium | Jupyter Server, Tornado, JupyterLab, Notebook | `2.21.1`, `6.5.10`, `4.6.4`, `7.6.3` | Security/maintenance updates are appropriate, but these packages form a coupled optional stack. Notebook `7.6.3` requires the JupyterLab 4.6 line; Tornado's static-file symlink behavior and Jupyter Server compatibility warrant a stack-level smoke test. |
| Medium, lifecycle concern | `bleach` | `6.4.0` | Clears the current audit findings, but upstream identifies 6.4.0 as its final release with no future security fixes. Track replacement/removal separately. |

Risk describes expected change/validation effort, not advisory severity. Prioritize security-relevant changes even when validation risk is medium.

## Task 1: Runtime Baseline Patches

**Packages:** `requests` to `2.34.2`; `idna` to `3.20`.

- [x] Update the two runtime dependency targets/lock resolutions only.
- [x] Review the resulting `uv.lock` diff for unrelated upgrades.
- [x] Run the client unit tests and lint checks.
- [x] Run the focused runtime audit and confirm these package findings are resolved.
- [x] Review client behavior against Requests 2.34.2, including normal session requests and response JSON handling. The project does not currently depend on specialized Requests typing behavior.

### Task 1 Results (2026-10-02)

- `uv lock --upgrade-package requests --upgrade-package idna` updated only these locked packages: Requests `2.32.5` to `2.34.2`, and idna `3.11` to `3.20`. The resolver's current idna release is newer than the original `3.15` target; it remains within the same major version and addresses the audited finding.
- No `pyproject.toml` constraint change was needed: the runtime Requests constraint already permits the resolved version, and idna is transitive.
- The lockfile diff contains only the two selected packages.
- `uv run pytest tests/test_client.py -v`: 30 passed. This exercises the normal client session request and JSON response handling against Requests `2.34.2`.
- `uv run ruff check .`: passed.
- `uv audit --locked --no-extra notebook --no-dev` reports no findings for Requests or idna. It exits non-zero because the separately planned `urllib3` update remains outstanding, with 10 advisory records for `urllib3 2.6.3`.

Keep `urllib3` out of this batch so its proxy-related behavior change has a separate review and validation step.

## Task 2: `urllib3` Runtime Update

**Package:** `urllib3` to `2.8.0`.

- [x] Update and lock `urllib3` independently of other dependency groups.
- [x] Inspect repository application and deployment configuration for HTTPS forwarding proxies or custom proxy TLS settings.
- [x] Run the client unit suite, focusing on session setup, GET/POST requests, and error handling.
- [x] Check for repository-documented HTTPS proxy support; retain deployment proxy validation as a release caveat because deployment configuration is not available here.
- [x] Run the focused runtime audit and confirm the `urllib3` findings are resolved.

### Task 2 Results (2026-10-02)

- `uv lock --upgrade-package urllib3` updated only `urllib3`, from `2.6.3` to `2.8.0`.
- No explicit proxy or custom proxy-TLS configuration appears in the client, tests, examples, or repository documentation. The client uses `requests.Session()`, which may inherit proxy configuration from its runtime environment; no deployment environment was available to test.
- `uv run pytest tests/test_client.py -v`: 30 passed, covering client session setup and mocked GET/POST behavior.
- `uv run ruff check .`: passed.
- `uv audit --locked --no-extra notebook --no-dev`: passed with no known vulnerabilities or adverse project statuses in the focused runtime dependency set.
- Before release, validate HTTPS forwarding-proxy behavior if the deployment configures one, particularly any custom proxy TLS settings.

## Task 3: Optional Notebook Stack as a Cohort

**Packages:** Jupyter Server `2.21.1`, Tornado `6.5.10`, JupyterLab `4.6.4`, Notebook `7.6.3`.

- [x] Update the four packages together. Use the JupyterLab 4.6 line because Notebook 7.6.3 does not resolve with JupyterLab 4.5.
- [x] Resolve and review the lockfile as a cohort; accept only resolver-required transitive changes.
- [x] Install/sync the notebook extra with the lockfile enforced.
- [x] Run core tests and a notebook-extra smoke check: import the notebook/Jupyter packages and start the relevant server command far enough to verify initialization.
- [x] Review any static-file serving behavior relied on by examples, particularly symlinks outside the served root.
- [x] Audit the notebook extra and record any advisory that remains.

Notebook `7.6.3` requires the JupyterLab 4.6 line, so the initially proposed JupyterLab `4.5.11` target could not be used with it. The user chose JupyterLab `4.6.4` to take the Notebook security fix. Jupyter Server `2.21.1` includes the Tornado 6.5.9+ compatibility adjustment; Tornado `6.5.10` stays on the same minor series.

### Task 3 Results (2026-10-02)

- `uv lock --upgrade-package jupyter-server --upgrade-package tornado --upgrade-package jupyterlab --upgrade-package notebook` resolved Jupyter Server `2.21.1`, Tornado `6.5.10`, JupyterLab `4.6.4`, and Notebook `7.6.3`. The resolver also added `jupyter-builder 1.2.3`, required by the JupyterLab 4.6 dependency graph.
- `uv sync --locked --extra notebook` completed successfully.
- `uv run --locked --extra notebook pytest`: 66 passed.
- A local Jupyter Server startup smoke check loaded the `jupyterlab`, `notebook`, Jupyter LSP, terminal, and notebook shim extensions, then shut down cleanly. The server was bound to `127.0.0.1` for the check.
- The examples and README contain no symlinks or custom static-file serving references.
- `uv audit --locked --no-dev` reports no findings for Jupyter Server, Tornado, JupyterLab, or Notebook. It reports 47 advisory records remaining in `anyio`, `bleach`, `mistune`, and `soupsieve`; those are tracked under Task 4, and Bleach has one advisory with no known fix.

## Task 4: Optional Parser and Development Dependencies

**Packages:** `mistune` `3.3.4`, `soupsieve` `2.10`, `bleach` `6.4.0`, `pytest` `9.0.3`, `anyio` `4.14.2` for Python `<3.14` and `4.15.1` for Python `>=3.14`.

`setuptools` was removed from the resolved graph by the JupyterLab 4.6 update, so do not add it back solely to apply the previous `84.0.0` target.

- [x] Apply updates to the relevant optional/development dependency graph, keeping `pytest` on 9.0.x.
- [x] Review lockfile changes to confirm unrelated packages were not broadly refreshed.
- [x] Run the full test suite and lint checks.
- [x] Exercise notebook/parser imports or rendering if those paths are available in the repository's examples/tests.
- [x] Run the full locked audit and record any remaining advisory.
- [x] Record a separate follow-up to evaluate replacing/removing Bleach; do not expand this update batch into a parser migration.

### Task 4 Results (2026-10-02)

- Selective lock refresh updated Bleach `6.3.0` to `6.4.0`, Mistune `3.2.0` to `3.3.4`, SoupSieve `2.8.3` to `2.10`, pytest `9.0.2` to `9.0.3`, and AnyIO `4.13.0` to `4.14.2` for Python `<3.14`; the lock resolves AnyIO `4.15.1` for Python `>=3.14`.
- Added the dev constraint `pytest>=9.0.3,<9.1` to stay on the 9.0 line as planned. `setuptools` is not present in the final resolved graph after the JupyterLab update and was not reintroduced.
- `uv sync --locked --extra notebook` completed successfully.
- `uv run --locked --extra notebook pytest`: 66 passed.
- `uv run --locked --extra notebook ruff check .`: passed.
- A parser smoke check passed for Mistune HTML rendering, Bleach sanitization, and SoupSieve selector matching.
- `uv audit --locked`: passed with no known vulnerabilities or adverse project statuses in 115 packages. The earlier Bleach `6.3.0` no-fix advisory is no longer reported for `6.4.0`; upstream says `6.4.0` is the final release and no further security fixes will be published.

### Separate Follow-Up: Bleach Lifecycle

Evaluate removing/replacing Bleach and its `html5lib` dependency in a separate task. Keep this out of the dependency bump batch; there are no active findings in the current locked audit, but the library will receive no future security releases.

## Task 5: Final Audit and Report

- [x] Run the project's full test suite and lint checks after all approved batches.
- [x] Run the runtime-focused and full locked audits; distinguish runtime findings from optional notebook/development findings.
- [x] Confirm the lockfile is reproducible with locked sync and inspect the complete dependency diff.
- [x] Record remaining risks, affected install paths, and planned dispositions.

### Task 5 Results (2026-10-02)

- `uv lock --check`: passed; resolved 116 packages without changing the lock.
- `uv sync --locked --extra notebook`: passed; checked all 111 installed packages against the lock.
- `uv run --locked --extra notebook pytest`: 66 passed.
- `uv run --locked --extra notebook ruff check .`: passed.
- `uv audit --locked --no-extra notebook --no-dev`: no known vulnerabilities or adverse project statuses in the five-package runtime set.
- `uv audit --locked`: no known vulnerabilities or adverse project statuses in 115 packages across the full lock.
- Reviewed `git diff bd9b134..HEAD`: dependency changes are limited to the planned package updates, the pytest 9.0 constraint, JupyterLab's resolver-required `jupyter-builder`, and marker/typing-extension lock entries for supported Python versions. `git diff --check bd9b134..HEAD` passed.
- No active audit findings remain. Bleach's lack of future security releases remains a maintenance lifecycle concern; its replacement/removal evaluation is tracked separately above.
- Deployment-specific caveat: validate `urllib3 2.8.0` HTTPS forwarding-proxy behavior before release if a deployment uses a proxy or custom proxy TLS settings. The repository contains no explicit proxy configuration, and no deployment environment was available for this check.

## Separate Documentation Follow-Up

The README API Reference gap for `search_sightings()` and `get_sighting()` remains a separate documentation activity, as recorded in `2026-10-02-dependency-audit-and-client-test-coverage.md`. It is not part of the dependency upgrade work.
