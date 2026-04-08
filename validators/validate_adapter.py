#!/usr/bin/env python3
"""
omaib-validate-adapter: CLI and library for validating OMAIB Domain Adapter Packs.

Usage (CLI)::

    omaib-validate-adapter <adapter-directory> [--json]

Validates the four required DAP files against their respective JSON Schema (Draft 2020-12)
documents bundled with this package, then computes a gate readiness score.

Required files validated as schema *instances*:
    benchmark_contract.yaml   -- benchmark identity and evaluation protocol
    data_profile.json         -- modality, format, and provenance metadata
    governance_policy.yaml    -- access tier, compute location, export rules

Required files validated as JSON Schema *definitions* (meta-schema check):
    scorecard_schema.json     -- adapter-specific scorecard structure (IS a schema, not an instance)

Exit codes:
    0  -- Gate 1 ready (all required files present, schema-valid, readiness score >= 60%).
    1  -- Gate 1 not ready or one or more validation errors.
"""

import json
import sys
from pathlib import Path
from dataclasses import dataclass, field

import yaml

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("Install jsonschema: pip install jsonschema")
    sys.exit(1)

# Resolve schema directory.
# When installed via pip: schemas are package data inside validators/schemas/.
# When running from source (pip install -e .): same path works via editable install.
try:
    from importlib.resources import files as _resource_files
    SCHEMA_DIR = _resource_files("validators") / "schemas"
except Exception:
    # Hard fallback — running directly from source without install
    SCHEMA_DIR = Path(__file__).parent / "schemas"


def _schema_exists(schema_path) -> bool:
    """Return True if the schema file exists, False otherwise.

    Handles both ``pathlib.Path`` objects (source installs) and
    ``importlib.resources.abc.Traversable`` objects (wheel installs), where
    ``Path.is_file()`` is not always available directly.

    Args:
        schema_path: A ``pathlib.Path`` or ``importlib.resources.abc.Traversable``
            pointing to the schema file.

    Returns:
        bool: True if the file is accessible and exists, False otherwise.
    """
    try:
        return schema_path.is_file()
    except Exception:
        return Path(str(schema_path)).is_file()


# Files validated as *instances* against their schema.
REQUIRED_FILES = {
    "benchmark_contract.yaml": "benchmark_contract.schema.json",
    "data_profile.json": "data_profile.schema.json",
    "governance_policy.yaml": "governance_policy.schema.json",
}

# Files validated as *JSON Schema definitions* (meta-schema validation).
# These define what the adapter's scorecards look like — they are schemas, not instances.
SCHEMA_DEF_FILES = [
    "scorecard_schema.json",
]

OPTIONAL_FILES = [
    "trust_toolkit.yaml",
    "assurance_crosswalk.yaml",
    "README.md",
    "CITATION.cff",
]

TBD_MARKERS = {"TBD", "tbd", "TODO", "todo", "N/A", "n/a", ""}


@dataclass
class FileReport:
    """Validation result for a single DAP file.

    Attributes:
        filename: Basename of the DAP file being reported on.
        exists: True if the file was found in the adapter directory.
        valid_schema: True if the file passed schema (or meta-schema) validation.
        errors: List of human-readable error strings (schema violations or parse errors).
        tbd_fields: Dot-notation paths of fields whose values are TBD-like placeholders.
        total_required_fields: Count of required fields defined in the schema.
        non_tbd_required_fields: Count of required fields that contain real (non-TBD) values.
    """

    filename: str
    exists: bool = False
    valid_schema: bool = False
    errors: list = field(default_factory=list)
    tbd_fields: list = field(default_factory=list)
    total_required_fields: int = 0
    non_tbd_required_fields: int = 0


