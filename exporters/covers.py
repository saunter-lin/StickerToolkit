"""Standalone LINE and WeChat cover asset export."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from core.config import LINE_CONFIG, WECHAT_CONFIG

from .common import clean_directory, save_optimized_png, save_rgba_png, validate_png
from .line import prepare_line_main_image, prepare_line_tab_image
from .wechat import prepare_wechat_cover_image, prepare_wechat_panel_icon_image


@dataclass(frozen=True)
class CoverExportResult:
    output_directory: Path
    main_path: Path
    tab_path: Path
    cover_path: Path
    panel_icon_path: Path


def export_cover_assets(source: Image.Image, output_directory: Path) -> CoverExportResult:
    """Create all four cover assets from one source using the platform exporters' logic."""
    if LINE_CONFIG.main_size is None or LINE_CONFIG.tab_size is None:
        raise RuntimeError("LINE_CONFIG 缺少 main 或 tab 尺寸。")
    clean_directory(output_directory, "Main / Cover 輸出")

    main_path = output_directory / "main.png"
    tab_path = output_directory / "tab.png"
    cover_path = output_directory / "cover.png"
    panel_icon_path = output_directory / "panel_icon.png"

    main = prepare_line_main_image(source)
    save_rgba_png(main, main_path)
    save_rgba_png(prepare_line_tab_image(main), tab_path)
    validate_png(main_path, LINE_CONFIG.main_size)
    validate_png(tab_path, LINE_CONFIG.tab_size)

    cover = prepare_wechat_cover_image(source)
    save_optimized_png(
        cover,
        cover_path,
        WECHAT_CONFIG.cover_max_bytes,
        "微信封面圖超過 500KB，請簡化圖片內容或調整輸出品質。",
    )
    save_optimized_png(
        prepare_wechat_panel_icon_image(cover),
        panel_icon_path,
        WECHAT_CONFIG.panel_icon_max_bytes,
        "微信聊天面板圖標超過 100KB，請簡化圖片內容或調整輸出品質。",
    )
    return CoverExportResult(
        output_directory=output_directory,
        main_path=main_path,
        tab_path=tab_path,
        cover_path=cover_path,
        panel_icon_path=panel_icon_path,
    )
