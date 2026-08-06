"""Preview 建立服務，不涉及 UI 顯示或開啟視窗。"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PIL import Image

from core.config import LINE_CONFIG, WECHAT_CONFIG
from core.images import load_image
from core.paths import PreviewPaths
from exporters.common import clean_directory, save_rgba_png
from exporters.wechat import WechatExportResult
from preview import make_line_preview, make_preview, make_wechat_preview
from sticker_toolkit.core.models import PlatformProcessingResult


def create_selection_preview(stickers: list[Image.Image], directory: Path) -> None:
    clean_directory(directory, "Preview")
    save_rgba_png(make_preview(stickers), directory / "selection.png")


def create_line_preview(
    stickers: list[Image.Image], previews: PreviewPaths, result: PlatformProcessingResult
) -> PlatformProcessingResult:
    if result.main_file is None or result.tab_file is None:
        raise ValueError("LINE 結果缺少 main.png 或 tab.png。")
    main_image = load_image(result.main_file, "LINE main")
    tab_image = load_image(result.tab_file, "LINE tab")
    messages = [
        "LINE 貼圖：16 張，370×320 RGBA PNG",
        "main.png：240×240 RGBA PNG",
        "tab.png：96×74 RGBA PNG",
        "LINE 素材驗證通過。",
    ]
    preview_file = previews.line_directory / LINE_CONFIG.preview_name
    save_rgba_png(make_line_preview(stickers, main_image, tab_image, messages), preview_file)
    return replace(result, preview_file=preview_file)


def create_wechat_preview(
    stickers: list[Image.Image],
    previews: PreviewPaths,
    result: PlatformProcessingResult,
    exported: WechatExportResult,
) -> PlatformProcessingResult:
    if result.cover_file is None or result.panel_icon_file is None:
        raise ValueError("WeChat 結果缺少 cover.png 或 panel_icon.png。")
    banner = load_image(result.banner_file, "已處理 Banner") if result.banner_file else None
    cover = load_image(result.cover_file, "WeChat cover")
    panel_icon = load_image(result.panel_icon_file, "WeChat panel icon")
    preview_file = previews.wechat_directory / WECHAT_CONFIG.preview_name
    save_rgba_png(
        make_wechat_preview(
            stickers,
            banner,
            cover,
            panel_icon,
            exported.zip_contents,
            exported.validation_messages,
            exported.complete,
        ),
        preview_file,
    )
    return replace(result, preview_file=preview_file)
