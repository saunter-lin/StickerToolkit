from __future__ import annotations

import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


class PackagingIconTests(unittest.TestCase):
    def test_packaging_icon_is_rgba_with_transparent_corners(self) -> None:
        with Image.open(ROOT / "assets" / "app_icon_packaging.png") as icon:
            self.assertEqual(icon.format, "PNG")
            self.assertEqual(icon.mode, "RGBA")
            self.assertEqual(icon.size, (1024, 1024))
            corners = ((0, 0), (1023, 0), (0, 1023), (1023, 1023))
            self.assertTrue(all(icon.getpixel(point)[3] == 0 for point in corners))

    def test_platform_icons_contain_expected_sizes(self) -> None:
        with Image.open(ROOT / "assets" / "icons" / "StickerToolkit.icns") as icon:
            sizes = {size[:2] for size in icon.info["sizes"]}
            self.assertTrue({(16, 16), (32, 32), (128, 128), (256, 256), (512, 512)} <= sizes)
        with Image.open(ROOT / "assets" / "icons" / "StickerToolkit.ico") as icon:
            self.assertEqual(
                icon.info["sizes"],
                {(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)},
            )
