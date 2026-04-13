#!/usr/bin/env python3
"""PII scan — reject commits that introduce PII into any omaib repo.

Hosted in ``omaib-contracts``; invoked by every repo in the omaib GitHub
organisation via a reusable GitHub Actions workflow.

Usage
-----
From within the repo being scanned (CI default — scans current directory)::

    python pii_scan_tool.py

Specify a path explicitly (e.g. during local development)::

    python scripts/pii_scan.py /path/to/repo

Exits 0 if clean, 1 if any violations are found.

Rules enforced
--------------
1. Legacy YAML field names (``pi:``, ``contact:``, ``email_contact:``,
   ``owner_contact:``) must not appear in data files (.yaml/.yml/.json).
2. Personal email addresses (anything matching ``word@word.tld`` that is NOT
   a known allowed functional address) must not appear in committed artefacts.
3. Files in ``backup/`` and ``.venv/`` are excluded from scanning.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Directories excluded from scanning
EXCLUDED_DIRS = {".venv", "backup", ".git", "__pycache__", "*.egg-info"}

# Functional / role email addresses that are explicitly allowed
ALLOWED_EMAILS: frozenset[str] = frozenset(
    {
        "omaib-ukomain-group@sheffield.ac.uk",
        "ukomain.contact@gmail.com",
    }
)

# Domains that appear in technical/service URLs but are never personal emails
# e.g. git@github.com SSH URLs, x-access-token:tok@github.com clone URLs
TECHNICAL_DOMAINS: frozenset[str] = frozenset(
    {
        "github.com",
        "gitlab.com",
        "bitbucket.org",
    }
)

# Extensions to scan for email address matches
EMAIL_SCAN_EXTENSIONS = {".py", ".yaml", ".yml", ".json", ".md", ".rst", ".txt", ".toml", ".cfg"}

# Extensions to scan for legacy YAML field names
FIELD_SCAN_EXTENSIONS = {".yaml", ".yml", ".json"}

# Legacy field patterns — name must appear as a YAML/JSON key
LEGACY_FIELD_RE = re.compile(
    r"""^\s*["']?(pi|contact|email_contact|owner_contact)["']?\s*:""",
    re.MULTILINE,
)

# Email pattern — broad match; we filter out allowed addresses afterwards
EMAIL_RE = re.compile(
    r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b"
)

# Files to skip entirely (by name, case-insensitive) — policy / plan docs
# that necessarily discuss the field names being scanned for
SKIP_FILENAMES = {
    "pii_scan.py",
    "pii_scan_tool.py",
    "pii_policy.md",
    "implementation_plan.md",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_args() -> Path:
    """Return the root path to scan, from CLI arg or auto-detection."""
    p = argparse.ArgumentParser(
        description="Scan a repository for PII violations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "root",
        nargs="?",
        help=(
            "Root path of the repository to scan. "
            "Defaults to the parent of this script's directory when run "
            "from within scripts/, otherwise defaults to the current directory."
        ),
    )
    args = p.parse_args()

    if args.root:
        return Path(args.root).resolve()

    # Auto-detect: if this script lives in a `scripts/` subdirectory, the
    # repo root is one level up; otherwise use the current working directory
    # (which is the default in CI after `actions/checkout`).
    script_dir = Path(__file__).resolve().parent
    if script_dir.name == "scripts":
        return script_dir.parent
    return Path.cwd()


def _is_excluded(path: Path) -> bool:
    """Return True if *path* is inside an excluded directory."""
    parts = {p.lower() for p in path.parts}
    for excl in EXCLUDED_DIRS:
        if excl.lower() in parts:
            return True
    return False


def _scan_file_legacy_fields(path: Path) -> list[tuple[int, str]]:
    """Return list of (lineno, line) tuples where legacy PII fields appear."""
    hits: list[tuple[int, str]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return hits
    for i, line in enumerate(lines, start=1):
        if LEGACY_FIELD_RE.search(line):
            hits.append((i, line.rstrip()))
    return hits


def _scan_file_emails(path: Path) -> list[tuple[int, str, str]]:
    """Return list of (lineno, email, line) for disallowed email addresses."""
    hits: list[tuple[int, str, str]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return hits
    for i, line in enumerate(lines, start=1):
        for match in EMAIL_RE.finditer(line):
            email = match.group(0).lower()
            if email in ALLOWED_EMAILS:
                continue
            domain = email.split("@", 1)[-1]
            if domain in TECHNICAL_DOMAINS:
                continue
            hits.append((i, match.group(0), line.rstrip()))
    return hits


# ---------------------------------------------------------------------------
# Main scan
# ---------------------------------------------------------------------------


def run_scan(root: Path) -> int:
    """Scan *root* and return the number of violations found."""
    violations = 0

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if _is_excluded(path):
            continue
        if path.name.lower() in SKIP_FILENAMES:
            continue

        suffix = path.suffix.lower()
        rel = path.relative_to(root)

        # 1. Legacy YAML/JSON field check
        if suffix in FIELD_SCAN_EXTENSIONS:
            for lineno, line in _scan_file_legacy_fields(path):
                print(f"[LEGACY FIELD] {rel}:{lineno}: {line}")
                violations += 1

        # 2. Email address check
        if suffix in EMAIL_SCAN_EXTENSIONS:
            for lineno, email, line in _scan_file_emails(path):
                print(f"[EMAIL PII]    {rel}:{lineno}: {email!r} — {line[:120]}")
                violations += 1

    return violations


def main() -> None:
    """Entry point."""
    root = _parse_args()
    print(f"Scanning {root} for PII...")
    count = run_scan(root)
    if count == 0:
        print("PII scan PASSED — no violations found.")
        sys.exit(0)
    else:
        print(f"\nPII scan FAILED — {count} violation(s) found.")
        print("See https://github.com/omaib/omaib-contracts/blob/main/PII_POLICY.md for remediation guidance.")
        sys.exit(1)


if __name__ == "__main__":
    main()
