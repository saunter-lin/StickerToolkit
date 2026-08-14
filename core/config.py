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


@dataclass(frozen=True)
class WechatConfig:
    name: str = "WeChat"
    min_sticker_count: int = 8
    max_sticker_count: int = 24
    default_sticker_count: int = 16
    sticker_width: int = 240
    sticker_height: int = 240
    sticker_max_bytes: int = 500 * 1024
    sticker_padding: int = 12
    banner_width: int = 750
    banner_height: int = 400
    banner_max_bytes: int = 500 * 1024
    banner_target_ratio: float = 750 / 400
    banner_ratio_tolerance: float = 0.05
    banner_padding: int = 0
    cover_width: int = 240
    cover_height: int = 240
    cover_max_bytes: int = 500 * 1024
    cover_padding: int = 12
    panel_icon_width: int = 50
    panel_icon_height: int = 50
    panel_icon_max_bytes: int = 100 * 1024
    panel_icon_padding: int = 3
    zip_name: str = "wechat_sticker.zip"
    preview_name: str = "wechat_preview.png"

    @property
    def sticker_size(self) -> tuple[int, int]:
        return self.sticker_width, self.sticker_height

    @property
    def banner_size(self) -> tuple[int, int]:
        return self.banner_width, self.banner_height

    @property
    def cover_size(self) -> tuple[int, int]:
        return self.cover_width, self.cover_height

    @property
    def panel_icon_size(self) -> tuple[int, int]:
        return self.panel_icon_width, self.panel_icon_height


LINE_CONFIG = PlatformConfig(
    name="LINE",
    sticker_size=(370, 320),
    sticker_padding=20,
    zip_name="line_sticker.zip",
    preview_name="preview.png",
    main_size=(240, 240),
    tab_size=(96, 74),
    main_padding=5,
    tab_padding=5,
)

LINE_ANIMATED_CONFIG = PlatformConfig(
    name="LINE Animated",
    sticker_size=(270, 270),
    sticker_padding=12,
    zip_name="line_sticker.zip",
    preview_name="preview.png",
)

WECHAT_CONFIG = WechatConfig()
