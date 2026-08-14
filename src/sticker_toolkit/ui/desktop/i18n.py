# ruff: noqa: E501
"""Desktop GUI translations with stable keys and English fallback."""

from __future__ import annotations

import re
from collections.abc import Mapping

DEFAULT_LANGUAGE = "en"
LANGUAGE_LABELS = {
    "zh_TW": "繁體中文",
    "zh_CN": "简体中文",
    "en": "English",
}

_EN = {
    "window.title": "Sticker Toolkit {version}",
    "language.label": "Language:",
    "group.input": "Input Mode",
    "group.source": "Source Images",
    "group.platform": "Output Platform",
    "group.line_cover": "LINE Cover Image",
    "group.wechat_cover": "WeChat Cover Image",
    "group.grid": "Grid Settings",
    "group.banner": "WeChat Banner",
    "group.output": "Output Location",
    "group.options": "Processing Options",
    "group.background": "Solid Background to Alpha",
    "label.mode": "Mode:",
    "label.platform": "Platform:",
    "label.rows": "Rows:",
    "label.columns": "Columns:",
    "label.background_color": "Background color:",
    "label.tolerance": "Tolerance:",
    "mode.sheet": "4×4 Sticker Sheet",
    "mode.batch": "WeChat 16-image Batch",
    "platform.line": "LINE",
    "platform.line_animated": "LINE Animated",
    "platform.wechat": "WeChat",
    "platform.both": "LINE + WeChat",
    "cover.auto": "Automatic",
    "cover.custom": "Custom image",
    "button.choose_image": "Choose Image",
    "button.choose_16": "Choose Images",
    "button.up": "↑ Move Up",
    "button.down": "↓ Move Down",
    "button.remove": "Remove",
    "button.choose": "Choose",
    "button.clear": "Clear",
    "button.choose_directory": "Choose Folder",
    "button.choose_color": "Choose Color",
    "button.start": "Start Processing",
    "button.open_output": "Open Output Folder",
    "batch.count": "Selected {count} / 16 images",
    "placeholder.source": "No source image selected",
    "placeholder.banner": "Optional for 4×4 mode; required for Batch",
    "placeholder.output": "Output location is suggested after choosing source images",
    "placeholder.cover.choose": "Choose a cover image",
    "placeholder.cover.auto": "Generated automatically",
    "placeholder.result": "Processing results appear here",
    "option.trim": "Trim empty margins",
    "option.padding": "Keep safe padding",
    "option.preview": "Create Preview",
    "option.zip": "Create ZIP",
    "option.remove_background": "Remove solid background",
    "option.auto_background": "Auto-detect background color (recommended)",
    "tooltip.remove_background": "Removes only the selected color connected to the canvas boundary. Best for flat-color sticker sheets; this is not AI background removal.",
    "tooltip.tolerance": "Higher values remove more similar colors but may affect light details. Recommended: 3–5 for PNG, 10–15 for JPEG or compression variation.",
    "status.waiting": "Ready",
    "status.starting": "Starting processing…",
    "status.completed": "Processing completed",
    "status.failed": "Processing failed",
    "dialog.images": "Images (*.png *.jpg *.jpeg)",
    "dialog.images_webp": "Images (*.png *.jpg *.jpeg *.webp)",
    "dialog.choose_batch": "Choose WeChat sticker images",
    "dialog.choose_sheet": "Choose Sticker Sheet",
    "dialog.choose_background": "Choose Solid Background Color",
    "dialog.choose_cover": "Choose Cover Image",
    "dialog.choose_banner": "Choose WeChat Banner",
    "dialog.choose_output": "Choose Output Root",
    "dialog.input_incomplete": "Incomplete Input",
    "dialog.completed.title": "Processing Completed",
    "dialog.completed.body": "Sticker assets were exported successfully.",
    "dialog.failed": "Processing Failed",
    "dialog.output_failed": "Cannot Open Output Folder",
    "dialog.processing": "Processing in Progress",
    "dialog.processing_wait": "Please wait for the current processing task to finish.",
    "background.detected": "Detected background color: {color}",
    "background.fallback": "Not detected automatically; using {color}",
    "validation.input_mode": "Please select a valid input mode.",
    "validation.batch_few": "WeChat Batch currently has {count} images; 16 are required.",
    "validation.batch_many": "WeChat Batch currently has {count} images. Use Remove to reduce the list to 16.",
    "validation.batch_platform": "WeChat Batch supports WeChat output only.",
    "validation.batch_banner": "WeChat Batch requires a Banner.",
    "validation.batch_missing": "Batch image not found: {name}",
    "validation.source_required": "Please choose a source image.",
    "validation.platform": "Please select LINE, LINE Animated, WeChat, or LINE + WeChat.",
    "validation.grid_positive": "Rows and columns must be positive integers.",
    "validation.grid_4x4": "This version supports 4 × 4 sticker sheets only.",
    "validation.source_missing": "Source image not found. Please choose it again.",
    "validation.output_required": "Please choose an output root.",
    "validation.output_writable": "The output location is not writable. Please choose another folder.",
    "validation.banner_missing": "WeChat Banner not found. Please choose it again or clear it.",
    "validation.cover_missing": "{label} image not found. Please choose it again or clear it.",
    "validation.tolerance": "Solid-background tolerance must be between 0 and 30.",
    "error.invalid_source": "Cannot read the source image. Check that the file format is supported.",
    "error.invalid_grid": "Invalid grid settings. Check rows and columns.",
    "error.output": "The output location is not writable. Please choose another folder.",
    "error.generic": "Processing failed. See the log for details.",
    "error.unexpected_title": "Sticker Toolkit Error",
    "error.unexpected": "An unexpected error occurred. Details were written to the local log.\n\n{error}",
    "summary.completed": "Processing completed",
    "summary.platforms": "Platforms: {platforms}",
    "summary.stickers": "{platform} stickers: {count}",
    "summary.directory": "{platform} folder: {path}",
    "summary.zip": "{platform} ZIP: {path}",
    "summary.preview": "{platform} Preview: {path}",
    "summary.warning": "Warning: {warning}",
    "summary.not_created": "Not created",
    "progress.prepare": "Preparing",
    "progress.read_batch": "Reading batch images",
    "progress.batch_item": "Processing batch image {index} / {total}",
    "progress.read_image": "Reading image",
    "progress.remove_background": "Removing connected solid background",
    "progress.split": "Splitting and processing stickers",
    "progress.line_assets": "Creating LINE assets",
    "progress.line_preview": "Creating LINE Preview",
    "progress.line_animated_assets": "Creating LINE animation frames",
    "progress.line_animated_preview": "Creating LINE animation Preview",
    "progress.wechat_assets": "Creating WeChat assets",
    "progress.wechat_preview": "Creating WeChat Preview",
    "progress.complete": "Processing completed",
}