@dataclass
class AdapterReport:
    """Aggregated validation result for an entire Domain Adapter Pack directory.

    Attributes:
        adapter_path: Absolute or relative path to the adapter directory that was validated.
        file_reports: One FileReport per required DAP file (both instance and schema-def files).
        gate_readiness_score: Percentage of required fields containing real (non-TBD) values.
            Used as the primary Gate 1 threshold metric (must be >= 60.0 to pass Gate 1).
        gate_1_ready: True when all required files are present, schema-valid, and
            gate_readiness_score >= 60.0.
        missing_required_files: Basenames of required files that were not found.
        optional_files_present: Basenames of recommended optional files that were found.
        optional_files_missing: Basenames of recommended optional files that were absent.
    """

    adapter_path: str
    file_reports: list = field(default_factory=list)
    gate_readiness_score: float = 0.0
    gate_1_ready: bool = False
    missing_required_files: list = field(default_factory=list)
    optional_files_present: list = field(default_factory=list)
    optional_files_missing: list = field(default_factory=list)


def load_file(path: Path):
    """Load and parse a YAML or JSON file into a Python object.

    Args:
        path: Absolute or relative path to the file.  Files with ``.yaml`` or
            ``.yml`` extensions are parsed with PyYAML; all others are parsed as JSON.

    Returns:
        The parsed Python object (typically a dict).

    Raises:
        yaml.YAMLError: If a YAML file cannot be parsed.
        json.JSONDecodeError: If a JSON file cannot be parsed.
        OSError: If the file cannot be read.
    """
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text)
    return json.loads(text)


def find_tbd_fields(data, prefix: str = "") -> list:
    """Recursively collect dot-notation paths of fields that contain TBD-like placeholder values.

    A value is considered TBD-like if it matches any entry in ``TBD_MARKERS`` or if its
    upper-cased form starts with ``"TBD"``.  Lists are traversed element-by-element using
    bracket notation (e.g. ``provenance_fields[0]``).

    Args:
        data: The parsed data structure to inspect (dict, list, or scalar).
        prefix: Dot-notation path accumulated by recursive calls.  Pass an empty string
            for the root call.

    Returns:
        A list of dot-notation field path strings whose values are TBD-like.
    """
    tbds = []
    if isinstance(data, dict):
        for k, v in data.items():
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, str) and v.strip() in TBD_MARKERS:
                tbds.append(path)
            elif isinstance(v, str) and v.strip().upper().startswith("TBD"):
                tbds.append(path)
            else:
                tbds.extend(find_tbd_fields(v, path))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            tbds.extend(find_tbd_fields(item, f"{prefix}[{i}]"))
    return tbds


def count_required_fields(schema: dict) -> int:
    """Count the total number of required fields declared in a JSON Schema object.

    Performs a shallow recursive walk: counts items in the top-level ``required``
    array and then recurses into any ``properties`` whose type is ``"object"``.
    This gives a reasonable proxy for "how many fields does this schema mandate?"
    without fully expanding ``$ref`` chains or ``allOf``/``anyOf`` combinators.

    Args:
        schema: A parsed JSON Schema dict (Draft 2020-12).

    Returns:
        Integer count of required field declarations encountered.
    """
    count = len(schema.get("required", []))
    for prop_schema in schema.get("properties", {}).values():
        if isinstance(prop_schema, dict) and prop_schema.get("type") == "object":
            count += count_required_fields(prop_schema)
    return count


