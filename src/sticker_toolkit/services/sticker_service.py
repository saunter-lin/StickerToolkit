"""CLI 與桌面 UI 共用的唯一貼圖處理流程。"""

from __future__ import annotations

from pathlib import Path

from core.config import LINE_CONFIG
from core.images import StickerError
from core.paths import ProjectPaths
from exporters.common import remove_directory
from sticker_toolkit.core.background_alpha import (
    detect_canvas_edge_color,
    detect_solid_background_color,
    parse_hex_color,
    remove_connected_solid_background,
)
from sticker_toolkit.core.exceptions import (
    InvalidGridError,
    InvalidSourceImageError,
    ProcessingError,
    StickerToolkitError,
)
from sticker_toolkit.core.image_processor import build_shared_stickers
from sticker_toolkit.core.loader import load_image
from sticker_toolkit.core.models import (
    OptionsCallback,
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
        options_callback: OptionsCallback | None = None,
    ) -> ProcessingResult:
        if options.platform not in {"line", "wechat", "both"}:
            raise StickerToolkitError(f"不支援的輸出平台：{options.platform}")
        if (options.rows, options.columns) != (4, 4):
            raise InvalidGridError("目前貼圖合集必須使用 4×4 格線。")
        if not options.trim_enabled:
            raise StickerToolkitError("v1.3 第一階段仍固定啟用 Trim。")
        if options.padding_ratio is not None:
            raise StickerToolkitError("v1.3 第一階段尚未開放自訂 padding_ratio。")
        source_path = source_path.expanduser().resolve()
        if not source_path.is_file():
            raise InvalidSourceImageError(f"找不到貼圖合集：{source_path}")

        self._report(progress_callback, 0, "準備處理")
        try:
            self._report(progress_callback, 10, "正在讀取圖片")
            source = load_image(source_path, "貼圖合集")
            if options.remove_solid_background:
                self._report(progress_callback, 20, "正在移除外部連通的純色背景")
                detected = (
                    detect_solid_background_color(source)
                    if options.auto_detect_solid_background
                    else None
                )
                background_color = detected or parse_hex_color(options.solid_background_color)
                if detected is not None:
                    edge_color = detect_canvas_edge_color(source)
                    if edge_color is not None and edge_color != background_color:
                        source = remove_connected_solid_background(
                            source,
                            edge_color,
                            options.solid_background_tolerance,
                        )
                source = remove_connected_solid_background(
                    source,
                    background_color,
                    options.solid_background_tolerance,
                    grid_size=(options.rows, options.columns),
                )
            self._report(progress_callback, 30, "正在切割與處理貼圖")
            stickers = build_shared_stickers(
                source,
                LINE_CONFIG.sticker_size,
                LINE_CONFIG.sticker_padding,
                remove_cell_edge_background=not options.remove_solid_background,
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
            selection_files: list[Path] = []
            if options.create_preview and options.platform in {"line", "both"}:
                create_selection_preview(stickers, paths.preview.line_directory)
                selection_files.append(paths.preview.line_directory / "selection.png")
            if options.create_preview and options.platform in {"wechat", "both"}:
                create_selection_preview(stickers, paths.preview.wechat_directory)
                selection_files.append(paths.preview.wechat_directory / "selection.png")
            if options_callback is not None:
                options = options_callback(options, tuple(selection_files))
            selected_indices = [options.main_index, options.tab_index, options.wechat_cover_index]
            if any(index < 1 or index > 16 for index in selected_indices):
                raise StickerToolkitError("貼圖來源編號必須是 1～16。")

            if options.platform in {"line", "both"}:
                self._report(progress_callback, 55, "正在產生 LINE 素材")
                if not options.create_preview:
                    remove_directory(paths.preview.line_directory, "LINE Preview")
                line_result = export_line_result(stickers, paths.output, options)
                if options.create_preview:
                    self._report(progress_callback, 75, "正在產生 LINE 預覽")
                    line_result = create_line_preview(stickers, paths.preview, line_result)
                results.append(line_result)

            if options.platform in {"wechat", "both"}:
                self._report(progress_callback, 80, "正在產生 WeChat 素材")
                if not options.create_preview:
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