_ZH_TW = {
    **_EN,
    "language.label": "語言：",
    "group.input": "輸入模式",
    "group.source": "來源圖片",
    "group.platform": "輸出平台",
    "group.line_cover": "LINE 封面圖片",
    "group.wechat_cover": "WeChat 封面圖片",
    "group.grid": "圖片切割設定",
    "group.banner": "WeChat Banner",
    "group.output": "輸出位置",
    "group.options": "處理選項",
    "group.background": "純色背景轉透明",
    "label.mode": "模式：",
    "label.platform": "平台：",
    "label.rows": "行數：",
    "label.columns": "列數：",
    "label.background_color": "背景色：",
    "label.tolerance": "容差：",
    "mode.sheet": "4×4 貼圖組圖",
    "mode.batch": "WeChat 16 張單圖 Batch",
    "platform.both": "LINE＋WeChat",
    "platform.line_animated": "LINE 動圖",
    "cover.auto": "自動產生",
    "cover.custom": "自選圖片",
    "button.choose_image": "選擇圖片",
    "button.choose_16": "選擇圖片",
    "button.up": "↑ 上移",
    "button.down": "↓ 下移",
    "button.remove": "移除",
    "button.choose": "選擇",
    "button.clear": "清除",
    "button.choose_directory": "選擇目錄",
    "button.choose_color": "選擇顏色",
    "button.start": "開始處理",
    "button.open_output": "開啟輸出資料夾",
    "batch.count": "已選擇 {count} / 16 張",
    "placeholder.source": "尚未選擇來源圖片",
    "placeholder.banner": "4×4 模式可略過；Batch 模式必填",
    "placeholder.output": "選擇來源圖片後自動建議輸出位置",
    "placeholder.cover.choose": "請選擇封面圖片",
    "placeholder.cover.auto": "自動產生",
    "placeholder.result": "處理結果會顯示在這裡",
    "option.trim": "去除空白邊",
    "option.padding": "保留安全留白",
    "option.preview": "建立預覽圖",
    "option.zip": "建立 ZIP",
    "option.remove_background": "去除純色背景",
    "option.auto_background": "自動偵測背景色（推薦）",
    "tooltip.remove_background": "只移除與畫布外部連通的指定背景色，適合固定純色背景的貼圖組圖；不是 AI 去背。",
    "tooltip.tolerance": "數值越高，越容易移除近似背景色，但也可能誤刪淺色細節。純色 PNG 建議 3～5；JPEG 或有壓縮色差的圖片可使用 10～15。",
    "status.waiting": "等待開始",
    "status.starting": "正在啟動處理…",
    "status.completed": "處理完成",
    "status.failed": "處理失敗",
    "dialog.images": "圖片 (*.png *.jpg *.jpeg)",
    "dialog.images_webp": "圖片 (*.png *.jpg *.jpeg *.webp)",
    "dialog.choose_batch": "選擇 WeChat 貼圖圖片",
    "dialog.choose_sheet": "選擇貼圖組圖",
    "dialog.choose_background": "選擇純色背景",
    "dialog.choose_cover": "選擇封面圖片",
    "dialog.choose_banner": "選擇 WeChat Banner",
    "dialog.choose_output": "選擇輸出根目錄",
    "dialog.input_incomplete": "輸入資料不完整",
    "dialog.completed.title": "處理完成",
    "dialog.completed.body": "貼圖素材已成功輸出。",
    "dialog.failed": "處理失敗",
    "dialog.output_failed": "無法開啟輸出目錄",
    "dialog.processing": "處理進行中",
    "dialog.processing_wait": "請等待目前的圖片處理完成。",
    "background.detected": "偵測到背景色：{color}",
    "background.fallback": "未自動偵測；使用 {color}",
    "validation.input_mode": "請選擇有效的輸入模式。",
    "validation.batch_few": "WeChat 批次單圖目前只有 {count} 張，尚不足 16 張。",
    "validation.batch_many": "WeChat 批次單圖目前有 {count} 張，請先使用「移除」整理至 16 張。",
    "validation.batch_platform": "WeChat 批次單圖模式僅支援 WeChat 輸出。",
    "validation.batch_banner": "WeChat 批次單圖模式必須選擇 Banner。",
    "validation.batch_missing": "找不到批次圖片：{name}",
    "validation.source_required": "請先選擇來源圖片。",
    "validation.platform": "請選擇 LINE、LINE 動圖、WeChat 或 LINE＋WeChat。",
    "validation.grid_positive": "切割設定必須為正整數，且不可為 0。",
    "validation.grid_4x4": "目前版本僅支援 4 × 4 貼圖組圖。",
    "validation.source_missing": "找不到來源圖片，請重新選擇。",
    "validation.output_required": "請選擇輸出根目錄。",
    "validation.output_writable": "輸出目錄無法寫入，請選擇其他位置。",
    "validation.banner_missing": "找不到 WeChat Banner 圖片，請重新選擇或清除。",
    "validation.cover_missing": "找不到{label}圖片，請重新選擇或清除。",
    "validation.tolerance": "純色背景容差必須介於 0～30。",
    "error.invalid_source": "無法讀取來源圖片，請確認檔案格式是否正確。",
    "error.invalid_grid": "切割設定不正確，請確認行數與列數。",
    "error.output": "輸出目錄無法寫入，請選擇其他位置。",
    "error.generic": "處理失敗，請查看記錄檔取得詳細資訊。",
    "error.unexpected_title": "Sticker Toolkit 發生錯誤",
    "error.unexpected": "程式發生未預期錯誤。詳細資訊已寫入本機記錄檔。\n\n{error}",
    "summary.completed": "處理完成",
    "summary.platforms": "輸出平台：{platforms}",
    "summary.stickers": "{platform} 貼圖：{count} 張",
    "summary.directory": "{platform} 目錄：{path}",
    "summary.zip": "{platform} ZIP：{path}",
    "summary.preview": "{platform} Preview：{path}",
    "summary.warning": "警告：{warning}",
    "summary.not_created": "未建立",
    "progress.prepare": "準備處理",
    "progress.read_batch": "正在讀取批次圖片",
    "progress.batch_item": "正在處理批次圖片 {index} / {total}",
    "progress.read_image": "正在讀取圖片",
    "progress.remove_background": "正在移除外部連通的純色背景",
    "progress.split": "正在切割與處理貼圖",
    "progress.line_assets": "正在產生 LINE 素材",
    "progress.line_preview": "正在產生 LINE 預覽",
    "progress.line_animated_assets": "正在產生 LINE 動圖 frames",
    "progress.line_animated_preview": "正在產生 LINE 動圖預覽",
    "progress.wechat_assets": "正在產生 WeChat 素材",
    "progress.wechat_preview": "正在產生 WeChat 預覽",
    "progress.complete": "處理完成",
}

