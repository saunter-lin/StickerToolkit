"""依圖片規格探索貼圖合集與 WeChat Banner。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, UnidentifiedImageError

from .config import WECHAT_CONFIG
from .images import StickerError

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
SHEET_RATIO_RANGE = (0.75, 1.35)
BANNER_RATIO_TOLERANCE = 0.25


def image_dimensions(path: Path) -> tuple[int, int]:
    try:
        with Image.open(path) as image:
            image.verify()
            return image.size
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise StickerError(f"無法辨識候選圖片：{path.name}（{exc}）") from exc


def image_ratio(path: Path) -> float:
    width, height = image_dimensions(path)
    if width <= 0 or height <= 0:
        raise StickerError(f"圖片尺寸錯誤：{path.name}（{width}×{height}）")
    return width / height


def is_sheet_candidate(path: Path) -> bool:
    ratio = image_ratio(path)
    return SHEET_RATIO_RANGE[0] <= ratio <= SHEET_RATIO_RANGE[1]


def is_banner_candidate(path: Path) -> bool:
    if path.suffix.lower() != ".png" or WECHAT_CONFIG.banner_size is None:
        return False
    target_ratio = WECHAT_CONFIG.banner_size[0] / WECHAT_CONFIG.banner_size[1]
    ratio = image_ratio(path)
    minimum = target_ratio * (1 - BANNER_RATIO_TOLERANCE)
    maximum = target_ratio * (1 + BANNER_RATIO_TOLERANCE)
    return minimum <= ratio <= maximum


def all_image_candidates(folder: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ),
        key=lambda path: (-path.stat().st_mtime_ns, path.name.lower()),
    )


def sheet_candidates(folder: Path) -> list[Path]:
    candidates = all_image_candidates(folder)
    likely_sheets = [path for path in candidates if is_sheet_candidate(path)]
    return likely_sheets or candidates


def banner_candidates(folder: Path, excluded: Path) -> list[Path]:
    return [
        path
        for path in all_image_candidates(folder)
        if path != excluded and is_banner_candidate(path)
    ]


def choose_candidate(candidates: list[Path], interactive: bool, label: str = "貼圖合集") -> Path:
    if not candidates:
        raise StickerError(f"指定資料夾中找不到可用的{label}圖片。")
    if len(candidates) == 1:
        return candidates[0]
    if not interactive and label == "貼圖合集":
        # 保留 v1 行為：非互動模式使用最後修改時間最新者。
        return candidates[0]
    if not interactive:
        names = "、".join(path.name for path in candidates)
        raise StickerError(f"找到多張{label}候選（{names}）；請使用 --banner 指定。")
    print(f"找到多張{label}候選：")
    for index, path in enumerate(candidates, 1):
        width, height = image_dimensions(path)
        print(f"  {index}. {path.name}（{width}×{height}）")
    while True:
        answer = input(f"請選擇{label}（1～{len(candidates)}）：").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(candidates):
            return candidates[int(answer) - 1]
        print("輸入無效，請輸入清單中的編號。")


def resolve_source(path: Path | None, default_folder: Path, interactive: bool) -> tuple[Path, Path | None]:
    target = (path or default_folder).expanduser().resolve()
    if not target.exists():
        raise StickerError(f"找不到輸入路徑：{target}")
    if target.is_file():
        if target.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise StickerError(f"指定檔案不是支援的貼圖合集：{target.name}")
        source = target
    elif target.is_dir():
        source = choose_candidate(sheet_candidates(target), interactive)
    else:
        raise StickerError(f"輸入路徑不是檔案或資料夾：{target}")
    banners = banner_candidates(source.parent, source)
    banner = choose_candidate(banners, interactive, "Banner") if banners else None
    return source, banner
