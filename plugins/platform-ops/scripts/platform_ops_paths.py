"""Path defaults shared by the standalone Platform Ops entry points."""

import os
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def add_specs_argument(parser):
    parser.add_argument(
        "-d", "--specs-dir",
        default=os.environ.get("ADDITIONAL_SPECS_PATH") or os.environ.get("PROJECT_SPECS_PATH"),
        help="Path to local specifications (or env ADDITIONAL_SPECS_PATH / PROJECT_SPECS_PATH).",
    )


def find_specs_dir(configured):
    if configured:
        return Path(configured).expanduser()

    cwd = Path.cwd()
    for parent in (cwd, *cwd.parents[:3]):
        candidate = parent / "Project_Specifications"
        if candidate.is_dir() and any(path.is_file() for path in candidate.glob("*.md")):
            return candidate
    return None