_ZH_CN = {key: value for key, value in _ZH_TW.items()}
_ZH_CN.update(
    {
        "language.label": "语言：",
        "group.input": "输入模式",
        "group.source": "来源图片",
        "group.platform": "输出平台",
        "group.line_cover": "LINE 封面图片",
        "group.wechat_cover": "WeChat 封面图片",
        "group.grid": "图片切割设置",
        "group.output": "输出位置",
        "group.options": "处理选项",
        "group.background": "纯色背景转透明",
        "label.rows": "行数：",
        "label.columns": "列数：",
        "label.background_color": "背景色：",
        "label.tolerance": "容差：",
        "mode.sheet": "4×4 贴图组图",
        "mode.batch": "WeChat 16 张单图 Batch",
        "platform.both": "LINE＋WeChat",
        "platform.line_animated": "LINE 动图",
        "cover.auto": "自动生成",
        "cover.custom": "自选图片",
        "button.choose_image": "选择图片",
        "button.choose_16": "选择图片",
        "button.up": "↑ 上移",
        "button.down": "↓ 下移",
        "button.remove": "移除",
        "button.choose": "选择",
        "button.clear": "清除",
        "button.choose_directory": "选择目录",
        "button.choose_color": "选择颜色",
        "button.start": "开始处理",
        "button.open_output": "打开输出文件夹",
        "batch.count": "已选择 {count} / 16 张",
        "placeholder.source": "尚未选择来源图片",
        "placeholder.banner": "4×4 模式可跳过；Batch 模式必填",
        "placeholder.output": "选择来源图片后自动建议输出位置",
        "placeholder.cover.choose": "请选择封面图片",
        "placeholder.cover.auto": "自动生成",
        "placeholder.result": "处理结果会显示在这里",
        "option.trim": "去除空白边",
        "option.padding": "保留安全留白",
        "option.preview": "创建预览图",
        "option.zip": "创建 ZIP",
        "option.remove_background": "去除纯色背景",
        "option.auto_background": "自动检测背景色（推荐）",
        "tooltip.remove_background": "只移除与画布外部连通的指定背景色，适合固定纯色背景的贴图组图；不是 AI 抠图。",
        "tooltip.tolerance": "数值越高，越容易移除近似背景色，但也可能误删浅色细节。纯色 PNG 建议 3～5；JPEG 或有压缩色差的图片可使用 10～15。",
        "status.waiting": "等待开始",
        "status.starting": "正在启动处理…",
        "status.completed": "处理完成",
        "status.failed": "处理失败",
        "dialog.images": "图片 (*.png *.jpg *.jpeg)",
        "dialog.images_webp": "图片 (*.png *.jpg *.jpeg *.webp)",
        "dialog.choose_batch": "选择 WeChat 贴图图片",
        "dialog.choose_sheet": "选择贴图组图",
        "dialog.choose_background": "选择纯色背景",
        "dialog.choose_cover": "选择封面图片",
        "dialog.choose_banner": "选择 WeChat Banner",
        "dialog.choose_output": "选择输出根目录",
        "dialog.input_incomplete": "输入信息不完整",
        "dialog.completed.title": "处理完成",
        "dialog.completed.body": "贴图素材已成功输出。",
        "dialog.failed": "处理失败",
        "dialog.output_failed": "无法打开输出目录",
        "dialog.processing": "正在处理",
        "dialog.processing_wait": "请等待当前图片处理完成。",
        "background.detected": "检测到背景色：{color}",
        "background.fallback": "未自动检测；使用 {color}",
        "validation.input_mode": "请选择有效的输入模式。",
        "validation.batch_few": "WeChat 批次单图目前只有 {count} 张，不足 16 张。",
        "validation.batch_many": "WeChat 批次单图目前有 {count} 张，请先使用“移除”整理至 16 张。",
        "validation.batch_platform": "WeChat 批次单图模式仅支持 WeChat 输出。",
        "validation.batch_banner": "WeChat 批次单图模式必须选择 Banner。",
        "validation.batch_missing": "找不到批次图片：{name}",
        "validation.source_required": "请先选择来源图片。",
        "validation.platform": "请选择 LINE、LINE 动图、WeChat 或 LINE＋WeChat。",
        "validation.grid_positive": "切割设置必须为正整数，且不能为 0。",
        "validation.grid_4x4": "当前版本仅支持 4 × 4 贴图组图。",
        "validation.source_missing": "找不到来源图片，请重新选择。",
        "validation.output_required": "请选择输出根目录。",
        "validation.output_writable": "输出目录无法写入，请选择其他位置。",
        "validation.banner_missing": "找不到 WeChat Banner 图片，请重新选择或清除。",
        "validation.cover_missing": "找不到{label}图片，请重新选择或清除。",
        "validation.tolerance": "纯色背景容差必须介于 0～30。",
        "error.invalid_source": "无法读取来源图片，请确认文件格式是否正确。",
        "error.invalid_grid": "切割设置不正确，请确认行数与列数。",
        "error.output": "输出目录无法写入，请选择其他位置。",
        "error.generic": "处理失败，请查看日志获取详细信息。",
        "error.unexpected_title": "Sticker Toolkit 发生错误",
        "error.unexpected": "程序发生意外错误。详细信息已写入本地日志。\n\n{error}",
        "summary.completed": "处理完成",
        "summary.platforms": "输出平台：{platforms}",
        "summary.stickers": "{platform} 贴图：{count} 张",
        "summary.directory": "{platform} 目录：{path}",
        "summary.warning": "警告：{warning}",
        "summary.not_created": "未创建",
        "progress.prepare": "准备处理",
        "progress.read_batch": "正在读取批次图片",
        "progress.batch_item": "正在处理批次图片 {index} / {total}",
        "progress.read_image": "正在读取图片",
        "progress.remove_background": "正在移除外部连通的纯色背景",
        "progress.split": "正在切割与处理贴图",
        "progress.line_assets": "正在生成 LINE 素材",
        "progress.line_preview": "正在生成 LINE 预览",
        "progress.line_animated_assets": "正在生成 LINE 动图 frames",
        "progress.line_animated_preview": "正在生成 LINE 动图预览",
        "progress.wechat_assets": "正在生成 WeChat 素材",
        "progress.wechat_preview": "正在生成 WeChat 预览",
        "progress.complete": "处理完成",
    }
)

