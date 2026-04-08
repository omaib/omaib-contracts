"""
omaib-contracts: OMAIB shared schemas, validators, and Domain Adapter Pack templates.

This package is the *keystone* of the OMAIB pull-based federation model.  It ships:

- JSON Schema files (Draft 2020-12) for all four required DAP files.
- A CLI entry point ``omaib-validate-adapter <path>`` that validates a DAP directory
  and reports gate readiness against the CDRF delivery gates (Gate 1 through Gate 4).
- A secondary CLI ``omaib-gate-status <path>`` that prints a per-gate readiness summary.
- A programmatic Python API for platform-side ingestion pipelines.

Typical PI workflow::

    pip install omaib-contracts
    omaib-validate-adapter path/to/omaib-adapter/

Public API
----------
validate_adapter(adapter_dir) -> AdapterReport
    Validate a DAP directory against all required schemas.  Returns a structured report.

compute_gate_status(report) -> list[GateStatus]
    Derive per-gate readiness from an AdapterReport.

AdapterReport
    Aggregated validation result for an entire DAP directory.

FileReport
    Per-file validation result (schema errors, TBD fields, field counts).

GateStatus
    Readiness state for a single CDRF delivery gate.

REQUIRED_FILES
    Mapping of required DAP filenames to their platform JSON Schema.

SCHEMA_DEF_FILES
    List of DAP files that are themselves JSON Schema definitions (meta-schema check).

OPTIONAL_FILES
    Recommended but not required DAP filenames.
"""

from validators.validate_adapter import (
    validate_adapter,
    AdapterReport,
    FileReport,
    REQUIRED_FILES,
    OPTIONAL_FILES,
    SCHEMA_DEF_FILES,
)
from validators.gate_readiness import compute_gate_status, GateStatus

__version__ = "0.3.0"

__all__ = [
    "validate_adapter",
    "AdapterReport",
    "FileReport",
    "REQUIRED_FILES",
    "OPTIONAL_FILES",
    "SCHEMA_DEF_FILES",
    "compute_gate_status",
    "GateStatus",
    "__version__",
]
