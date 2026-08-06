from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

from core.config import LINE_CONFIG, WECHAT_CONFIG
from core.discovery import find_banner, sheet_candidates
from core.images import StickerError, build_shared_stickers, contain, load_image
from exporters.line import export_line
from exporters.wechat import export_wechat


def sample_sheet() -> Image.Image:
    sheet = Image.new("RGBA", (800, 800), "white")
    draw = ImageDraw.Draw(sheet)
    for index in range(16):
        row, column = divmod(index, 4)
        x, y = column * 200, row * 200
        draw.ellipse((x + 30, y + 20, x + 170, y + 160), fill=(30 + index * 10, 80, 150, 255))
        draw.rectangle((x + 65, y + 150, x + 135, y + 180), fill=(10, 10, 10, 255))
    return sheet


class PipelineTests(unittest.TestCase):
    def test_shared_pipeline_returns_sixteen_rgba_stickers(self) -> None:
        stickers = build_shared_stickers(
            sample_sheet(), LINE_CONFIG.sticker_size, LINE_CONFIG.sticker_padding
        )
        self.assertEqual(len(stickers), 16)
        self.assertTrue(all(image.mode == "RGBA" for image in stickers))
        self.assertTrue(all(image.size == LINE_CONFIG.sticker_size for image in stickers))

    def test_fully_transparent_cell_has_chinese_error(self) -> None:
        with self.assertRaisesRegex(StickerError, "完全透明"):
            build_shared_stickers(
                Image.new("RGBA", (400, 400), (0, 0, 0, 0)),
                LINE_CONFIG.sticker_size,
                LINE_CONFIG.sticker_padding,
            )

    def test_contain_never_stretches(self) -> None:
        source = Image.new("RGBA", (200, 100), (0, 0, 0, 255))
        result = contain(source, (100, 100), 10)
        self.assertEqual(result.getchannel("A").getbbox(), (10, 30, 90, 70))

    def test_decode_failure_has_chinese_error(self) -> None:
        with tempfile.TemporaryDirectory() as folder_name:
            broken = Path(folder_name) / "broken.png"
            broken.write_bytes(b"not a png")
            with self.assertRaisesRegex(StickerError, "不是有效"):
                load_image(broken)


class ExporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.output = Path(self.temp.name)
        self.stickers = build_shared_stickers(
            sample_sheet(), LINE_CONFIG.sticker_size, LINE_CONFIG.sticker_padding
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_line_export_and_legacy_zip(self) -> None:
        zip_path = export_line(self.stickers, self.output, 9, 3)
        self.assertEqual(zip_path.name, "line_sticker_package.zip")
        self.assertTrue((self.output / "line_stickers.zip").is_file())
        with zipfile.ZipFile(zip_path) as archive:
            self.assertEqual(len(archive.namelist()), 18)
            self.assertIsNone(archive.testzip())

    def test_wechat_export_without_banner(self) -> None:
        zip_path, names, banner = export_wechat(self.stickers, self.output, None)
        self.assertIsNone(banner)
        self.assertNotIn("wechat/banner/wechat_banner.png", names)
        self.assertEqual(len(names), 17)
        with zipfile.ZipFile(zip_path) as archive:
            manifest = json.loads(archive.read("wechat/manifest.json"))
            self.assertIsNone(manifest["banner"])
            self.assertEqual(manifest["sticker_count"], 16)

    def test_wechat_export_with_contained_banner(self) -> None:
        banner_path = self.output / "source_banner.png"
        Image.new("RGB", (1000, 200), "blue").save(banner_path)
        zip_path, names, banner = export_wechat(self.stickers, self.output, banner_path)
        self.assertIn("wechat/banner/wechat_banner.png", names)
        self.assertIsNotNone(banner)
        assert banner is not None
        with Image.open(banner) as image:
            self.assertEqual(image.size, WECHAT_CONFIG.banner_size)
            self.assertEqual(image.mode, "RGBA")
        with zipfile.ZipFile(zip_path) as archive:
            self.assertIsNone(archive.testzip())


class DiscoveryTests(unittest.TestCase):
    def test_banner_excluded_from_sheet_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as folder_name:
            folder = Path(folder_name)
            Image.new("RGB", (10, 10), "white").save(folder / "Berry.png")
            Image.new("RGB", (10, 10), "white").save(folder / "wechat_banner.png")
            self.assertEqual([path.name for path in sheet_candidates(folder)], ["Berry.png"])
            self.assertEqual(find_banner(folder), folder / "wechat_banner.png")


if __name__ == "__main__":
    unittest.main()
