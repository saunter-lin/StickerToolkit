"""平台共用的輸出驗證與 ZIP 寫入。"""

from __future__ import annotations

import zipfile
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from core.images import StickerError


def save_rgba_png(image: Image.Image, path: Path) -> None:
    try:
        image.convert("RGBA").save(path, "PNG")
    except OSError as exc:
        raise StickerError(f"無法寫入 PNG：{path.name}（{exc}）") from exc


def save_optimized_png(image: Image.Image, path: Path, max_bytes: int, error_message: str) -> None:
    """先做無損壓縮，超限時再以逐級色盤最佳化降低 PNG 大小。"""
    rgba = image.convert("RGBA")
    try:
        rgba.save(path, "PNG", optimize=True, compress_level=9)
        if path.stat().st_size <= max_bytes:
            return
        for colors in (256, 128, 64, 32):
            optimized = rgba.quantize(
                colors=colors,
                method=Image.Quantize.FASTOCTREE,
                dither=Image.Dither.FLOYDSTEINBERG,
            )
            optimized.save(path, "PNG", optimize=True, compress_level=9)
            if path.stat().st_size <= max_bytes:
                return
    except OSError as exc:
        raise StickerError(f"無法寫入 PNG：{path.name}（{exc}）") from exc
    raise StickerError(error_message)


def validate_png(path: Path, expected_size: tuple[int, int]) -> None:
    try:
        with Image.open(path) as image:
            image.load()
            if image.format != "PNG" or image.mode != "RGBA" or image.size != expected_size:
                raise StickerError(
                    f"{path.name} 規格錯誤：{image.format}/{image.mode}/{image.size}，"
                    f"預期 PNG/RGBA/{expected_size}。"
                )
            if image.getchannel("A").getbbox() is None:
                raise StickerError(f"{path.name} 完全透明。")
    except (UnidentifiedImageError, OSError) as exc:
        raise StickerError(f"PNG 驗證失敗：{path.name}（{exc}）") from exc


def write_zip(zip_path: Path, entries: list[tuple[Path, str]]) -> list[str]:
    try:
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for source, archive_name in entries:
                archive.write(source, archive_name)
        return [archive_name for _, archive_name in entries]
    except (OSError, zipfile.BadZipFile) as exc:
        raise StickerError(f"ZIP 建立失敗：{zip_path.name}（{exc}）") from exc
