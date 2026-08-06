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
)


@dataclass(frozen=True)
class DesktopFormData:
    source_path: str
    platform: str
    rows: int
    columns: int
    banner_path: str
    output_directory: str
    trim_enabled: bool = True
    create_preview: bool = True
    create_zip: bool = True


class DesktopValidationError(ValueError):
    """可直接顯示於桌面 UI 的表單錯誤。"""


def banner_enabled(platform: str) -> bool:
    return platform in {"wechat", "both"}


def validate_form(data: DesktopFormData) -> None:
    if not data.source_path.strip():
        raise DesktopValidationError("請先選擇來源圖片。")
    if data.platform not in {"line", "wechat", "both"}:
        raise DesktopValidationError("請選擇 LINE、微信或 LINE＋微信。")
    if data.rows <= 0 or data.columns <= 0:
        raise DesktopValidationError("切割設定必須為正整數，且不可為 0。")
    if (data.rows, data.columns) != (4, 4):
        raise DesktopValidationError("目前版本僅支援 4 × 4 貼圖合集。")
    source = Path(data.source_path).expanduser()
    if not source.is_file():
        raise DesktopValidationError("找不到來源圖片，請重新選擇。")
    if not data.output_directory.strip():
        raise DesktopValidationError("請選擇輸出目錄。")
    if data.banner_path.strip() and not Path(data.banner_path).expanduser().is_file():
        raise DesktopValidationError("找不到微信 Banner 圖片，請重新選擇或清除。")


def build_processing_options(data: DesktopFormData) -> ProcessingOptions:
    validate_form(data)
    banner = Path(data.banner_path).expanduser().resolve() if data.banner_path.strip() else None
    return ProcessingOptions(
        platform=data.platform,
        rows=data.rows,
        columns=data.columns,
        trim_enabled=data.trim_enabled,
        output_directory=Path(data.output_directory).expanduser().resolve(),
        create_preview=data.create_preview,
        create_zip=data.create_zip,
        banner_path=banner,
    )


def user_error_message(error: Exception) -> str:
    if isinstance(error, InvalidSourceImageError):
        return "無法讀取來源圖片，請確認檔案格式是否正確。"
    if isinstance(error, InvalidGridError):
        return "切割設定不正確，請確認行數與列數。"
    if isinstance(error, StickerToolkitError):
        return str(error)
    if isinstance(error, OSError):
        return "輸出目錄無法寫入，請選擇其他位置。"
    return "處理失敗，請查看記錄檔取得詳細資訊。"


def result_summary(result: ProcessingResult) -> str:
    lines = ["處理完成", f"輸出平台：{', '.join(item.platform for item in result.platforms)}"]
    for item in result.platforms:
        lines.append(f"{item.platform} 貼圖：{len(item.sticker_files)} 張")
        lines.append(f"{item.platform} 目錄：{item.output_directory}")
        lines.append(f"{item.platform} ZIP：{item.zip_file or '未建立'}")
        lines.append(f"{item.platform} Preview：{item.preview_file or '未建立'}")
    lines.extend(f"警告：{warning}" for warning in result.warnings)
    return "\n".join(lines)
