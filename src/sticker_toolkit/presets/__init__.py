"""平台規格 Preset。"""

from .line import LINE_PRESET
from .line_animated import LINE_ANIMATED_PRESET
from .models import PlatformPreset
from .wechat import WECHAT_PRESET

PRESETS = {
    LINE_PRESET.key: LINE_PRESET,
    LINE_ANIMATED_PRESET.key: LINE_ANIMATED_PRESET,
    WECHAT_PRESET.key: WECHAT_PRESET,
}

__all__ = ["LINE_ANIMATED_PRESET", "LINE_PRESET", "PRESETS", "PlatformPreset", "WECHAT_PRESET"]
