"""
Gate readiness computation for OMAIB Domain Adapter Packs.

This module maps an AdapterReport (produced by ``validate_adapter``) onto the
CDRF portfolio delivery gates.  Gates follow the UKOMAIN/OMAIB P0-P4 model:

    Gate 1 -- Contract readiness: all required DAP files present, schema-valid, and
              gate readiness score >= 60%.  Governance boundary and export policy recorded.
    Gate 2 -- Pilot readiness: evaluator runnable end-to-end in at least one evaluation mode.
              Score threshold >= 80%.
    Gate 3 -- Convergence: cross-project scorecard alignment confirmed; external review evidence
              submitted.  Cannot be determined from adapter files alone.
    Gate 4 -- Release readiness: v1.0 packaging, schema version pins, reproducibility manifests,
              and adoption assets in place.  Cannot be determined from adapter files alone.

Gates 3 and 4 require platform-level evidence gathered outside the adapter directory and will
always report ``ready=False`` when computed purely from a local DAP.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .validate_adapter import AdapterReport, validate_adapter


GATE_1_MIN_SCORE = 60.0
GATE_2_MIN_SCORE = 80.0


@dataclass
class GateStatus:
    """Readiness state for a single CDRF delivery gate.

    Attributes:
        gate: Gate number (1 through 4).
        ready: True if the gate has been passed.
        score: The gate readiness score (percentage) from the underlying AdapterReport.
        blockers: Human-readable list of reasons the gate is not yet ready.
            Empty when ``ready`` is True.
        notes: One-line description of what this gate requires.
    """

    gate: int
    ready: bool
    score: float
    blockers: list[str]
    notes: str


def compute_gate_status(report: AdapterReport) -> list[GateStatus]:
    """Compute per-gate delivery readiness from an AdapterReport.

    Evaluates Gates 1 and 2 from the adapter files alone.  Gates 3 and 4 always
    return ``ready=False`` because they require platform-level evidence (cross-project
    scorecard alignment, external review, release packaging) that cannot be inferred
    from a local DAP directory.

    Args:
        report: A populated AdapterReport as returned by ``validate_adapter``.

    Returns:
        A list of four GateStatus objects in gate order (1, 2, 3, 4).
    """
    gates = []

    # Gate 1: Contract readiness
    blockers_1 = []
    if report.missing_required_files:
        blockers_1.append(f"Missing files: {', '.join(report.missing_required_files)}")
    schema_failures = [r for r in report.file_reports if r.exists and not r.valid_schema]
    if schema_failures:
        blockers_1.append(f"Schema failures: {', '.join(r.filename for r in schema_failures)}")
    if report.gate_readiness_score < GATE_1_MIN_SCORE:
        blockers_1.append(
            f"Readiness score {report.gate_readiness_score}% < {GATE_1_MIN_SCORE}% threshold"
        )

    gates.append(GateStatus(
        gate=1,
        ready=report.gate_1_ready,
        score=report.gate_readiness_score,
        blockers=blockers_1,
        notes="All required DAP files valid; governance boundary and export policy recorded.",
    ))

    # Gate 2: Pilot readiness (heuristic — score threshold)
    gate_2_ready = report.gate_1_ready and report.gate_readiness_score >= GATE_2_MIN_SCORE
    blockers_2 = []
    if not report.gate_1_ready:
        blockers_2.append("Gate 1 not passed")
    elif report.gate_readiness_score < GATE_2_MIN_SCORE:
        blockers_2.append(
            f"Readiness score {report.gate_readiness_score}% < {GATE_2_MIN_SCORE}% threshold"
        )

    gates.append(GateStatus(
        gate=2,
        ready=gate_2_ready,
        score=report.gate_readiness_score,
        blockers=blockers_2,
        notes="Evaluator runnable end-to-end; scorecard produced.",
    ))

    # Gates 3 & 4 cannot be determined from adapter files alone
    for g, note in [
        (3, "Cross-project scorecard alignment + external review evidence."),
        (4, "v1.0 packaging: docs, schema versions, reproducibility manifests, adoption assets."),
    ]:
        gates.append(GateStatus(
            gate=g,
            ready=False,
            score=report.gate_readiness_score,
            blockers=["Requires platform-level evidence beyond adapter files"],
            notes=note,
        ))

    return gates


def print_gate_summary(gates: list[GateStatus]) -> None:
    """Print a concise per-gate readiness summary to stdout.

    Uses printable ASCII only (no Unicode box-drawing or symbol characters) to
    ensure compatibility with Windows cp1252 terminals.

    Args:
        gates: List of GateStatus objects as returned by ``compute_gate_status``.
    """
    for g in gates:
        icon = "[PASS]" if g.ready else "[----]"
        print(f"  {icon} Gate {g.gate}: {'READY' if g.ready else 'NOT READY'}  ({g.notes})")
        if not g.ready and g.blockers:
            for b in g.blockers:
                print(f"        > {b}")


def main() -> None:
    """Entry point for the ``omaib-gate-status`` CLI command.

    Validates the adapter at the given directory path, then prints a per-gate
    readiness summary using ``print_gate_summary``.

    Exits with code 1 if the adapter directory argument is missing.
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: omaib-gate-status <adapter-directory>")
        sys.exit(1)

    adapter_dir = Path(sys.argv[1])
    report = validate_adapter(adapter_dir)
    gates = compute_gate_status(report)
    print(f"\nGate Status for: {adapter_dir}\n")
    print_gate_summary(gates)
    print()


if __name__ == "__main__":
    main()
