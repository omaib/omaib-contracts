"""Tests that all bundled JSON Schema files in schemas/ are well-formed Draft 2020-12 documents.

Each schema must:
- Parse as a valid JSON object.
- Declare the ``$schema``, ``$id``, and ``title`` meta-fields.
- Pass ``Draft202012Validator.check_schema`` (i.e. be a structurally valid JSON Schema).

These tests run parametrically over every ``*.json`` file found in the schemas/ directory,
so new schemas are automatically picked up without changes to this file.
"""

import json
from pathlib import Path

import pytest

SCHEMA_DIR = Path(__file__).parent.parent / "schemas"
SCHEMA_FILES = list(SCHEMA_DIR.glob("*.json"))


@pytest.mark.parametrize("schema_path", SCHEMA_FILES, ids=[p.name for p in SCHEMA_FILES])
def test_schema_is_valid_json(schema_path: Path):
    """Each bundled schema file must parse as a JSON object (not an array or scalar)."""
    content = schema_path.read_text(encoding="utf-8")
    schema = json.loads(content)
    assert isinstance(schema, dict), f"{schema_path.name} must be a JSON object"


@pytest.mark.parametrize("schema_path", SCHEMA_FILES, ids=[p.name for p in SCHEMA_FILES])
def test_schema_has_required_meta_fields(schema_path: Path):
    """Each bundled schema must declare the three required JSON Schema meta-fields.

    ``$schema`` must be the Draft 2020-12 URI.  ``$id`` and ``title`` are required
    by OMAIB schema conventions so that schemas are self-identifying in error messages.
    """
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert "$schema" in schema, f"{schema_path.name} must declare $schema"
    assert "$id" in schema, f"{schema_path.name} must declare $id"
    assert "title" in schema, f"{schema_path.name} must declare title"
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


@pytest.mark.parametrize("schema_path", SCHEMA_FILES, ids=[p.name for p in SCHEMA_FILES])
def test_schema_is_valid_jsonschema(schema_path: Path):
    """Each bundled schema must itself be a structurally valid JSON Schema.

    Uses ``Draft202012Validator.check_schema`` which raises ``SchemaError`` if the
    schema contains invalid keywords, bad type values, or other structural problems.
    """
    from jsonschema import Draft202012Validator

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
