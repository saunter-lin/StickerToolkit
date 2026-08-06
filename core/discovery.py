"""以檔名優先、圖片規格備援探索 WeChat Banner。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from .config import WECHAT_CONFIG
from .images import StickerError

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
KNOWN_BANNER_STEMS = {"wechat_banner", "banner"}
SHEET_RATIO_RANGE = (0.75, 1.35)
BANNER_RATIO_TOLERANCE = WECHAT_CONFIG.banner_ratio_tolerance


def image_dimensions(path: Path) -> tuple[int, int]:
    """回傳套用 EXIF Orientation 後的實際尺寸。"""
    try:
        with Image.open(path) as opened:
            oriented = ImageOps.exif_transpose(opened)
            oriented.load()
            width, height = oriented.size
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise StickerError(f"無法辨識候選圖片：{path.name}（{exc}）") from exc
    if width <= 0 or height <= 0:
        raise StickerError(f"圖片尺寸錯誤：{path.name}（{width}×{height}）")
    return width, height


def image_ratio(path: Path) -> float:
    width, height = image_dimensions(path)
    return width / height


def is_known_banner_name(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS and path.stem.lower() in KNOWN_BANNER_STEMS


def is_sheet_candidate(path: Path) -> bool:
    if is_known_banner_name(path):
        return False
    ratio = image_ratio(path)
    return SHEET_RATIO_RANGE[0] <= ratio <= SHEET_RATIO_RANGE[1]


def is_banner_ratio_candidate(path: Path) -> bool:
    if WECHAT_CONFIG.banner_size is None:
        return False
    width, height = image_dimensions(path)
    target_width, target_height = WECHAT_CONFIG.banner_size
    if (width, height) == (target_width, target_height):
        return True
    if width <= height:
        return False
    target_ratio = WECHAT_CONFIG.banner_target_ratio
    actual_ratio = width / height
    ratio_difference = abs(actual_ratio - target_ratio) / target_ratio
    return ratio_difference <= WECHAT_CONFIG.banner_ratio_tolerance


def is_exact_banner_size(path: Path) -> bool:
    return image_dimensions(path) == WECHAT_CONFIG.banner_size


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
    fallback = [path for path in candidates if not is_known_banner_name(path)]
    return likely_sheets or fallback


def named_banner_candidates(folder: Path, excluded: Path) -> list[Path]:
    candidates: list[Path] = []
    for path in all_image_candidates(folder):
        if path != excluded and is_known_banner_name(path):
            image_dimensions(path)
            candidates.append(path)
    return candidates


def ratio_banner_candidates(folder: Path, excluded: Path) -> list[Path]:
    return [
        path
        for path in all_image_candidates(folder)
        if path != excluded
        and not is_known_banner_name(path)
        and not is_exact_banner_size(path)
        and is_banner_ratio_candidate(path)
    ]


def exact_banner_size_candidates(folder: Path, excluded: Path) -> list[Path]:
    return [
        path
        for path in all_image_candidates(folder)
        if path != excluded and not is_known_banner_name(path) and is_exact_banner_size(path)
    ]


def banner_candidates(folder: Path, excluded: Path) -> list[Path]:
    """回傳最高優先級候選：已知檔名優先，其次為比例。"""
    named = named_banner_candidates(folder, excluded)
    exact = exact_banner_size_candidates(folder, excluded)
    return named or exact or ratio_banner_candidates(folder, excluded)


def choose_candidate(candidates: list[Path], interactive: bool, label: str = "貼圖合集") -> Path:
    if not candidates:
        raise StickerError(f"指定資料夾中找不到可用的{label}圖片。")
    if len(candidates) == 1:
        return candidates[0]
    if not interactive and label == "貼圖合集":
        return candidates[0]
    if not interactive:
        names = "、".join(path.name for path in candidates)
        raise StickerError(f"找到多張{label}候選（{names}）；請使用 --banner 指定。")
    print(f"找到多張{label}候選：")
    for index, path in enumerate(candidates, 1):
        width, height = image_dimensions(path)
        ratio_text = f"，比例 {width / height:.3f}" if label == "Banner" else ""
        print(f"  {index}. {path.name}（{width}×{height}{ratio_text}）")
    while True:
        answer = input(f"請選擇{label}（1～{len(candidates)}）：").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(candidates):
            return candidates[int(answer) - 1]
        print("輸入無效，請輸入清單中的編號。")


def resolve_source(
    path: Path | None,
    default_folder: Path,
    interactive: bool,
    detect_banner: bool = True,
) -> tuple[Path, Path | None]:
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
    if not detect_banner:
        return source, None
    banners = banner_candidates(source.parent, source)
    banner = choose_candidate(banners, interactive, "Banner") if banners else None
    return source, banner
