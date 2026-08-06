"""集中管理正式輸出與 Preview 路徑。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OutputPaths:
    root: Path
    line_directory: Path
    wechat_directory: Path
    line_zip: Path
    wechat_zip: Path


@dataclass(frozen=True)
class PreviewPaths:
    root: Path
    line_directory: Path
    wechat_directory: Path


@dataclass(frozen=True)
class ProjectPaths:
    output: OutputPaths
    preview: PreviewPaths

    @classmethod
    def from_root(cls, project_root: Path) -> ProjectPaths:
        output_root = project_root / "output"
        preview_root = project_root / "preview"
        return cls(
            output=OutputPaths(
                root=output_root,
                line_directory=output_root / "line_sticker",
                wechat_directory=output_root / "wechat_sticker",
                line_zip=output_root / "line_sticker.zip",
                wechat_zip=output_root / "wechat_sticker.zip",
            ),
            preview=PreviewPaths(
                root=preview_root,
                line_directory=preview_root / "line",
                wechat_directory=preview_root / "wechat",
            ),
        )
