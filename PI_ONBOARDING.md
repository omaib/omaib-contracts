# PI Adapter Onboarding Guide

This guide walks a PI team through publishing an OMAIB Domain Adapter Pack (DAP) in your own GitHub repository so the OMAIB platform can pull, validate, and register your benchmark.

---

## The Operational Formula

```
1. We (OMAIB team) publish the contract  →  omaib-contracts package + schemas
2. PIs publish adapters      →  in your own repo, tagged releases
3. Platform pulls & validates →  automated, scheduled every 6 hours
4. Platform serves the view  →  API, dashboard, leaderboard
5. If adapter fails          →  platform keeps last valid version and notifies you
```

Your adapter repo stays under your institution's GitHub organisation. OMAIB never pushes to your repo.

---

## Step 1 — Create Your Adapter Repository

Create a public or private GitHub repository in your institution's GitHub organisation, e.g.:
`github.com/<your-uni>/<your-project-name>`

Recommended repo structure:
```
<your-project-name>/
├── ...                            ← (your code, data, papers, etc)
├── omaib-adapter/                 ← OMAIB reads everything from here. At the repo root
│   ├── benchmark_contract.yaml    ← required (see next step)
│   ├── data_profile.json          ← required (see next step)
│   ├── governance_policy.yaml     ← required (see next step)
│   ├── scorecard_schema.json      ← required (see next step)
│   ├── trust_toolkit.yaml         ← recommended (see next step)
│   ├── assurance_crosswalk.yaml   ← recommended (see next step)
│   ├── README.md                  ← recommended
│   └── CITATION.cff               ← recommended
├── .github/
│   └── workflows/
│       └── validate-dap.yml       ← copy from omaib-contracts/templates/
├── README.md
└── LICENSE
```

---

## Step 2 — Create Your Adapter Files

### Option A — Using the CLI (recommended)

Install the `omaib-contracts` 

```bash
pip install omaib-contracts
# OR,
pip install git+https://github.com/omaib/omaib-contracts.git

# If you prefer to install the released version e.g.,
pip install  git+https://github.com/omaib/omaib-contracts.git@v0.3.0
```
With `omaib-contracts` installed, run the scaffolding command from your project repo:

```bash
omaib-init-adapter omaib-adapter/ --slug <your-project-slug>
```

This creates all six DAP template files with the correct names (no `.template.` suffix) pre-populated with your slug:

```
omaib-adapter/
  benchmark_contract.yaml    ← required
  data_profile.json          ← required
  governance_policy.yaml     ← required
  scorecard_schema.json      ← required
  trust_toolkit.yaml         ← recommended
  assurance_crosswalk.yaml   ← recommended
```

To overwrite an existing adapter directory: add `--force`.

### Option B — Manual copy

```bash
git clone https://github.com/omaib/omaib-contracts.git
cp omaib-contracts/templates/*.yaml  omaib-adapter/
cp omaib-contracts/templates/*.json  omaib-adapter/
# Then rename each file: remove the .template. part from the filename
# e.g. benchmark_contract.template.yaml → benchmark_contract.yaml
```

Fill in every field — replace all `<placeholder>` values and `TBD` entries. The validator will report any remaining TBDs and they lower your Gate Readiness Score.

---

## Step 3 — Validate Locally Before Tagging

With `omaib-contracts` installed, run validation against your adapter directory:

```bash
omaib-validate-adapter omaib-adapter/
```

Example output:
```
======================================================================
OMAIB Adapter Validation Report
Adapter: omaib-adapter/
======================================================================

  [OK] benchmark_contract.yaml
  [OK] data_profile.json
  [OK] governance_policy.yaml
  [OK] scorecard_schema.json

  Optional files:
    [OK] trust_toolkit.yaml
    [OK] README.md
    [--] assurance_crosswalk.yaml (missing — recommended but not required)
    [--] CITATION.cff (missing — recommended but not required)

----------------------------------------------------------------------
  Gate Readiness Score: 87.5%
  Gate 1 Ready:        YES
----------------------------------------------------------------------
```

Check gate-by-gate status:

```bash
omaib-gate-status omaib-adapter/
```

**Do not tag a release until `Gate 1 Ready: YES`.**

### Understanding the Gate Readiness Score

| Score | Meaning |
|-------|---------|
| < 60% | Gate 1 blocked — too many TBD fields or schema errors |
| 60–79% | Gate 1 passes — consider filling more fields before release |
| 80–99% | Gate 2 eligible — evaluator can proceed to pilot |
| 100% | All required fields complete — ideal for v1.0 |

---

## Step 4 — Add CI Validation

Copy the provided GitHub Actions template:

```bash
mkdir -p .github/workflows
cp omaib-contracts/templates/github-actions/validate-dap.yml \
   .github/workflows/validate-dap.yml
```

This runs `omaib-validate-adapter` on every push and pull request to `omaib-adapter/`. On release, it also validates before the release is considered complete. Failed validation blocks the release.

---

## Step 5 — Register with OMAIB

Submit a registration request to the OMAIB platform team:

1. Open an issue at: `https://github.com/omaib/omaib-contracts/issues/new`
2. Use the title: `[PI Registration] <your-project-name>`
3. Include:
   - Your repository URL
   - Your adapter path within the repo (default: `omaib-adapter/`)
   - Your GitHub handle (for issue assignments and notifications)
   - Your project's benchmark_id from `benchmark_contract.yaml`

The platform team will add your repo to the ingestion registry within 5 working days. You'll receive a confirmation issue comment.

---

## Step 5b — Install the OMAIB Platform Bot - GitHub App (one-time)

> **Why?** The OMAIB platform opens failure-notification issues directly in your adapter repository when benchmark ingestion detects a problem. This requires the GitHub App (OMAIB Platform Bot) to have `contents: read-only` and `issues: read & write` access to your repo.

