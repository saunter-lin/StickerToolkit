"""CLI 與桌面 UI 共用的唯一貼圖處理流程。"""

from __future__ import annotations

from pathlib import Path

from core.config import LINE_CONFIG
from core.images import StickerError
from core.paths import ProjectPaths
from exporters.common import remove_directory
from sticker_toolkit.core.exceptions import (
    InvalidGridError,
    InvalidSourceImageError,
    ProcessingError,
    StickerToolkitError,
)
from sticker_toolkit.core.image_processor import build_shared_stickers
from sticker_toolkit.core.loader import load_image
from sticker_toolkit.core.models import (
    PlatformProcessingResult,
    ProcessingOptions,
    ProcessingResult,
    ProgressCallback,
)
from sticker_toolkit.presets import PRESETS
from sticker_toolkit.services.output_service import export_line_result, export_wechat_result
from sticker_toolkit.services.preview_service import (
    create_line_preview,
    create_selection_preview,
    create_wechat_preview,
)


class StickerService:
    """無 UI 狀態、可由背景執行緒安全呼叫的應用服務。"""

    @staticmethod
    def _report(callback: ProgressCallback | None, value: int, message: str) -> None:
        if callback is not None:
            callback(value, message)

    def process(
        self,
        source_path: Path,
        options: ProcessingOptions,
        progress_callback: ProgressCallback | None = None,
    ) -> ProcessingResult:
        if options.platform not in {"line", "wechat", "both"}:
            raise StickerToolkitError(f"不支援的輸出平台：{options.platform}")
        if (options.rows, options.columns) != (4, 4):
            raise InvalidGridError("目前貼圖合集必須使用 4×4 格線。")
        if not options.trim_enabled:
            raise StickerToolkitError("v1.3 第一階段仍固定啟用 Trim。")
        if options.padding_ratio is not None:
            raise StickerToolkitError("v1.3 第一階段尚未開放自訂 padding_ratio。")
        selected_indices = [options.main_index, options.tab_index, options.wechat_cover_index]
        if any(index < 1 or index > 16 for index in selected_indices):
            raise StickerToolkitError("貼圖來源編號必須是 1～16。")
        source_path = source_path.expanduser().resolve()
        if not source_path.is_file():
            raise InvalidSourceImageError(f"找不到貼圖合集：{source_path}")

        self._report(progress_callback, 0, "準備處理")
        try:
            self._report(progress_callback, 10, "正在讀取圖片")
            source = load_image(source_path, "貼圖合集")
            self._report(progress_callback, 30, "正在切割與處理貼圖")
            stickers = build_shared_stickers(
                source,
                LINE_CONFIG.sticker_size,
                LINE_CONFIG.sticker_padding,
            )
            platform_keys = ("line", "wechat") if options.platform == "both" else (options.platform,)
            for key in platform_keys:
                preset = PRESETS[key]
                if not preset.min_sticker_count <= len(stickers) <= preset.max_sticker_count:
                    raise ProcessingError(
                        f"{preset.name} 貼圖數量必須為 {preset.min_sticker_count}～"
                        f"{preset.max_sticker_count} 張，目前為 {len(stickers)} 張。"
                    )
            paths = ProjectPaths.from_output(options.output_directory.expanduser().resolve())
            paths.output.root.mkdir(parents=True, exist_ok=True)
            results: list[PlatformProcessingResult] = []

            if options.platform in {"line", "both"}:
                self._report(progress_callback, 55, "正在產生 LINE 素材")
                if options.create_preview:
                    create_selection_preview(stickers, paths.preview.line_directory)
                else:
                    remove_directory(paths.preview.line_directory, "LINE Preview")
                line_result = export_line_result(stickers, paths.output, options)
                if options.create_preview:
                    self._report(progress_callback, 75, "正在產生 LINE 預覽")
                    line_result = create_line_preview(stickers, paths.preview, line_result)
                results.append(line_result)

            if options.platform in {"wechat", "both"}:
                self._report(progress_callback, 80, "正在產生 WeChat 素材")
                if options.create_preview:
                    create_selection_preview(stickers, paths.preview.wechat_directory)
                else:
                    remove_directory(paths.preview.wechat_directory, "WeChat Preview")
                wechat_result, exported = export_wechat_result(stickers, paths.output, options)
                if options.create_preview:
                    self._report(progress_callback, 90, "正在產生 WeChat 預覽")
                    wechat_result = create_wechat_preview(
                        stickers, paths.preview, wechat_result, exported
                    )
                results.append(wechat_result)
        except StickerToolkitError:
            raise
        except StickerError as exc:
            raise ProcessingError(str(exc)) from exc
        except OSError as exc:
            raise ProcessingError(f"檔案處理失敗：{exc}") from exc

        warnings = tuple(warning for result in results for warning in result.warnings)
        self._report(progress_callback, 100, "處理完成")
        return ProcessingResult(source_path, tuple(results), warnings)