def validate_file(adapter_dir: Path, filename: str, schema_filename: str) -> FileReport:
    """Validate a single DAP file as an instance against its JSON Schema.

    Loads the file from ``adapter_dir``, loads the corresponding schema from the
    package's bundled ``schemas/`` directory, then runs ``Draft202012Validator``.
    Also scans for TBD-like placeholder values and counts required fields for the
    gate readiness score calculation.

    Args:
        adapter_dir: Path to the DAP directory being validated.
        filename: Basename of the DAP file to validate (e.g. ``"data_profile.json"``).
        schema_filename: Basename of the JSON Schema file to validate against
            (e.g. ``"data_profile.schema.json"``).

    Returns:
        A populated FileReport.  If the file is missing or cannot be parsed, the report
        will have ``exists=False`` or ``valid_schema=False`` with errors populated.
    """
    report = FileReport(filename=filename)
    filepath = adapter_dir / filename
    schema_path = SCHEMA_DIR / schema_filename

    if not filepath.exists():
        report.errors.append(f"File not found: {filename}")
        return report

    report.exists = True

    if not _schema_exists(schema_path):
        report.errors.append(f"Schema not found: {schema_filename} (SCHEMA_DIR={SCHEMA_DIR})")
        return report

    try:
        data = load_file(filepath)
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except Exception as e:
        report.errors.append(f"Parse error: {e}")
        return report

    validator = Draft202012Validator(schema)
    schema_errors = list(validator.iter_errors(data))
    if schema_errors:
        for err in schema_errors[:10]:
            path_str = ".".join(str(p) for p in err.absolute_path)
            report.errors.append(f"{path_str or '<root>'}: {err.message}")
    else:
        report.valid_schema = True

    report.tbd_fields = find_tbd_fields(data)
    report.total_required_fields = count_required_fields(schema)
    # Exclude "dependencies.*" from TBD count — those fields are platform-resolved
    tbd_in_required = len([t for t in report.tbd_fields if not t.startswith("dependencies")])
    report.non_tbd_required_fields = max(0, report.total_required_fields - tbd_in_required)

    return report


def validate_schema_def_file(adapter_dir: Path, filename: str) -> FileReport:
    """Validate a DAP file that is itself a JSON Schema definition (meta-schema check).

    ``scorecard_schema.json`` defines what the adapter's scorecard submissions look like.
    It is a schema, not an instance, so it must NOT be validated as an instance against
    the platform's ``scorecard.schema.json``.  Instead this function performs structural
    checks: the file must be valid JSON, must be a dict, must declare ``$schema``, and
    must define ``properties`` or ``$ref``.

    Args:
        adapter_dir: Path to the DAP directory being validated.
        filename: Basename of the schema definition file (e.g. ``"scorecard_schema.json"``).

    Returns:
        A populated FileReport.  ``valid_schema`` is True only if all structural checks pass.
    """
    report = FileReport(filename=filename)
    filepath = adapter_dir / filename

    if not filepath.exists():
        report.errors.append(f"File not found: {filename}")
        return report

    report.exists = True

    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
    except Exception as e:
        report.errors.append(f"JSON parse error: {e}")
        return report

    # Minimal structural checks for a JSON Schema document
    if not isinstance(data, dict):
        report.errors.append("scorecard_schema.json must be a JSON object (schema definition)")
        return report
    if "$schema" not in data:
        report.errors.append("scorecard_schema.json must declare '$schema' (e.g. JSON Schema Draft 2020-12)")
    if "properties" not in data and "$ref" not in data:
        report.errors.append("scorecard_schema.json must define 'properties' or '$ref'")

    if not report.errors:
        report.valid_schema = True

    report.tbd_fields = find_tbd_fields(data)
    # Count top-level properties as a proxy for field completeness
    report.total_required_fields = len(data.get("properties", {}))
    tbd_in_required = len([t for t in report.tbd_fields if not t.startswith("dependencies")])
    report.non_tbd_required_fields = max(0, report.total_required_fields - tbd_in_required)

    return report


