"""WeChat 平台輸出。"""

from __future__ import annotations

import json
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
    path = output_dir / "wechat_banner.png"
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
    if banner_path is not None:
        banner_dir.mkdir(parents=True, exist_ok=True)
        prepared_banner = prepare_banner(banner_path, banner_dir)
        entries.append((prepared_banner, "wechat/banner/wechat_banner.png"))

    manifest = {
        "format_version": "1.0",
        "platform": "WeChat",
        "tool_version": "1.2.0",
        "sticker_count": len(stickers),
        "stickers": [f"stickers/{index:02d}.png" for index in range(1, len(stickers) + 1)],
        "banner": "banner/wechat_banner.png" if prepared_banner else None,
        "notes": "Banner 尺寸為工具暫定值；請依最新微信官方規格確認。",
    }
    manifest_path = staging / "manifest.json"
    try:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise StickerError(f"manifest.json 建立失敗：{exc}") from exc
    entries.append((manifest_path, "wechat/manifest.json"))
    zip_path = output_dir / WECHAT_CONFIG.zip_name
    names = write_zip(zip_path, entries)
    return zip_path, names, prepared_banner
