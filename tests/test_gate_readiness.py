"""Tests for CDRF gate readiness computation.

Verifies that ``compute_gate_status`` correctly maps an AdapterReport onto the
four CDRF delivery gates, using the synthetic demo as the reference adapter.

Key invariants tested:
- The synthetic demo passes Gate 1 (all files valid, score >= 60%).
- ``compute_gate_status`` always returns exactly four GateStatus objects in order 1-4.
- Gates 3 and 4 never auto-pass from adapter files alone.
"""

from pathlib import Path

from validators.validate_adapter import validate_adapter
from validators.gate_readiness import compute_gate_status

SYNTHETIC_DEMO = Path(__file__).parent.parent / "examples" / "dap-synthetic-demo"


def test_synthetic_demo_passes_gate_1():
    """The synthetic demo must pass Gate 1 (all required files valid, score >= 60%)."""
    report = validate_adapter(SYNTHETIC_DEMO)
    gates = compute_gate_status(report)
    gate_1 = next(g for g in gates if g.gate == 1)
    assert gate_1.ready, f"Gate 1 should be ready. Blockers: {gate_1.blockers}"


def test_gate_list_has_four_gates():
    """compute_gate_status must return exactly four GateStatus objects numbered 1 through 4."""
    report = validate_adapter(SYNTHETIC_DEMO)
    gates = compute_gate_status(report)
    assert len(gates) == 4
    assert [g.gate for g in gates] == [1, 2, 3, 4]


def test_gates_3_and_4_not_auto_ready():
    """Gates 3 and 4 require platform-level evidence — never auto-pass from files alone."""
    report = validate_adapter(SYNTHETIC_DEMO)
    gates = compute_gate_status(report)
    for g in gates:
        if g.gate in (3, 4):
            assert not g.ready, f"Gate {g.gate} should not auto-pass from adapter files alone"
