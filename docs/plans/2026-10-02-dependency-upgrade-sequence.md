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
| Low | `setuptools` | `84.0.0` | Current release within the existing major version; it is only present through the optional notebook dependency graph. |
| Low | `anyio` | `4.14.2` | Audit-identified patch-level security target; transitive/optional, with no corresponding Dependabot PR. |
| Medium | `urllib3` | `2.8.0` | Resolves current findings, but includes HTTPS forwarding-proxy TLS behavior changes. Verify configured proxy behavior where applicable. |
| Medium | `mistune` | `3.3.0` | Addresses current findings in the optional notebook/parser graph; exercise notebook rendering/import paths. |
| Medium | `soupsieve` | `2.9.0` | Covers the current audit findings, including newer ReDoS advisories; optional HTML/parser dependency. |
| Medium | Jupyter Server, Tornado, JupyterLab, Notebook | `2.21.1`, `6.5.10`, `4.5.11`, `7.6.3` | Security/maintenance updates are appropriate, but these packages form a coupled optional stack. Tornado's static-file symlink behavior and Jupyter Server compatibility warrant a stack-level smoke test. |
| Medium, residual risk | `bleach` | `6.4.0` | Fixes known fixable findings, but the project reports an unfixed advisory and Bleach is no longer maintained. Upgrade for the available fixes, record the residual finding, and track replacement/removal separately. |

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

**Packages:** Jupyter Server `2.21.1`, Tornado `6.5.10`, JupyterLab `4.5.11`, Notebook `7.6.3`.

- [ ] Update the four packages together, preserving the current JupyterLab 4.5 line rather than broadening to a new minor line.
- [ ] Resolve and review the lockfile as a cohort; do not manually pin transitive packages unless the resolver requires it.
- [ ] Install/sync the notebook extra with the lockfile enforced.
- [ ] Run core tests and a notebook-extra smoke check: import the notebook/Jupyter packages and start the relevant server command far enough to verify initialization.
- [ ] Review any static-file serving behavior relied on by examples, particularly symlinks outside the served root.
- [ ] Audit the notebook extra and record any advisory that remains.

The Jupyter Server target is `2.21.1` rather than the older Dependabot target because it includes the Tornado 6.5.9+ compatibility adjustment. Tornado's `6.5.10` target incorporates the current patch line while keeping the same minor series.

## Task 4: Optional Parser and Development Dependencies

**Packages:** `mistune` `3.3.0`, `soupsieve` `2.9.0`, `bleach` `6.4.0`, `pytest` `9.0.3`, `setuptools` `84.0.0`, `anyio` `4.14.2`.

- [ ] Apply updates to the relevant optional/development dependency graph, keeping `pytest` on 9.0.x.
- [ ] Review lockfile changes to confirm unrelated packages were not broadly refreshed.
- [ ] Run the full test suite and lint checks.
- [ ] Exercise notebook/parser imports or rendering if those paths are available in the repository's examples/tests.
- [ ] Run the full locked audit and record the remaining Bleach advisory separately; do not treat the audit as fully clean while that advisory is present.
- [ ] Create a separate follow-up to evaluate replacing/removing Bleach; do not expand this update batch into a parser migration.

## Task 5: Final Audit and Report

- [ ] Run the project's full test suite and lint checks after all approved batches.
- [ ] Run the runtime-focused and full locked audits; distinguish runtime findings from optional notebook/development findings.
- [ ] Confirm the lockfile is reproducible with locked sync and inspect the complete dependency diff.
- [ ] Record any unresolved advisory, its affected install paths, and the planned disposition.

## Separate Documentation Follow-Up

The README API Reference gap for `search_sightings()` and `get_sighting()` remains a separate documentation activity, as recorded in `2026-10-02-dependency-audit-and-client-test-coverage.md`. It is not part of the dependency upgrade work.