**Install takes ~30 seconds:**

1. Visit <https://github.com/apps/omaib-platform-bot/installations/new>
2. Select your organisation (or personal account)
3. Under **Repository access**, choose **Only select repositories** and pick your adapter repo
4. Click **Install**

The app requests `contents: read-only` and `issues: write` permission — it never reads or modifies your code.

> **Optional but strongly recommended.** Without it, failure notifications are posted to the shared `omaib-contracts` tracker only; you will miss them unless you watch that repository.

---

## Step 6 — Tag a Release

Once registered and Gate 1 passes:

```bash
git tag -a v0.1.0 -m "Initial DAP release"
git push origin v0.1.0
```

The OMAIB platform polls registered repos every 6 hours for new tagged releases. Your adapter will be ingested, validated, and registered within the next polling cycle.

You can also trigger immediate ingestion by posting to: `POST /api/v1/ingestion/trigger/<your-adapter-id>` (requires an API token — request one from the platform team).

---

## Step 7 — Releasing Updates (Subsequent Submissions)

After your initial registration, **you do not need to re-register**. The platform polls your repo automatically every 6 hours.

To publish an updated adapter:

```bash
# Make your changes to files in omaib-adapter/
# Re-validate locally first
omaib-validate-adapter omaib-adapter/
# Confirm Gate 1 Ready: YES, then tag
git add omaib-adapter/
git commit -m "Update adapter — describe what changed"
git tag -a v0.2.0 -m "Adapter update: describe what changed"
git push origin main
git push origin v0.2.0
```

### What happens automatically

| Trigger | Actor | Action |
|---------|-------|--------|
| New tag detected | Platform (automated) | Fetch and validate adapter at that tag |
| Gate 1 passes | Platform (automated) | Store new immutable snapshot, update live registry |
| Gate 1 fails | Platform (automated) | Open GitHub issue in `omaib/omaib-adapter-registry`, keep last valid snapshot live |
| Issue opened | PI | Fix errors locally, push new tag, comment on issue |
| New tag passes | Platform (automated) | Store snapshot, close failure issue automatically |

### What requires contacting the OMAIB team

You only need to update `registered_sources.yaml` (via a new GitHub issue or email) if you:

- Change your `adapter_id` (rare — this changes your persistent identifier)
- Move your adapter directory to a different path within the repo
- Change your repo URL (e.g. moved organisations)

All other changes — file content, metrics, schema updates, governance policy revisions — are picked up automatically via the tag/poll cycle.

### Version numbering guidance

| Change type | Example | Version bump |
|-------------|---------|-------------|
| Fix TBD fields or schema errors | First complete fill | `0.0.x` patch |
| Update metrics or governance policy | New data tier | `0.x.0` minor |
| Add new tasks or change evaluation mode | Pilot → full evaluation | `x.0.0` major |
| First complete submission for Gate 2+ | Ready for evaluator | `1.0.0` |

---

## What Happens After Ingestion

### Success path

1. Platform detects your tagged release
2. Platform pulls `omaib-adapter/` from that tag
3. Platform validates against OMAIB schemas
4. Snapshot stored immutably at `adapters/snapshots/{adapter_id}/{tag}/`
5. Registry updated — your benchmark appears in the catalogue and API
6. Gate status updated on the OMAIB status dashboard

### Failure path

1. Platform detects new tag — pulls and validates
2. Validation fails (schema error, missing file, score < 60%)
3. Platform keeps the last valid snapshot in production
4. Platform opens a GitHub issue on `omaib/omaib-adapter-registry` tagging your adapter ID and listing the validation errors
5. You fix the adapter, push a new tag, cycle repeats

This means a bad release **never breaks production** — the platform just keeps using your last good version.

---

## File Reference

### benchmark_contract.yaml (required)

Declares what your benchmark does, who owns it, and how data is accessed.
See: [templates/benchmark_contract.template.yaml](templates/benchmark_contract.template.yaml)

Key fields:
- `adapter_id`: `dap-<your-slug>` (must match your repo slug)
- `benchmark_id`: `omaib-<your-slug>` (assigned on registration)
- `evaluation_modes`: at least one of `public`, `hidden-test`, `maintainer-run`, `custodian-run`
- `governance.export_rules`: at least one rule — do not leave as TBD

### data_profile.json (required)

Describes your dataset: size, modalities, access tier, dataset version.
See: [templates/data_profile.template.yaml](templates/data_profile.template.yaml)

### governance_policy.yaml (required)

Records your data governance boundary: legal basis, custodian, data sharing tier. This is the FAIR "Accessible" layer.
See: [templates/governance_policy.template.yaml](templates/governance_policy.template.yaml)

### scorecard_schema.json (required)

Defines what metrics your benchmark produces and which are public vs. restricted. Must include at least one `public_fields` entry.
See: [templates/scorecard_schema.template.yaml](templates/scorecard_schema.template.yaml)

### trust_toolkit.yaml (recommended)

Stakeholder engagement map: who the benchmark serves and how they were involved. Required for Gate 3 (convergence).
See: [templates/trust_toolkit.template.yaml](templates/trust_toolkit.template.yaml)

### assurance_crosswalk.yaml (recommended)

Maps benchmark metrics to regulatory/assurance frameworks. Required for Gate 4.
See: [templates/assurance_crosswalk.template.yaml](templates/assurance_crosswalk.template.yaml)

---

## Getting Help

- Open a GitHub issue: [https://github.com/omaib/omaib-contracts/issues](https://github.com/omaib/omaib-contracts/issues)
- Platform status: [https://omaib.github.io/status](https://omaib.github.io/status)
- Contact: `omaib-platform@sheffield.ac.uk`
