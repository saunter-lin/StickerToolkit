"""平台輸出與結果模型組裝。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from core.paths import OutputPaths
from exporters.line import export_line
from exporters.wechat import WechatExportResult, export_wechat
from sticker_toolkit.core.models import PlatformProcessingResult, ProcessingOptions


def sticker_files(directory: Path, count: int) -> tuple[Path, ...]:
    return tuple(directory / f"{index:02d}.png" for index in range(1, count + 1))


def export_line_result(
    stickers: list[Image.Image], paths: OutputPaths, options: ProcessingOptions
) -> PlatformProcessingResult:
    created_zip = export_line(stickers, paths, options.main_index, options.tab_index)
    zip_file: Path | None = created_zip
    if not options.create_zip:
        created_zip.unlink(missing_ok=True)
        zip_file = None
    return PlatformProcessingResult(
        platform="line",
        output_directory=paths.line_directory,
        sticker_files=sticker_files(paths.line_directory, len(stickers)),
        main_file=paths.line_directory / "main.png",
        tab_file=paths.line_directory / "tab.png",
        zip_file=zip_file,
    )


def export_wechat_result(
    stickers: list[Image.Image], paths: OutputPaths, options: ProcessingOptions
) -> tuple[PlatformProcessingResult, WechatExportResult]:
    exported = export_wechat(
        stickers,
        paths,
        options.banner_path,
        options.wechat_cover_index,
    )
    zip_file: Path | None = exported.zip_path
    if not options.create_zip:
        exported.zip_path.unlink(missing_ok=True)
        zip_file = None
    warnings = () if exported.complete else ("微信素材尚未完整，可能無法直接提交。",)
    result = PlatformProcessingResult(
        platform="wechat",
        output_directory=paths.wechat_directory,
        sticker_files=sticker_files(paths.wechat_directory, len(stickers)),
        banner_file=exported.banner_path,
        cover_file=exported.cover_path,
        panel_icon_file=exported.panel_icon_path,
        zip_file=zip_file,
        warnings=warnings,
    )
    return result, exported
