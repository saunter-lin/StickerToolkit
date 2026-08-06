#!/usr/bin/env python3
"""Sticker Toolkit v1.2.0 多平台貼圖匯出入口。"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image

from core.config import LINE_CONFIG, WECHAT_CONFIG
from core.discovery import resolve_source
from core.images import StickerError, build_shared_stickers, load_image
from exporters.common import save_rgba_png
from exporters.line import export_line
from exporters.wechat import export_wechat
from preview import make_preview, make_wechat_preview

VERSION = "1.2.0"
ROOT = Path(__file__).resolve().parent
INPUT_DIR = ROOT / "input"
OUTPUT_DIR = ROOT / "output"


def choose_number(label: str, supplied: int | None, interactive: bool) -> int:
    if supplied is not None:
        if 1 <= supplied <= 16:
            return supplied
        raise StickerError(f"{label} 必須是 1～16。")
    if not interactive:
        return 1
    while True:
        answer = input(f"請選擇 {label} 使用的貼圖（1～16，直接 Enter 使用 01）：").strip()
        if not answer:
            return 1
        if answer.isdigit() and 1 <= int(answer) <= 16:
            return int(answer)
        print("輸入無效，請輸入 1～16。")


def choose_platform(supplied: str | None, interactive: bool) -> str:
    if supplied:
        return supplied
    if not interactive:
        return "line"
    print("輸出平台：1. LINE（預設）  2. WeChat  3. LINE + WeChat")
    while True:
        answer = input("請選擇輸出平台（1～3，直接 Enter 使用 LINE）：").strip()
        mapping = {"": "line", "1": "line", "2": "wechat", "3": "both"}
        if answer in mapping:
            return mapping[answer]
        print("輸入無效，請輸入 1、2 或 3。")


def choose_banner(
    supplied: Path | None, detected: Path | None, interactive: bool, enabled: bool
) -> Path | None:
    if not enabled:
        return None
    if supplied is not None:
        candidate = supplied.expanduser().resolve()
        if not candidate.is_file():
            raise StickerError(f"找不到 WeChat Banner：{candidate}")
        return candidate
    if detected is not None:
        print(f"依圖片規格自動偵測 WeChat Banner：{detected.name}")
        return detected
    if interactive:
        answer = input("未偵測到符合比例的 Banner；可輸入 Banner 路徑，直接 Enter 略過：").strip()
        if answer:
            candidate = Path(answer).expanduser().resolve()
            if not candidate.is_file():
                raise StickerError(f"找不到 WeChat Banner：{candidate}")
            return candidate
    print("警告：未提供 WeChat Banner，將省略 Banner 並繼續輸出。")
    return None


def open_on_macos(path: Path) -> None:
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)


def process(
    source_path: Path,
    detected_banner: Path | None,
    platform_option: str | None,
    banner_option: Path | None,
    main_choice: int | None,
    tab_choice: int | None,
    interactive: bool,
    open_preview: bool,
) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    platform = choose_platform(platform_option, interactive)
    use_line = platform in {"line", "both"}
    use_wechat = platform in {"wechat", "both"}
    source = load_image(source_path, "貼圖合集")
    print(f"選用貼圖合集：{source_path.name}")
    print("執行共用管線：Split → Trim → Safe Margin（僅執行一次）")
    stickers = build_shared_stickers(source, LINE_CONFIG.sticker_size, LINE_CONFIG.sticker_padding)

    line_preview = OUTPUT_DIR / LINE_CONFIG.preview_name
    save_rgba_png(make_preview(stickers), line_preview)
    print(f"16 張貼圖縮圖已建立：{line_preview}")
    if open_preview:
        open_on_macos(line_preview)

    exported: list[tuple[str, Path]] = []
    main_index = tab_index = 1
    if use_line:
        main_index = choose_number("main.png", main_choice, interactive)
        tab_index = choose_number("tab.png", tab_choice, interactive)
        exported.append(("LINE", export_line(stickers, OUTPUT_DIR, main_index, tab_index)))

    if use_wechat:
        banner_path = choose_banner(banner_option, detected_banner, interactive, True)
        zip_path, zip_contents, prepared_banner_path = export_wechat(stickers, OUTPUT_DIR, banner_path)
        prepared_banner: Image.Image | None = None
        if prepared_banner_path is not None:
            prepared_banner = load_image(prepared_banner_path, "已處理 Banner")
        wechat_preview = OUTPUT_DIR / WECHAT_CONFIG.preview_name
        save_rgba_png(make_wechat_preview(stickers, prepared_banner, zip_contents), wechat_preview)
        exported.append(("WeChat", zip_path))
        print(f"WeChat Preview：{wechat_preview}")
        if open_preview:
            open_on_macos(wechat_preview)

    print("\n====================================")
    print(f"Sticker Toolkit v{VERSION} Export Finished")
    print(f"Input：\n{source_path.name}")
    print("Sticker：\n16")
    print(f"Platform：\n{platform}")
    if use_line:
        print(f"Main：\n{main_index:02d}.png")
        print(f"Tab：\n{tab_index:02d}.png")
    print("Output：\noutput/")
    for label, zip_path in exported:
        print(f"{label} ZIP：\n{zip_path.name}")
    print("====================================")
    if open_preview:
        open_on_macos(OUTPUT_DIR)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"Multi Platform Sticker Toolkit v{VERSION}")
    parser.add_argument("path", nargs="?", type=Path, help="拖放的貼圖合集檔案或資料夾")
    parser.add_argument("--input", type=Path, help="指定貼圖合集檔案")
    parser.add_argument("--banner", type=Path, help="手動指定任意檔名的 WeChat Banner PNG")
    parser.add_argument("--platform", choices=("line", "wechat", "both"), help="輸出平台；預設 LINE")
    parser.add_argument("--main", type=int, help="LINE main.png 使用的貼圖編號（1～16）")
    parser.add_argument("--tab", type=int, help="LINE tab.png 使用的貼圖編號（1～16）")
    parser.add_argument("--interactive", action="store_true", help="使用終端互動選擇")
    parser.add_argument("--open-preview", action="store_true", help="在 macOS 自動開啟 Preview")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.input is not None and args.path is not None:
            raise StickerError("請勿同時使用拖放路徑與 --input。")
        source, detected_banner = resolve_source(args.input or args.path, INPUT_DIR, args.interactive)
        process(
            source,
            detected_banner,
            args.platform,
            args.banner,
            args.main,
            args.tab,
            args.interactive,
            args.open_preview,
        )
        return 0
    except StickerError as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
    except Exception as exc:
        print(f"錯誤：未預期的處理失敗（{exc}）", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