def validate_adapter(adapter_dir: Path) -> AdapterReport:
    """Validate an entire Domain Adapter Pack directory and compute gate readiness.

    Runs ``validate_file`` for each entry in ``REQUIRED_FILES`` and
    ``validate_schema_def_file`` for each entry in ``SCHEMA_DEF_FILES``.
    Checks for optional files.  Computes ``gate_readiness_score`` as the ratio of
    non-TBD required fields to total required fields, and sets ``gate_1_ready``.

    Args:
        adapter_dir: Path to the DAP directory to validate.

    Returns:
        A fully populated AdapterReport including per-file reports, missing file lists,
        gate readiness score, and gate 1 pass/fail status.
    """
    report = AdapterReport(adapter_path=str(adapter_dir))

    for filename, schema_filename in REQUIRED_FILES.items():
        file_report = validate_file(adapter_dir, filename, schema_filename)
        report.file_reports.append(file_report)
        if not file_report.exists:
            report.missing_required_files.append(filename)

    for filename in SCHEMA_DEF_FILES:
        file_report = validate_schema_def_file(adapter_dir, filename)
        report.file_reports.append(file_report)
        if not file_report.exists:
            report.missing_required_files.append(filename)

    for filename in OPTIONAL_FILES:
        if (adapter_dir / filename).exists():
            report.optional_files_present.append(filename)
        else:
            report.optional_files_missing.append(filename)

    total_required = sum(r.total_required_fields for r in report.file_reports if r.exists)
    total_non_tbd = sum(r.non_tbd_required_fields for r in report.file_reports if r.exists)
    total_valid = sum(1 for r in report.file_reports if r.valid_schema)
    all_required_count = len(REQUIRED_FILES) + len(SCHEMA_DEF_FILES)

    if total_required > 0:
        report.gate_readiness_score = round((total_non_tbd / total_required) * 100, 1)

    report.gate_1_ready = (
        len(report.missing_required_files) == 0
        and total_valid == all_required_count
        and report.gate_readiness_score >= 60.0
    )

    return report


def print_report(report: AdapterReport) -> None:
    """Print a human-readable validation report to stdout.

    Outputs per-file status lines (``[OK]``, ``[FAIL]``, or ``[MISS]``), schema error
    details, TBD field lists, optional file presence, the gate readiness score, and the
    Gate 1 pass/fail verdict.  All output uses printable ASCII to ensure compatibility
    with Windows cp1252 terminals.

    Args:
        report: A populated AdapterReport as returned by ``validate_adapter``.
    """
    print(f"\n{'=' * 70}")
    print("OMAIB Adapter Validation Report")
    print(f"Adapter: {report.adapter_path}")
    print(f"{'=' * 70}\n")

    for fr in report.file_reports:
        if fr.valid_schema:
            status = "[OK]"
        elif fr.exists:
            status = "[FAIL]"
        else:
            status = "[MISS]"
        print(f"  {status} {fr.filename}")
        for e in fr.errors:
            print(f"      ERROR: {e}")
        if fr.tbd_fields:
            print(f"      TBD fields ({len(fr.tbd_fields)}):")
            for t in fr.tbd_fields[:5]:
                print(f"        - {t}")
            if len(fr.tbd_fields) > 5:
                print(f"        ... and {len(fr.tbd_fields) - 5} more")

    print("\n  Optional files:")
    for f in report.optional_files_present:
        print(f"    [OK] {f}")
    for f in report.optional_files_missing:
        print(f"    [--] {f} (missing - recommended but not required)")

    print(f"\n{'-' * 70}")
    print(f"  Gate Readiness Score: {report.gate_readiness_score}%")
    print(f"  Gate 1 Ready:        {'YES' if report.gate_1_ready else 'NO'}")
    if report.missing_required_files:
        print(f"  Missing required:    {', '.join(report.missing_required_files)}")
    print(f"{'-' * 70}\n")


def main() -> None:
    """Entry point for the ``omaib-validate-adapter`` CLI command.

    Parses command-line arguments, runs ``validate_adapter`` on the given directory,
    prints the human-readable report, and optionally dumps the full report as JSON
    when ``--json`` is supplied.

    Exits with code 0 if Gate 1 is ready, 1 otherwise.
    """
    if len(sys.argv) < 2:
        print("Usage: omaib-validate-adapter <adapter-directory> [--json]")
        sys.exit(1)

    adapter_dir = Path(sys.argv[1])
    if not adapter_dir.is_dir():
        print(f"Error: {adapter_dir} is not a directory")
        sys.exit(1)

    report = validate_adapter(adapter_dir)
    print_report(report)

    if "--json" in sys.argv:
        import dataclasses
        print(json.dumps(dataclasses.asdict(report), indent=2))

    sys.exit(0 if report.gate_1_ready else 1)


if __name__ == "__main__":
    main()
