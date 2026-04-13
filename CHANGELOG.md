# Changelog

All notable changes to `omaib-contracts` are documented here.
Follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [SemVer](https://semver.org/).

## [Unreleased]

## [0.3.0] — 2026-03-29

### Added
- **pip package data fix**: JSON schemas now ship as package data inside   `validators/schemas/` so `omaib-validate-adapter` works after a clean  `pip install omaib-contracts` (not just `pip install -e .`)
- **importlib.resources** schema resolution — works in both editable and wheel installs
- `validators/schemas/` directory: canonical schema location for installed package
- `templates/github-actions/validate-dap.yml` — GitHub Actions template for PI adapter repos; copy this into `.github/workflows/` to get automatic Gate 1 validation on every push and release
- `PI_ONBOARDING.md` — end-to-end guide covering: repo structure, local validation, CI setup, registration with OMAIB, and the failure handling model
- `pyproject.toml`: added `[tool.setuptools.packages.find]` and `[tool.setuptools.package-data]` for correct package discovery
- `pyproject.toml`: added classifiers, keywords, and project URLs for PyPI
- CI: `install-and-smoke` job — builds a wheel and runs the CLI from the installed wheel (no source) to catch package data regressions
- CI: `publish` job — publishes to PyPI on GitHub release via Trusted Publisher
- CI: Python 3.11 + 3.12 matrix on tests

### Changed
- `validate_adapter.py`: replaced `Path(__file__).parent.parent / "schemas"` with `importlib.resources.files("validators") / "schemas"` for pip compat
- `validate_adapter.py`: report uses `[OK]`/`[FAIL]`/`[MISS]` ASCII markers instead of Unicode symbols for broader terminal compatibility
- `validate_adapter.py`: optional files now display "recommended but not required" to clarify their status to PI teams

## [0.2.0] — 2026-03-26

### Added
- JSON Schema Draft 2020-12 schemas for all seven DAP file types
- `omaib-validate-adapter` CLI with structured gate readiness report
- `omaib-gate-status` CLI for gate-by-gate readiness breakdown
- Synthetic demo DAP (`examples/dap-synthetic-demo/`) — zero TBDs, CI fixture
- Templates for all DAP file types under `templates/`
- Tests: schema validity, validator regression, gate readiness
- `CITATION.cff` and `codemeta.json` for FAIR-compliant citation

## [0.1.0] — 2026-03-19

### Added
- Initial skeleton: `benchmark_contract.yaml` template and stub validator
