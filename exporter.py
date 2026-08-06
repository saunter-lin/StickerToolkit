"""v1.1 相容層；新程式請使用 exporters.common。"""

from pathlib import Path

from exporters.common import validate_png, write_zip

__all__ = ["create_zip", "validate_png"]


def create_zip(zip_path: Path, paths: list[Path]) -> None:
    write_zip(zip_path, [(path, path.name) for path in paths])
