# Synthetic Demo DAP

This is a **fully valid** Domain Adapter Pack used exclusively for platform
integration testing. It contains zero TBD fields and exercises all DAP
schema requirements.

**Do not use this for real benchmarking.** The data is synthetic.

## Purpose

- Validates the end-to-end submission → evaluation → scorecard → leaderboard
  pipeline without depending on any real project's data or governance.
- Serves as the reference implementation for new DAP authors.
- Used by the CI walking skeleton test.

## Gate Status

This adapter is designed to pass Gate 1 and Gate 2 validation out of the box.

## Adapter IDs

| Field | Value |
|-------|-------|
| `adapter_id` | `dap-synthetic-demo` |
| `benchmark_id` | `omaib-synthetic-demo` |
| `version` | `0.1.0` |