TRANSLATIONS: Mapping[str, Mapping[str, str]] = {"en": _EN, "zh_TW": _ZH_TW, "zh_CN": _ZH_CN}


def language_for_locale(locale_name: str) -> str:
    normalized = locale_name.replace("-", "_").lower()
    if normalized.startswith(("zh_tw", "zh_hk", "zh_mo", "zh_hant")):
        return "zh_TW"
    if normalized.startswith(("zh_cn", "zh_sg", "zh_hans")):
        return "zh_CN"
    return DEFAULT_LANGUAGE


def normalize_language(language: str | None, system_locale: str = "") -> str:
    if language is not None and language in TRANSLATIONS:
        return language
    return language_for_locale(system_locale)


def tr(language: str, key: str, **kwargs: object) -> str:
    template = TRANSLATIONS.get(language, _EN).get(key, _EN.get(key, key))
    try:
        return template.format(**kwargs)
    except (KeyError, ValueError):
        fallback = _EN.get(key, key)
        try:
            return fallback.format(**kwargs)
        except (KeyError, ValueError):
            return fallback


_VISIBLE_ALIASES = {
    "整合圖": "mode.sheet",
    "WeChat 批次單圖": "mode.batch",
    "微信": "platform.wechat",
    "LINE 動圖": "platform.line_animated",
    "微信 Banner": "group.banner",
    "未選擇時沿用既有無 Banner 行為": "placeholder.banner",
    "選擇來源圖片後自動建立輸出位置": "placeholder.output",
    "只移除與畫布外部連通的指定背景色，適合固定純色背景的貼圖合集；不是 AI 去背。": (
        "tooltip.remove_background"
    ),
    "數值越高，越容易移除近似背景色，但也可能誤刪淺色細節。"
    "純色 PNG 建議 3～5；JPEG 或有壓縮色差的圖片可使用 10～15。": "tooltip.tolerance",
    "LINE 封面圖片": "group.line_cover",
    "WeChat 封面圖片": "group.wechat_cover",
}


