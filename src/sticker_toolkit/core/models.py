"""UI、Service 與 Core 之間的型別化資料模型。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

ProgressCallback = Callable[[int, str], None]


@dataclass(frozen=True)
class ProcessingOptions:
    platform: str = "line"
    rows: int = 4
    columns: int = 4
    trim_enabled: bool = True
    padding_ratio: float | None = None
    output_directory: Path = Path("output")
    create_preview: bool = True
    create_zip: bool = True
    main_index: int = 1
    tab_index: int = 1
    wechat_cover_index: int = 1
    banner_path: Path | None = None


OptionsCallback = Callable[[ProcessingOptions, tuple[Path, ...]], ProcessingOptions]


@dataclass(frozen=True)
class PlatformProcessingResult:
    platform: str
    output_directory: Path
    sticker_files: tuple[Path, ...]
    main_file: Path | None = None
    tab_file: Path | None = None
    banner_file: Path | None = None
    cover_file: Path | None = None
    panel_icon_file: Path | None = None
    preview_file: Path | None = None
    zip_file: Path | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProcessingResult:
    source_path: Path
    platforms: tuple[PlatformProcessingResult, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def for_platform(self, platform: str) -> PlatformProcessingResult:
        for result in self.platforms:
            if result.platform == platform:
                return result
        raise KeyError(platform)
