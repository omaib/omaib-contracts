# omaib-contracts
[![CI](https://github.com/omaib/omaib-contracts/actions/workflows/ci.yml/badge.svg)](https://github.com/omaib/omaib-contracts/actions/workflows/ci.yml) [![codecov](https://codecov.io/gh/omaib/omaib-contracts/branch/main/graph/badge.svg)](https://codecov.io/gh/omaib/omaib-contracts) [![PyPI version](https://img.shields.io/pypi/v/omaib-contracts)](https://pypi.org/project/omaib-contracts/) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Shared schemas, validators, and Domain Adapter Pack (DAP) templates for the [OMAIB](https://omaib.github.io) benchmarking platform (CDRF-aligned).

`omaib-contracts` is the **interoperability contract** between PI teams and the OMAIB platform. It defines what a valid adapter looks like, ships the CLI validator, and provides templates for creating new adapters.

## What This Repo Contains

| Directory | Purpose |
|-----------|---------|
| `schemas/` | JSON Schema Draft 2020-12 schemas for all DAP file types (canonical, browsable) |
| `validators/` | CLI tools + package data (schemas shipped here for pip install) |
| `templates/` | Starter templates for new Domain Adapter Packs |
| `templates/github-actions/` | GitHub Actions workflow template for PI repos |
| `examples/dap-synthetic-demo/` | Fully valid reference DAP (zero TBDs, CI fixture) |
| `tests/` | Schema validity and validator regression tests |
| `PI_ONBOARDING.md` | End-to-end guide for PI teams setting up external adapter repos |

---

## For PI Teams — Quick Start

### 1. Install the validator

```bash
pip install omaib-contracts
```

### 2. Create your adapter directory

Run the scaffolding command in your repo root — this creates all six DAP files with the correct names in one step (no manual copy-and-rename required):

```bash
# In your adapter repo:
omaib-init-adapter omaib-adapter/ --slug <your-project-slug>
```

Or without slug substitution (fill adapter_id / benchmark_id manually afterward):

```bash
omaib-init-adapter omaib-adapter/
```

Fill in every field — replace all `<placeholder>` values and `TBD` entries.

If you prefer to copy templates manually:

```bash
git clone https://github.com/omaib/omaib-contracts.git
cp omaib-contracts/templates/*.yaml  omaib-adapter/
cp omaib-contracts/templates/*.json  omaib-adapter/
# Then rename files: remove the .template. suffix
```

### 3. Validate before tagging

```bash
omaib-validate-adapter omaib-adapter/
```

```
======================================================================
OMAIB Adapter Validation Report
Adapter: omaib-adapter/
======================================================================

  [OK] benchmark_contract.yaml
  [OK] data_profile.json
  [OK] governance_policy.yaml
  [OK] scorecard_schema.json

  Gate Readiness Score: 87.5%
  Gate 1 Ready:        YES
```

**Do not tag a release until `Gate 1 Ready: YES`.**

### 4. Check gate-by-gate status

```bash
omaib-gate-status omaib-adapter/
```

### 5. Add CI validation

Copy `templates/github-actions/validate-dap.yml` into your repo's `.github/workflows/`. This runs Gate 1 validation on every push and on release publication.

### 6. Register with OMAIB

Open an issue at `https://github.com/omaib/omaib-contracts/issues/new` with the title  `[PI Registration] <your-project-name>`.

See [PI_ONBOARDING.md](PI_ONBOARDING.md) for the complete guide.

### 7. Releasing updates (subsequent submissions)

After your initial registration, you do **not** need to re-register. Push a new tag and the platform picks it up automatically within 6 hours:

```bash
git tag -a v0.2.0 -m "Update adapter — revised governance policy"
git push origin v0.2.0
```

The platform will:
1. Detect the new tag on the next poll cycle
2. Fetch and validate the updated adapter
3. If Gate 1 passes: store a new immutable snapshot and update the live registry
4. If Gate 1 fails: open a GitHub issue in `omaib/omaib-adapter-registry` and keep the last valid snapshot live

You will only need to contact the OMAIB team again if you change your `adapter_id`, `adapter_path`, or repository URL — those require editing `registered_sources.yaml`.

---

## How the Platform Uses This Package

```
omaib-contracts (this repo)
  └── publishes: schemas + CLI validator

PI repo (github.com/<your-uni>/<your-project-name>)
  └── PIs run: pip install omaib-contracts && omaib-validate-adapter omaib-adapter/
  └── CI validates on every push and release

OMAIB platform (omaibench)
  └── polls registered PI repos every 6 hours
  └── runs same omaib-contracts validator at ingestion boundary
  └── stores immutable snapshot of each validated release
  └── serves validated view via API, dashboard, leaderboard
  └── if PI adapter fails: keeps last valid snapshot, notifies PI
```

---

## Requirements

- Python >= 3.11
- `jsonschema >= 4.21`
- `pyyaml >= 6.0`

These are installed automatically with `pip install omaib-contracts`.

## Install

```bash
pip install omaib-contracts
# OR,
pip install git+https://github.com/omaib/omaib-contracts.git
```

Or from source (development):

```bash
git clone https://github.com/omaib/omaib-contracts.git
cd omaib-contracts
pip install -e ".[dev]"
```

Development extras add `pytest >= 8.0` and `ruff >= 0.4`.

---

## Schemas

| Schema | Validates |
|--------|-----------|
| `benchmark_contract.schema.json` | `benchmark_contract.yaml` |
| `data_profile.schema.json` | `data_profile.json` |
| `governance_policy.schema.json` | `governance_policy.yaml` |
| `scorecard.schema.json` | `scorecard_schema.json` per adapter + platform scorecards |
| `run_manifest.schema.json` | Run reproducibility manifests |
| `trust_toolkit.schema.json` | `trust_toolkit.yaml` (CDRF-Trust) |
| `assurance_crosswalk.schema.json` | `assurance_crosswalk.yaml` (CDRF-Assure) |

Schemas use JSON Schema Draft 2020-12 and are versioned via `$id` URIs
(`https://omaib.github.io/schemas/{type}/v{N}.json`).

---

## FAIR Compliance

| Principle | Implementation |
|-----------|---------------|
| Findable  | Persistent `benchmark_id` URIs; `$id` on every schema; CITATION.cff |
| Accessible | Versioned JSON Schemas; documented access tiers; MIT licence |
| Interoperable | JSON Schema Draft 2020-12; ISO 8601 timestamps; SemVer |
| Reusable  | CITATION.cff; codemeta.json; MIT licence; SemVer releases |

---

## Running Tests

```bash
pip install -e ".[dev]"
pytest -v
```

The test suite includes:
- Schema self-validity (all schemas are valid JSON Schema Draft 2020-12)
- Validator regression (synthetic demo must pass Gate 1)
- Gate readiness computation
- Empty directory returns all files as missing

---

## Licence

MIT — see [LICENSE](LICENSE)

## Citation

See [CITATION.cff](CITATION.cff)
