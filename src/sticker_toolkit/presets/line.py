"""LINE 平台 Preset。"""

from core.config import LINE_CONFIG

from .models import PlatformPreset

LINE_PRESET = PlatformPreset(
    key="line",
    name=LINE_CONFIG.name,
    sticker_size=LINE_CONFIG.sticker_size,
    sticker_padding=LINE_CONFIG.sticker_padding,
    min_sticker_count=16,
    max_sticker_count=16,
    output_folder_name="line_sticker",
    preview_name=LINE_CONFIG.preview_name,
    zip_name=LINE_CONFIG.zip_name,
    main_size=LINE_CONFIG.main_size,
    tab_size=LINE_CONFIG.tab_size,
)
