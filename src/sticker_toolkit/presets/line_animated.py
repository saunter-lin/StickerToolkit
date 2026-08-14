"""LINE animation frame preparation Preset (PNG frames only; no APNG encoding)."""

from core.config import LINE_ANIMATED_CONFIG

from .models import PlatformPreset

LINE_ANIMATED_PRESET = PlatformPreset(
    key="line_animated",
    name=LINE_ANIMATED_CONFIG.name,
    sticker_size=LINE_ANIMATED_CONFIG.sticker_size,
    sticker_padding=LINE_ANIMATED_CONFIG.sticker_padding,
    min_sticker_count=16,
    max_sticker_count=16,
    output_folder_name="line_sticker",
    preview_name=LINE_ANIMATED_CONFIG.preview_name,
    zip_name=LINE_ANIMATED_CONFIG.zip_name,
)
