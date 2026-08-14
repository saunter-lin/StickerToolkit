"""符合微信素材尺寸、數量與檔案上限的 Exporter。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from core.config import WECHAT_CONFIG
from core.images import StickerError, contain, load_image
from core.paths import OutputPaths

from .common import clean_directory, remove_file, save_optimized_png, write_zip


@dataclass(frozen=True)
class WechatExportResult:
    zip_path: Path
    zip_contents: list[str]
    banner_path: Path | None
    cover_path: Path
    panel_icon_path: Path
    validation_messages: list[str]
    complete: bool


def validate_sticker_count(count: int) -> None:
    if not WECHAT_CONFIG.min_sticker_count <= count <= WECHAT_CONFIG.max_sticker_count:
        raise StickerError(
            f"微信表情圖數量必須為 {WECHAT_CONFIG.min_sticker_count}～"
            f"{WECHAT_CONFIG.max_sticker_count} 張，目前為 {count} 張。"
        )


def prepare_banner_image(banner: Image.Image, output_path: Path) -> Path:
    prepared = contain(banner, WECHAT_CONFIG.banner_size, WECHAT_CONFIG.banner_padding)
    save_optimized_png(
        prepared,
        output_path,
        WECHAT_CONFIG.banner_max_bytes,
        "微信詳情頁橫幅超過 500KB，請簡化圖片內容或調整輸出品質。",
    )
    return output_path


def prepare_banner(banner_path: Path, output_path: Path) -> Path:
    return prepare_banner_image(load_image(banner_path, "WeChat Banner"), output_path)


def _save_stickers(stickers: list[Image.Image], staging: Path) -> tuple[list[Path], list[tuple[Path, str]]]:
    paths: list[Path] = []
    entries: list[tuple[Path, str]] = []
    for index, sticker in enumerate(stickers, 1):
        path = staging / f"{index:02d}.png"
        prepared = contain(sticker, WECHAT_CONFIG.sticker_size, WECHAT_CONFIG.sticker_padding)
        save_optimized_png(
            prepared,
            path,
            WECHAT_CONFIG.sticker_max_bytes,
            f"第 {index} 張微信表情圖超過 500KB，請簡化圖片內容或調整輸出品質。",
        )
        paths.append(path)
        entries.append((path, path.name))
    return paths, entries


def export_wechat(
    stickers: list[Image.Image],
    paths: OutputPaths,
    banner_path: Path | None,
    cover_index: int = 1,
    cover_source_path: Path | None = None,
    *,
    auto_generate_banner: bool = False,
) -> WechatExportResult:
    validate_sticker_count(len(stickers))
    if not 1 <= cover_index <= len(stickers):
        raise StickerError(f"微信封面來源必須是 1～{len(stickers)}。")

    staging = paths.wechat_directory
    clean_directory(staging, "WeChat 輸出")
    remove_file(paths.wechat_zip, "WeChat ZIP")
    sticker_paths, entries = _save_stickers(stickers, staging)

    cover_path = staging / "cover.png"
    cover_source = (
        load_image(cover_source_path, "WeChat 自選封面")
        if cover_source_path is not None
        else stickers[cover_index - 1]
    )
    cover = contain(cover_source, WECHAT_CONFIG.cover_size, WECHAT_CONFIG.cover_padding)
    save_optimized_png(
        cover,
        cover_path,
        WECHAT_CONFIG.cover_max_bytes,
        "微信封面圖超過 500KB，請簡化圖片內容或調整輸出品質。",
    )
    entries.append((cover_path, "cover.png"))

    panel_icon_path = staging / "panel_icon.png"
    panel_icon = contain(
        cover,
        WECHAT_CONFIG.panel_icon_size,
        WECHAT_CONFIG.panel_icon_padding,
    )
    save_optimized_png(
        panel_icon,
        panel_icon_path,
        WECHAT_CONFIG.panel_icon_max_bytes,
        "微信聊天面板圖標超過 100KB，請簡化圖片內容或調整輸出品質。",
    )
    entries.append((panel_icon_path, "panel_icon.png"))

    prepared_banner: Path | None = None
    if banner_path is not None:
        prepared_banner = prepare_banner(banner_path, staging / "banner.png")
        entries.append((prepared_banner, "banner.png"))
    elif auto_generate_banner:
        prepared_banner = prepare_banner_image(cover, staging / "banner.png")
        entries.append((prepared_banner, "banner.png"))

    for old_name in ("wechat_sticker_package.zip",):
        try:
            (paths.root / old_name).unlink(missing_ok=True)
        except OSError as exc:
            raise StickerError(f"無法清除舊版 WeChat ZIP：{old_name}（{exc}）") from exc
    try:
        (staging / "manifest.json").unlink(missing_ok=True)
    except OSError as exc:
        raise StickerError(f"無法清除舊版 manifest.json（{exc}）") from exc

    zip_path = paths.wechat_zip
    names = write_zip(zip_path, entries)
    sticker_limit_kb = WECHAT_CONFIG.sticker_max_bytes // 1024
    banner_limit_kb = WECHAT_CONFIG.banner_max_bytes // 1024
    cover_limit_kb = WECHAT_CONFIG.cover_max_bytes // 1024
    panel_limit_kb = WECHAT_CONFIG.panel_icon_max_bytes // 1024
    sticker_size_parts = [
        f"{index:02d}={path.stat().st_size / 1024:.1f}KB" for index, path in enumerate(sticker_paths, 1)
    ]
    sticker_size_messages = [
        "表情圖大小：" + "、".join(sticker_size_parts[start : start + 4])
        for start in range(0, len(sticker_size_parts), 4)
    ]
    messages = [
        f"表情圖：{len(sticker_paths)} 張，240×240 PNG，全部不大於 {sticker_limit_kb}KB",
        *sticker_size_messages,
        (
            f"詳情頁橫幅：750×400 PNG，{prepared_banner.stat().st_size / 1024:.1f}KB，"
            f"不大於 {banner_limit_kb}KB"
            if prepared_banner
            else "詳情頁橫幅：缺少"
        ),
        f"封面圖：240×240 PNG，{cover_path.stat().st_size / 1024:.1f}KB，不大於 {cover_limit_kb}KB",
        (
            f"聊天面板圖標：50×50 PNG，{panel_icon_path.stat().st_size / 1024:.1f}KB，"
            f"不大於 {panel_limit_kb}KB"
        ),
    ]
    return WechatExportResult(
        zip_path=zip_path,
        zip_contents=names,
        banner_path=prepared_banner,
        cover_path=cover_path,
        panel_icon_path=panel_icon_path,
        validation_messages=messages,
        complete=prepared_banner is not None,
    )
