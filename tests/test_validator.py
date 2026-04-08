"""End-to-end tests for the adapter validator against the synthetic demo DAP.

The synthetic demo (``examples/dap-synthetic-demo/``) is the canonical reference adapter
shipped with omaib-contracts.  It must always pass Gate 1 at a high readiness score,
have no missing required files, no schema errors, and no TBD placeholder values.

These tests serve as the acceptance gate for any changes to schemas, validator logic,
or the demo adapter files themselves.
"""

from pathlib import Path

from validators.validate_adapter import validate_adapter

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
SYNTHETIC_DEMO = EXAMPLES_DIR / "dap-synthetic-demo"


def test_synthetic_demo_exists():
    """The synthetic demo adapter directory must be present in the examples/ folder."""
    assert SYNTHETIC_DEMO.is_dir(), "dap-synthetic-demo example directory must exist"


def test_synthetic_demo_gate_1_ready():
    """The synthetic demo adapter must pass Gate 1 validation end-to-end."""
    report = validate_adapter(SYNTHETIC_DEMO)
    assert report.gate_1_ready, (
        f"Synthetic demo failed Gate 1. Score: {report.gate_readiness_score}%. "
        f"Missing: {report.missing_required_files}. "
        f"Errors: {[e for r in report.file_reports for e in r.errors]}"
    )


def test_synthetic_demo_no_missing_files():
    """All four required DAP files must be present in the synthetic demo directory."""
    report = validate_adapter(SYNTHETIC_DEMO)
    assert not report.missing_required_files, (
        f"Missing required files: {report.missing_required_files}"
    )


def test_synthetic_demo_all_schemas_valid():
    """Every required DAP file in the synthetic demo must pass schema (or meta-schema) validation."""
    report = validate_adapter(SYNTHETIC_DEMO)
    failures = [r for r in report.file_reports if r.exists and not r.valid_schema]
    assert not failures, (
        f"Schema failures: {[(r.filename, r.errors) for r in failures]}"
    )


def test_synthetic_demo_no_tbd_fields():
    """The synthetic demo must not contain any TBD placeholder values in any required file."""
    report = validate_adapter(SYNTHETIC_DEMO)
    all_tbds = [(r.filename, r.tbd_fields) for r in report.file_reports if r.tbd_fields]
    assert not all_tbds, f"TBD fields found in synthetic demo: {all_tbds}"


def test_synthetic_demo_readiness_score_above_90():
    """The synthetic demo gate readiness score must be at least 90%.

    The demo is a fully-filled reference adapter, so a score below 90% indicates
    either TBD placeholders crept in or the scoring logic regressed.
    """
    report = validate_adapter(SYNTHETIC_DEMO)
    assert report.gate_readiness_score >= 90.0, (
        f"Synthetic demo readiness score {report.gate_readiness_score}% is below 90%"
    )


def test_invalid_adapter_dir_returns_missing_files(tmp_path: Path):
    """An empty directory must report all four required files as missing and Gate 1 not ready."""
    report = validate_adapter(tmp_path)
    assert len(report.missing_required_files) == 4
    assert not report.gate_1_ready
