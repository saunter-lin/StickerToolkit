#!/usr/bin/env python3
"""Sticker Toolkit v1.2.2 多平台貼圖匯出入口。"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image

from core.config import LINE_CONFIG, WECHAT_CONFIG
from core.discovery import resolve_source
from core.images import StickerError, build_shared_stickers, load_image
from core.paths import ProjectPaths
from exporters.common import clean_directory, save_rgba_png
from exporters.line import export_line
from exporters.wechat import export_wechat
from preview import make_line_preview, make_preview, make_wechat_preview

VERSION = "1.2.2"
ROOT = Path(__file__).resolve().parent
INPUT_DIR = ROOT / "input"
PROJECT_PATHS = ProjectPaths.from_root(ROOT)


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
        load_image(candidate, "WeChat Banner")
        return candidate
    if detected is not None:
        load_image(detected, "WeChat Banner")
        print(f"自動偵測 WeChat Banner：{detected.name}")
        return detected
    if interactive:
        while True:
            answer = input(
                "未自動偵測到 WeChat Banner；請輸入 Banner 圖片路徑，直接 Enter 可略過："
            ).strip()
            if not answer:
                break
            candidate = Path(answer).expanduser().resolve()
            if not candidate.is_file():
                print(f"路徑無效：找不到 WeChat Banner：{candidate}")
                continue
            try:
                load_image(candidate, "WeChat Banner")
            except StickerError as exc:
                print(f"路徑無效：{exc}")
                continue
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
    wechat_cover_choice: int | None,
    interactive: bool,
    open_preview: bool,
) -> None:
    PROJECT_PATHS.output.root.mkdir(exist_ok=True)
    platform = choose_platform(platform_option, interactive)
    use_line = platform in {"line", "both"}
    use_wechat = platform in {"wechat", "both"}
    source = load_image(source_path, "貼圖合集")
    print(f"選用貼圖合集：{source_path.name}")
    print("執行共用管線：Split → Trim → Safe Margin（僅執行一次）")
    stickers = build_shared_stickers(source, LINE_CONFIG.sticker_size, LINE_CONFIG.sticker_padding)

    selection_preview = make_preview(stickers)
    if use_line:
        clean_directory(PROJECT_PATHS.preview.line_directory, "LINE Preview")
        line_selection = PROJECT_PATHS.preview.line_directory / "selection.png"
        save_rgba_png(selection_preview, line_selection)
        print(f"LINE 選擇縮圖：{line_selection}")
        if open_preview:
            open_on_macos(line_selection)
    if use_wechat:
        clean_directory(PROJECT_PATHS.preview.wechat_directory, "WeChat Preview")
        wechat_selection = PROJECT_PATHS.preview.wechat_directory / "selection.png"
        save_rgba_png(selection_preview, wechat_selection)
        print(f"WeChat 選擇縮圖：{wechat_selection}")
        if open_preview:
            open_on_macos(wechat_selection)

    exported: list[tuple[str, Path]] = []
    main_index = tab_index = 1
    if use_line:
        main_index = choose_number("main.png", main_choice, interactive)
        tab_index = choose_number("tab.png", tab_choice, interactive)
        line_zip = export_line(stickers, PROJECT_PATHS.output, main_index, tab_index)
        main_image = load_image(PROJECT_PATHS.output.line_directory / "main.png", "LINE main")
        tab_image = load_image(PROJECT_PATHS.output.line_directory / "tab.png", "LINE tab")
        line_messages = [
            "LINE 貼圖：16 張，370×320 RGBA PNG",
            "main.png：240×240 RGBA PNG",
            "tab.png：96×74 RGBA PNG",
            "LINE 素材驗證通過。",
        ]
        line_preview = PROJECT_PATHS.preview.line_directory / LINE_CONFIG.preview_name
        save_rgba_png(make_line_preview(stickers, main_image, tab_image, line_messages), line_preview)
        exported.append(("LINE", line_zip))
        print(f"LINE Preview：{line_preview}")
        try:
            (PROJECT_PATHS.output.root / "preview.png").unlink(missing_ok=True)
        except OSError as exc:
            raise StickerError(f"無法清除舊版 LINE Preview（{exc}）") from exc
        if open_preview:
            open_on_macos(line_preview)

    if use_wechat:
        cover_index = choose_number("WeChat cover.png", wechat_cover_choice, interactive)
        banner_path = choose_banner(banner_option, detected_banner, interactive, True)
        result = export_wechat(stickers, PROJECT_PATHS.output, banner_path, cover_index)
        prepared_banner: Image.Image | None = None
        if result.banner_path is not None:
            prepared_banner = load_image(result.banner_path, "已處理 Banner")
        cover_image = load_image(result.cover_path, "WeChat cover")
        panel_icon = load_image(result.panel_icon_path, "WeChat panel icon")
        wechat_preview = PROJECT_PATHS.preview.wechat_directory / WECHAT_CONFIG.preview_name
        save_rgba_png(
            make_wechat_preview(
                stickers,
                prepared_banner,
                cover_image,
                panel_icon,
                result.zip_contents,
                result.validation_messages,
                result.complete,
            ),
            wechat_preview,
        )
        exported.append(("WeChat", result.zip_path))
        print(f"WeChat Preview：{wechat_preview}")
        try:
            (PROJECT_PATHS.output.root / "wechat_preview.png").unlink(missing_ok=True)
        except OSError as exc:
            raise StickerError(f"無法清除舊版 WeChat Preview（{exc}）") from exc
        for message in result.validation_messages:
            print(message)
        if result.complete:
            print("微信素材符合上傳規格。")
        else:
            print("微信素材尚未完整，可能無法直接提交。")
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
        open_on_macos(PROJECT_PATHS.output.root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"Multi Platform Sticker Toolkit v{VERSION}")
    parser.add_argument("path", nargs="?", type=Path, help="拖放的貼圖合集檔案或資料夾")
    parser.add_argument("--input", type=Path, help="指定貼圖合集檔案")
    parser.add_argument("--banner", type=Path, help="手動指定任意檔名的 WeChat Banner PNG")
    parser.add_argument("--platform", choices=("line", "wechat", "both"), help="輸出平台；預設 LINE")
    parser.add_argument("--main", type=int, help="LINE main.png 使用的貼圖編號（1～16）")
    parser.add_argument("--tab", type=int, help="LINE tab.png 使用的貼圖編號（1～16）")
    parser.add_argument("--wechat-cover", type=int, help="微信 cover.png 與 panel_icon.png 來源編號")
    parser.add_argument("--interactive", action="store_true", help="使用終端互動選擇")
    parser.add_argument("--open-preview", action="store_true", help="在 macOS 自動開啟 Preview")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.input is not None and args.path is not None:
            raise StickerError("請勿同時使用拖放路徑與 --input。")
        platform = choose_platform(args.platform, args.interactive)
        use_wechat = platform in {"wechat", "both"}
        detect_banner = use_wechat and args.banner is None
        source, detected_banner = resolve_source(
            args.input or args.path,
            INPUT_DIR,
            args.interactive,
            detect_banner=detect_banner,
        )
        process(
            source,
            detected_banner,
            platform,
            args.banner,
            args.main,
            args.tab,
            args.wechat_cover,
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
