"""LINE 平台輸出。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from core.config import LINE_ANIMATED_CONFIG, LINE_CONFIG
from core.images import StickerError, contain, load_image
from core.paths import OutputPaths

from .common import clean_directory, remove_file, save_rgba_png, validate_png, write_zip

OLD_LINE_ZIP_NAMES = ("line_sticker_package.zip", "line_stickers.zip")


def prepare_line_main_image(source: Image.Image) -> Image.Image:
    if LINE_CONFIG.main_size is None:
        raise RuntimeError("LINE_CONFIG 缺少 main 尺寸。")
    return contain(source, LINE_CONFIG.main_size, LINE_CONFIG.main_padding)


def prepare_line_tab_image(main_image: Image.Image) -> Image.Image:
    if LINE_CONFIG.tab_size is None:
        raise RuntimeError("LINE_CONFIG 缺少 tab 尺寸。")
    return contain(main_image, LINE_CONFIG.tab_size, LINE_CONFIG.tab_padding)


def export_line(
    stickers: list[Image.Image],
    paths: OutputPaths,
    main_index: int,
    tab_index: int,
    main_source_path: Path | None = None,
) -> Path:
    if LINE_CONFIG.main_size is None or LINE_CONFIG.tab_size is None:
        raise RuntimeError("LINE_CONFIG 缺少 main 或 tab 尺寸。")
    clean_directory(paths.line_directory, "LINE 輸出")
    remove_file(paths.line_zip, "LINE ZIP")
    # 清除 v1.2.1 以前散落在 output/ 根目錄的 LINE 素材，不觸碰 WeChat。
    legacy_names = [*(f"{index:02d}.png" for index in range(1, 17)), "main.png", "tab.png"]
    for name in legacy_names:
        try:
            (paths.root / name).unlink(missing_ok=True)
        except OSError as exc:
            raise StickerError(f"無法清除舊版 LINE 素材：{name}（{exc}）") from exc
    sticker_paths: list[Path] = []
    for index, sticker in enumerate(stickers, 1):
        path = paths.line_directory / f"{index:02d}.png"
        save_rgba_png(sticker, path)
        validate_png(path, LINE_CONFIG.sticker_size)
        sticker_paths.append(path)
    main_path = paths.line_directory / "main.png"
    tab_path = paths.line_directory / "tab.png"
    main_source = (
        load_image(main_source_path, "LINE 自選封面")
        if main_source_path is not None
        else stickers[main_index - 1]
    )
    main_image = prepare_line_main_image(main_source)
    save_rgba_png(main_image, main_path)
    save_rgba_png(prepare_line_tab_image(main_image), tab_path)
    validate_png(main_path, LINE_CONFIG.main_size)
    validate_png(tab_path, LINE_CONFIG.tab_size)
    zip_path = paths.line_zip
    entries = [(path, f"line_sticker/{path.name}") for path in [*sticker_paths, main_path, tab_path]]
    for old_name in OLD_LINE_ZIP_NAMES:
        old_path = paths.root / old_name
        try:
            old_path.unlink(missing_ok=True)
        except OSError as exc:
            raise StickerError(f"無法清除舊版 LINE ZIP：{old_name}（{exc}）") from exc
    write_zip(zip_path, entries)
    return zip_path


def export_line_animated(stickers: list[Image.Image], paths: OutputPaths) -> Path:
    """Export PNG frames for Sticker Motion Toolkit; intentionally does not encode APNG."""
    clean_directory(paths.line_animated_directory, "LINE 動圖輸出")
    remove_file(paths.line_zip, "LINE 動圖 ZIP")
    entries: list[tuple[Path, str]] = []
    for index, sticker in enumerate(stickers, 1):
        path = paths.line_animated_directory / f"{index:02d}.png"
        frame = contain(
            sticker,
            LINE_ANIMATED_CONFIG.sticker_size,
            LINE_ANIMATED_CONFIG.sticker_padding,
        )
        save_rgba_png(frame, path)
        validate_png(path, LINE_ANIMATED_CONFIG.sticker_size)
        entries.append((path, f"line_sticker/{path.name}"))
    write_zip(paths.line_zip, entries)
    return paths.line_zip
