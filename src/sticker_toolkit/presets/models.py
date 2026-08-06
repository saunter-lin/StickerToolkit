"""平台規格資料模型。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformPreset:
    key: str
    name: str
    sticker_size: tuple[int, int]
    sticker_padding: int
    min_sticker_count: int
    max_sticker_count: int
    output_folder_name: str
    preview_name: str
    zip_name: str
    main_size: tuple[int, int] | None = None
    tab_size: tuple[int, int] | None = None
