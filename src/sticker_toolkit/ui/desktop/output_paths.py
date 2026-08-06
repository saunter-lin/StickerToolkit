"""Desktop-only output directory suggestions and writability checks."""

from __future__ import annotations

import os
from pathlib import Path


def suggested_output_directory(source_path: Path) -> Path:
    """Return a sibling `<source stem>_output` directory without creating it."""
    source = source_path.expanduser()
    return source.parent / f"{source.stem}_output"


def output_directory_is_writable(output_path: Path) -> bool:
    """Check the output itself, or its nearest existing parent, for writability."""
    candidate = output_path.expanduser()
    if candidate.exists():
        return candidate.is_dir() and os.access(candidate, os.W_OK)

    parent = candidate.parent
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    return parent.is_dir() and os.access(parent, os.W_OK)
