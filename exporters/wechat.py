"""WeChat 平台輸出。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from core.config import WECHAT_CONFIG
from core.images import StickerError, contain, load_image

from .common import save_rgba_png, write_zip


def prepare_banner(banner_path: Path, output_dir: Path) -> Path:
    if WECHAT_CONFIG.banner_size is None:
        raise RuntimeError("WECHAT_CONFIG 缺少 Banner 尺寸。")
    banner = load_image(banner_path, "WeChat Banner")
    prepared = contain(banner, WECHAT_CONFIG.banner_size, WECHAT_CONFIG.banner_padding)
    path = output_dir / "banner.png"
    save_rgba_png(prepared, path)
    return path


def export_wechat(
    stickers: list[Image.Image], output_dir: Path, banner_path: Path | None
) -> tuple[Path, list[str], Path | None]:
    staging = output_dir / "wechat"
    stickers_dir = staging / "stickers"
    banner_dir = staging / "banner"
    stickers_dir.mkdir(parents=True, exist_ok=True)
    entries: list[tuple[Path, str]] = []
    for index, sticker in enumerate(stickers, 1):
        path = stickers_dir / f"{index:02d}.png"
        save_rgba_png(sticker, path)
        entries.append((path, f"wechat/stickers/{path.name}"))

    prepared_banner: Path | None = None
    # 清除舊版暫存檔，確保輸出資料夾不殘留 manifest 或舊 Banner 名稱。
    for old_path in (staging / "manifest.json", banner_dir / "wechat_banner.png", banner_dir / "banner.png"):
        try:
            old_path.unlink(missing_ok=True)
        except OSError as exc:
            raise StickerError(f"無法清除舊版 WeChat 輸出：{old_path.name}（{exc}）") from exc
    if banner_path is not None:
        banner_dir.mkdir(parents=True, exist_ok=True)
        prepared_banner = prepare_banner(banner_path, banner_dir)
        entries.append((prepared_banner, "wechat/banner/banner.png"))
    zip_path = output_dir / WECHAT_CONFIG.zip_name
    names = write_zip(zip_path, entries)
    return zip_path, names, prepared_banner
