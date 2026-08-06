"""平台規格 Preset。"""

from .line import LINE_PRESET
from .models import PlatformPreset
from .wechat import WECHAT_PRESET

PRESETS = {LINE_PRESET.key: LINE_PRESET, WECHAT_PRESET.key: WECHAT_PRESET}

__all__ = ["LINE_PRESET", "PRESETS", "PlatformPreset", "WECHAT_PRESET"]