def translation_key(text: str) -> str | None:
    """Find a stable key for a currently displayed translated string."""
    alias = _VISIBLE_ALIASES.get(text)
    if alias is not None:
        return alias
    for catalog in TRANSLATIONS.values():
        for key, value in catalog.items():
            if value == text and "{" not in value:
                return key
    return None


def translate_visible_text(language: str, text: str) -> str:
    key = translation_key(text)
    return tr(language, key) if key is not None else text


_PROGRESS_KEYS = {
    "準備處理": "progress.prepare",
    "正在讀取批次圖片": "progress.read_batch",
    "正在讀取圖片": "progress.read_image",
    "正在移除外部連通的純色背景": "progress.remove_background",
    "正在切割與處理貼圖": "progress.split",
    "正在產生 LINE 素材": "progress.line_assets",
    "正在產生 LINE 預覽": "progress.line_preview",
    "正在產生 LINE 動圖 frames": "progress.line_animated_assets",
    "正在產生 LINE 動圖預覽": "progress.line_animated_preview",
    "正在產生 WeChat 素材": "progress.wechat_assets",
    "正在產生 WeChat 預覽": "progress.wechat_preview",
    "處理完成": "progress.complete",
}


def translate_progress(language: str, message: str) -> str:
    key = _PROGRESS_KEYS.get(message)
    if key is not None:
        return tr(language, key)
    match = re.fullmatch(r"正在處理批次圖片 (\d+) / (\d+)", message)
    if match:
        return tr(language, "progress.batch_item", index=match.group(1), total=match.group(2))
    return message


