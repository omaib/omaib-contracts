"""
Adapter scaffolding CLI for OMAIB Domain Adapter Packs.

Creates an omaib-adapter/ directory pre-populated with all six DAP file templates,
named correctly (no .template. suffix) and ready to fill in. This removes the manual
copy-and-rename step described in PI_ONBOARDING.md.

Usage:
    omaib-init-adapter <target-directory> [--slug <project-slug>]
    omaib-init-adapter <target-directory> [--slug <project-slug>] [--force]

Examples:
    # Create omaib-adapter/ in the current repo (no slug substitution)
    omaib-init-adapter omaib-adapter/

    # Substitute the placeholder slug throughout all generated files
    omaib-init-adapter omaib-adapter/ --slug my-benchmark

    # Overwrite existing files in an already-initialised directory
    omaib-init-adapter omaib-adapter/ --slug my-benchmark --force

Exit codes:
    0  All files created successfully.
    1  Target directory already contains DAP files and --force was not given.
    2  Usage error (missing arguments).
"""

from __future__ import annotations

import argparse
import importlib.resources as _pkg_resources
import sys
from pathlib import Path


# Map from template filename -> final (output) filename
_TEMPLATE_MAP: dict[str, str] = {
    "benchmark_contract.template.yaml": "benchmark_contract.yaml",
    "data_profile.template.json":       "data_profile.json",
    "governance_policy.template.yaml":  "governance_policy.yaml",
    "scorecard_schema.template.json":   "scorecard_schema.json",
    "trust_toolkit.template.yaml":      "trust_toolkit.yaml",
    "assurance_crosswalk.template.yaml": "assurance_crosswalk.yaml",
}

_REQUIRED = {
    "benchmark_contract.yaml",
    "data_profile.json",
    "governance_policy.yaml",
    "scorecard_schema.json",
}

_RECOMMENDED = {
    "trust_toolkit.yaml",
    "assurance_crosswalk.yaml",
}


def _read_template(template_filename: str) -> str:
    """Read a template file from the validators.templates package data.

    Works with both editable installs (pip install -e .) and regular pip installs,
    because the templates are shipped as package data inside validators/templates/.

    Args:
        template_filename (str): Basename of the template file to read
            (e.g. ``"benchmark_contract.template.yaml"``).

    Returns:
        str: UTF-8 decoded contents of the template file.

    Raises:
        RuntimeError: If the template file is not found in the installed package data.
    """
    try:
        pkg = _pkg_resources.files("validators") / "templates" / template_filename
        return pkg.read_text(encoding="utf-8")
    except (FileNotFoundError, TypeError) as exc:
        raise RuntimeError(
            f"Template '{template_filename}' not found in omaib-contracts package. "
            "Ensure omaib-contracts is correctly installed."
        ) from exc


def _apply_slug(content: str, slug: str) -> str:
    """Replace ``<project-slug>`` and ``<benchmark-slug>`` placeholders with the given slug.

    Args:
        content (str): Raw template file contents containing placeholder strings.
        slug (str): Project slug to substitute (e.g. ``"my-benchmark"``).

    Returns:
        str: Template content with all slug placeholders replaced.
    """
    content = content.replace("dap-<project-slug>", f"dap-{slug}")
    content = content.replace("omaib-<benchmark-slug>", f"omaib-{slug}")
    return content


def _check_existing(target_dir: Path) -> list[str]:
    """Return the list of DAP output files that already exist in ``target_dir``.

    Args:
        target_dir (Path): Directory to check for existing DAP files.

    Returns:
        list[str]: Basenames of files from :data:`_TEMPLATE_MAP` that are already present.
    """
    existing = []
    for final_name in _TEMPLATE_MAP.values():
        if (target_dir / final_name).exists():
            existing.append(final_name)
    return existing


def init_adapter(
    target_dir: Path,
    slug: str | None = None,
    force: bool = False,
) -> int:
    """Create a pre-populated adapter directory from the bundled templates.

    Args:
        target_dir: Destination directory (created if it does not exist).
        slug:       Optional project slug to substitute into placeholder values.
        force:      If True, overwrite existing files without prompting.

    Returns:
        Exit code: 0 on success, 1 if files already exist and force is False.
    """
    target_dir = Path(target_dir)

    existing = _check_existing(target_dir)
    if existing and not force:
        print(
            f"[STOP] {target_dir} already contains DAP files: {', '.join(existing)}\n"
            "       Use --force to overwrite."
        )
        return 1

    target_dir.mkdir(parents=True, exist_ok=True)

    created = []
    for template_name, final_name in _TEMPLATE_MAP.items():
        content = _read_template(template_name)
        if slug:
            content = _apply_slug(content, slug)
        dest = target_dir / final_name
        dest.write_text(content, encoding="utf-8")
        tag = "(required)" if final_name in _REQUIRED else "(recommended)"
        created.append((final_name, tag))

    print(f"\nOMAIB adapter initialised in: {target_dir}\n")
    for fname, tag in created:
        print(f"  [+] {fname}  {tag}")

    slug_note = f" (slug: dap-{slug})" if slug else " (no slug substituted — edit manually)"
    print(f"\n{slug_note}")
    print("\nNext steps:")
    print("  1. Fill in all fields — replace every <placeholder> and TBD value")
    print("  2. Run: omaib-validate-adapter", str(target_dir))
    print("  3. Confirm Gate 1 Ready: YES before tagging a release")
    return 0


def main() -> None:
    """Entry point for the omaib-init-adapter CLI command."""
    parser = argparse.ArgumentParser(
        prog="omaib-init-adapter",
        description=(
            "Initialise an OMAIB adapter directory with all six DAP template files.\n"
            "Files are created with their final names (no .template. suffix), ready to fill in."
        ),
    )
    parser.add_argument(
        "target_dir",
        metavar="TARGET_DIRECTORY",
        help="Directory to create (e.g. omaib-adapter/). Created if it does not exist.",
    )
    parser.add_argument(
        "--slug",
        metavar="PROJECT_SLUG",
        default=None,
        help=(
            "Project slug to substitute into adapter_id and benchmark_id placeholders "
            "(e.g. --slug my-benchmark sets adapter_id: dap-my-benchmark)."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files without prompting.",
    )

    args = parser.parse_args()
    sys.exit(init_adapter(Path(args.target_dir), slug=args.slug, force=args.force))


if __name__ == "__main__":
    main()
