"""不依賴 Qt widget 的桌面表單狀態、驗證與結果摘要。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sticker_toolkit.core import (
    InvalidGridError,
    InvalidSourceImageError,
    ProcessingOptions,
    ProcessingResult,
    StickerToolkitError,
    parse_hex_color,
)

from .i18n import tr
from .output_paths import output_directory_from_root, output_directory_is_writable


@dataclass(frozen=True)
class DesktopFormData:
    source_path: str
    platform: str
    rows: int
    columns: int
    banner_path: str
    output_directory: str
    input_mode: str = "sheet"
    batch_source_paths: tuple[str, ...] = ()
    line_cover_path: str = ""
    wechat_cover_path: str = ""
    trim_enabled: bool = True
    create_preview: bool = True
    create_zip: bool = True
    remove_solid_background: bool = False
    auto_detect_solid_background: bool = True
    solid_background_color: str = "#FFF8EC"
    solid_background_tolerance: int = 3


class DesktopValidationError(ValueError):
    """可直接顯示於桌面 UI 的表單錯誤。"""


def banner_enabled(platform: str) -> bool:
    return platform in {"wechat", "both"}


def validate_form(data: DesktopFormData) -> None:
    if data.input_mode not in {"sheet", "wechat_batch", "line_animated", "main_cover"}:
        raise DesktopValidationError("請選擇有效的輸入模式。")
    if data.input_mode == "wechat_batch":
        count = len(data.batch_source_paths)
        if count < 16:
            raise DesktopValidationError(f"WeChat 批次單圖目前只有 {count} 張，尚不足 16 張。")
        if count > 16:
            raise DesktopValidationError(f"WeChat 批次單圖目前有 {count} 張，請先使用「移除」整理至 16 張。")
        if data.platform != "wechat":
            raise DesktopValidationError("WeChat 批次單圖模式僅支援微信輸出。")
        if not data.banner_path.strip():
            raise DesktopValidationError("WeChat 批次單圖模式必須選擇 Banner。")
        missing = [path for path in data.batch_source_paths if not Path(path).expanduser().is_file()]
        if missing:
            raise DesktopValidationError(f"找不到批次圖片：{Path(missing[0]).name}")
    elif not data.source_path.strip():
        raise DesktopValidationError("請先選擇來源圖片。")
    if data.input_mode == "line_animated" and data.platform != "line_animated":
        raise DesktopValidationError("LINE 動圖模式必須使用 LINE 動圖輸出。")
    if data.input_mode == "main_cover" and data.platform != "main_cover":
        raise DesktopValidationError("Main / Cover 模式必須使用 Main / Cover 輸出。")
    if data.platform not in {"line", "line_animated", "wechat", "both", "main_cover"}:
        raise DesktopValidationError("請選擇 LINE、LINE 動圖、微信或 LINE＋微信。")
    if data.rows <= 0 or data.columns <= 0:
        raise DesktopValidationError("切割設定必須為正整數，且不可為 0。")
    if data.input_mode != "main_cover" and (data.rows, data.columns) != (4, 4):
        raise DesktopValidationError("目前版本僅支援 4 × 4 貼圖合集。")
    source = Path(data.source_path).expanduser()
    if not source.is_file():
        raise DesktopValidationError("找不到來源圖片，請重新選擇。")
    if not data.output_directory.strip():
        raise DesktopValidationError("請選擇輸出目錄。")
    output = output_directory_from_root(Path(data.output_directory))
    if not output_directory_is_writable(output):
        raise DesktopValidationError("輸出目錄無法寫入，請選擇其他位置。")
    if data.banner_path.strip() and not Path(data.banner_path).expanduser().is_file():
        raise DesktopValidationError("找不到微信 Banner 圖片，請重新選擇或清除。")
    for label, cover_path in (("LINE 封面", data.line_cover_path), ("WeChat 封面", data.wechat_cover_path)):
        if cover_path.strip() and not Path(cover_path).expanduser().is_file():
            raise DesktopValidationError(f"找不到{label}圖片，請重新選擇或清除。")
    if not 0 <= data.solid_background_tolerance <= 30:
        raise DesktopValidationError("純色背景容差必須介於 0～30。")
    if data.remove_solid_background:
        try:
            parse_hex_color(data.solid_background_color)
        except StickerToolkitError as exc:
            raise DesktopValidationError(str(exc)) from exc


def build_processing_options(data: DesktopFormData) -> ProcessingOptions:
    validate_form(data)
    banner = Path(data.banner_path).expanduser().resolve() if data.banner_path.strip() else None
    line_cover = Path(data.line_cover_path).expanduser().resolve() if data.line_cover_path.strip() else None
    wechat_cover = (
        Path(data.wechat_cover_path).expanduser().resolve() if data.wechat_cover_path.strip() else None
    )
    return ProcessingOptions(
        input_mode=data.input_mode,
        batch_source_paths=tuple(Path(path).expanduser().resolve() for path in data.batch_source_paths),
        platform=data.platform,
        rows=data.rows,
        columns=data.columns,
        trim_enabled=data.trim_enabled,
        output_directory=output_directory_from_root(Path(data.output_directory)).resolve(),
        create_preview=data.create_preview,
        create_zip=data.create_zip,
        banner_path=banner,
        line_cover_path=line_cover,
        wechat_cover_path=wechat_cover,
        remove_solid_background=data.remove_solid_background,
        auto_detect_solid_background=data.auto_detect_solid_background,
        solid_background_color=data.solid_background_color.upper(),
        solid_background_tolerance=data.solid_background_tolerance,
    )


def user_error_message(error: Exception, language: str = "zh_TW") -> str:
    if isinstance(error, InvalidSourceImageError):
        return tr(language, "error.invalid_source")
    if isinstance(error, InvalidGridError):
        return tr(language, "error.invalid_grid")
    if isinstance(error, StickerToolkitError):
        return str(error)
    if isinstance(error, OSError):
        return tr(language, "error.output")
    return tr(language, "error.generic")


def result_summary(result: ProcessingResult, language: str = "zh_TW") -> str:
    lines = [
        tr(language, "summary.completed"),
        tr(language, "summary.platforms", platforms=", ".join(item.platform for item in result.platforms)),
    ]
    for item in result.platforms:
        if item.platform == "main_cover":
            lines.append(tr(language, "summary.cover_files"))
            lines.append(
                tr(language, "summary.directory", platform=item.platform, path=item.output_directory)
            )
            continue
        lines.append(tr(language, "summary.stickers", platform=item.platform, count=len(item.sticker_files)))
        lines.append(tr(language, "summary.directory", platform=item.platform, path=item.output_directory))
        missing = tr(language, "summary.not_created")
        lines.append(tr(language, "summary.zip", platform=item.platform, path=item.zip_file or missing))
        lines.append(
            tr(language, "summary.preview", platform=item.platform, path=item.preview_file or missing)
        )
    lines.extend(tr(language, "summary.warning", warning=warning) for warning in result.warnings)
    return "\n".join(lines)
