"""集中管理平台尺寸與輸出設定。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformConfig:
    name: str
    sticker_size: tuple[int, int]
    sticker_padding: int
    zip_name: str
    preview_name: str
    main_size: tuple[int, int] | None = None
    tab_size: tuple[int, int] | None = None
    main_padding: int = 0
    tab_padding: int = 0
    banner_size: tuple[int, int] | None = None
    banner_padding: int = 0


LINE_CONFIG = PlatformConfig(
    name="LINE",
    sticker_size=(370, 320),
    sticker_padding=20,
    zip_name="line_sticker_package.zip",
    preview_name="preview.png",
    main_size=(240, 240),
    tab_size=(96, 74),
    main_padding=5,
    tab_padding=5,
)

# TODO: 發布前依目標微信貼圖平台的最新官方文件確認 Banner 尺寸。
# 目前採用可調整的 750×400 contain 畫布，不宣稱為微信官方規格。
WECHAT_CONFIG = PlatformConfig(
    name="WeChat",
    sticker_size=LINE_CONFIG.sticker_size,
    sticker_padding=LINE_CONFIG.sticker_padding,
    zip_name="wechat_sticker_package.zip",
    preview_name="wechat_preview.png",
    banner_size=(750, 400),
    banner_padding=16,
)

