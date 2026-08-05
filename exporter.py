"""Sticker Toolkit 輸出驗證與 ZIP 打包。"""

import zipfile
from pathlib import Path

from PIL import Image


def validate_png(path: Path, expected_size: tuple[int, int]) -> None:
    with Image.open(path) as image:
        if image.format != "PNG" or image.mode != "RGBA" or image.size != expected_size:
            raise RuntimeError(
                f"{path.name} 格式錯誤：{image.format}/{image.mode}/{image.size}，預期 PNG/RGBA/{expected_size}。"
            )
        bbox = image.getchannel("A").getbbox()
        if bbox is None:
            raise RuntimeError(f"{path.name} 沒有可見內容。")
        if not (0 <= bbox[0] < bbox[2] <= expected_size[0] and 0 <= bbox[1] < bbox[3] <= expected_size[1]):
            raise RuntimeError(f"{path.name} 存在內容超出畫布的情況。")


def create_zip(zip_path: Path, paths: list[Path]) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, path.name)