def translate_user_message(language: str, message: str) -> str:
    """Translate known service/validation messages without changing core behavior."""
    direct = {
        "請選擇有效的輸入模式。": "validation.input_mode",
        "WeChat 批次單圖模式僅支援微信輸出。": "validation.batch_platform",
        "WeChat 批次單圖模式必須選擇 Banner。": "validation.batch_banner",
        "請先選擇來源圖片。": "validation.source_required",
        "請選擇 LINE、微信或 LINE＋微信。": "validation.platform",
        "請選擇 LINE、LINE 動圖、微信或 LINE＋微信。": "validation.platform",
        "切割設定必須為正整數，且不可為 0。": "validation.grid_positive",
        "目前版本僅支援 4 × 4 貼圖合集。": "validation.grid_4x4",
        "找不到來源圖片，請重新選擇。": "validation.source_missing",
        "請選擇輸出目錄。": "validation.output_required",
        "輸出目錄無法寫入，請選擇其他位置。": "validation.output_writable",
        "找不到微信 Banner 圖片，請重新選擇或清除。": "validation.banner_missing",
        "純色背景容差必須介於 0～30。": "validation.tolerance",
    }
    key = direct.get(message)
    if key is not None:
        return tr(language, key)
    match = re.fullmatch(r"WeChat 批次單圖目前只有 (\d+) 張，尚不足 16 張。", message)
    if match:
        return tr(language, "validation.batch_few", count=match.group(1))
    match = re.fullmatch(r"WeChat 批次單圖目前有 (\d+) 張，請先使用「移除」整理至 16 張。", message)
    if match:
        return tr(language, "validation.batch_many", count=match.group(1))
    match = re.fullmatch(r"找不到批次圖片：(.+)", message)
    if match:
        return tr(language, "validation.batch_missing", name=match.group(1))
    match = re.fullmatch(r"找不到(.+封面)圖片，請重新選擇或清除。", message)
    if match:
        return tr(language, "validation.cover_missing", label=match.group(1))
    return message
