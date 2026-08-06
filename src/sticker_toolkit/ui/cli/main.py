"""只處理互動、參數解析與結果顯示的 CLI adapter。"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

from core.discovery import resolve_source
from core.images import StickerError, load_image
from exporters.common import remove_directory
from sticker_toolkit.core import ProcessingOptions, ProcessingResult, StickerToolkitError
from sticker_toolkit.services import StickerService
from sticker_toolkit.version import __version__


def choose_number(label: str, supplied: int | None, interactive: bool) -> int:
    if supplied is not None:
        if 1 <= supplied <= 16:
            return supplied
        raise StickerToolkitError(f"{label} 必須是 1～16。")
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
            raise StickerToolkitError(f"找不到 WeChat Banner：{candidate}")
        try:
            load_image(candidate, "WeChat Banner")
        except StickerError as exc:
            raise StickerToolkitError(str(exc)) from exc
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


def console_progress(value: int, message: str) -> None:
    print(f"[{value:3d}%] {message}")


def display_result(result: ProcessingResult, options: ProcessingOptions) -> None:
    print("\n====================================")
    print(f"Sticker Toolkit v{__version__} Export Finished")
    print(f"Input：\n{result.source_path.name}")
    print("Sticker：\n16")
    print(f"Platform：\n{options.platform}")
    if options.platform in {"line", "both"}:
        print(f"Main：\n{options.main_index:02d}.png")
        print(f"Tab：\n{options.tab_index:02d}.png")
    print(f"Output：\n{options.output_directory}")
    for platform in result.platforms:
        if platform.preview_file:
            print(f"{platform.platform} Preview：\n{platform.preview_file}")
        if platform.zip_file:
            print(f"{platform.platform} ZIP：\n{platform.zip_file.name}")
    for warning in result.warnings:
        print(f"警告：{warning}")
    print("====================================")


def run_process(
    source_path: Path,
    detected_banner: Path | None,
    platform_option: str | None,
    banner_option: Path | None,
    main_choice: int | None,
    tab_choice: int | None,
    wechat_cover_choice: int | None,
    interactive: bool,
    open_preview: bool,
    output_directory: Path,
) -> ProcessingResult:
    platform = choose_platform(platform_option, interactive)
    use_line = platform in {"line", "both"}
    use_wechat = platform in {"wechat", "both"}
    banner = choose_banner(banner_option, detected_banner, interactive, use_wechat)
    options = ProcessingOptions(
        platform=platform,
        output_directory=output_directory,
        main_index=choose_number("main.png", main_choice, False) if use_line else 1,
        tab_index=choose_number("tab.png", tab_choice, False) if use_line else 1,
        wechat_cover_index=(
            choose_number("WeChat cover.png", wechat_cover_choice, False)
            if use_wechat
            else 1
        ),
        banner_path=banner,
    )

    def select_after_preview(
        current: ProcessingOptions, selection_files: tuple[Path, ...]
    ) -> ProcessingOptions:
        if open_preview:
            for preview_file in selection_files:
                open_on_macos(preview_file)
        return replace(
            current,
            main_index=(choose_number("main.png", main_choice, True) if use_line else 1),
            tab_index=(choose_number("tab.png", tab_choice, True) if use_line else 1),
            wechat_cover_index=(
                choose_number("WeChat cover.png", wechat_cover_choice, True)
                if use_wechat
                else 1
            ),
        )

    if output_directory.name == "output":
        remove_directory(output_directory.parent / "preview", "舊版 Preview")
    result = StickerService().process(
        source_path,
        options,
        console_progress,
        select_after_preview if interactive else None,
    )
    display_result(result, options)
    if open_preview:
        for platform_result in result.platforms:
            if platform_result.preview_file:
                open_on_macos(platform_result.preview_file)
        open_on_macos(output_directory)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"Multi Platform Sticker Toolkit v{__version__}")
    parser.add_argument("path", nargs="?", type=Path, help="拖放的貼圖合集檔案或資料夾")
    parser.add_argument("--input", type=Path, help="指定貼圖合集檔案")
    parser.add_argument("--banner", type=Path, help="手動指定任意檔名的 WeChat Banner")
    parser.add_argument("--platform", choices=("line", "wechat", "both"), help="輸出平台")
    parser.add_argument("--main", type=int, help="LINE main.png 來源編號（1～16）")
    parser.add_argument("--tab", type=int, help="LINE tab.png 來源編號（1～16）")
    parser.add_argument("--wechat-cover", type=int, help="微信 cover 與 panel icon 來源編號")
    parser.add_argument("--output", type=Path, default=Path("output"), help="輸出目錄")
    parser.add_argument("--interactive", action="store_true", help="使用終端互動選擇")
    parser.add_argument("--open-preview", action="store_true", help="在 macOS 自動開啟 Preview")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.input is not None and args.path is not None:
            raise StickerToolkitError("請勿同時使用拖放路徑與 --input。")
        platform = choose_platform(args.platform, args.interactive)
        use_wechat = platform in {"wechat", "both"}
        source, detected_banner = resolve_source(
            args.input or args.path,
            Path("input"),
            args.interactive,
            detect_banner=use_wechat and args.banner is None,
        )
        run_process(
            source,
            detected_banner,
            platform,
            args.banner,
            args.main,
            args.tab,
            args.wechat_cover,
            args.interactive,
            args.open_preview,
            args.output.expanduser().resolve(),
        )
        return 0
    except (StickerToolkitError, StickerError) as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
    except Exception as exc:
        print(f"錯誤：未預期的處理失敗（{exc}）", file=sys.stderr)
    return 1
