"""輸入合集與 WeChat Banner 探索。"""

from __future__ import annotations

from pathlib import Path

from .images import StickerError

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
BANNER_NAME = "wechat_banner.png"


def find_banner(folder: Path) -> Path | None:
    return next(
        (path for path in folder.iterdir() if path.is_file() and path.name.lower() == BANNER_NAME),
        None,
    )


def sheet_candidates(folder: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in folder.iterdir()
            if path.is_file()
            and path.suffix.lower() in SUPPORTED_EXTENSIONS
            and path.name.lower() != BANNER_NAME
        ),
        key=lambda path: (-path.stat().st_mtime_ns, path.name.lower()),
    )


def choose_candidate(candidates: list[Path], interactive: bool) -> Path:
    if not candidates:
        raise StickerError("指定資料夾中找不到可用的 PNG、JPG 或 JPEG 貼圖合集。")
    if len(candidates) == 1:
        return candidates[0]
    if not interactive:
        # 保留 v1 行為：非互動模式使用最後修改時間最新者。
        return candidates[0]
    print("找到多張貼圖合集候選：")
    for index, path in enumerate(candidates, 1):
        print(f"  {index}. {path.name}")
    while True:
        answer = input(f"請選擇貼圖合集（1～{len(candidates)}）：").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(candidates):
            return candidates[int(answer) - 1]
        print("輸入無效，請輸入清單中的編號。")


def resolve_source(path: Path | None, default_folder: Path, interactive: bool) -> tuple[Path, Path | None]:
    target = (path or default_folder).expanduser().resolve()
    if not target.exists():
        raise StickerError(f"找不到輸入路徑：{target}")
    if target.is_file():
        if target.name.lower() == BANNER_NAME or target.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise StickerError(f"指定檔案不是貼圖合集：{target.name}")
        return target, find_banner(target.parent)
    if not target.is_dir():
        raise StickerError(f"輸入路徑不是檔案或資料夾：{target}")
    return choose_candidate(sheet_candidates(target), interactive), find_banner(target)
