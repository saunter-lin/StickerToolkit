"""WeChat 平台 Preset。"""

from core.config import WECHAT_CONFIG

from .models import PlatformPreset

WECHAT_PRESET = PlatformPreset(
    key="wechat",
    name=WECHAT_CONFIG.name,
    sticker_size=WECHAT_CONFIG.sticker_size,
    sticker_padding=WECHAT_CONFIG.sticker_padding,
    min_sticker_count=WECHAT_CONFIG.min_sticker_count,
    max_sticker_count=WECHAT_CONFIG.max_sticker_count,
    output_folder_name="wechat_sticker",
    preview_name="wechat_preview.png",
    zip_name=WECHAT_CONFIG.zip_name,
)
