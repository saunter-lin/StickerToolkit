from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

from core.config import LINE_CONFIG, WECHAT_CONFIG
from core.discovery import (
    BANNER_RATIO_TOLERANCE,
    banner_candidates,
    choose_candidate,
    image_dimensions,
    is_banner_ratio_candidate,
    named_banner_candidates,
    ratio_banner_candidates,
    resolve_source,
)
from core.images import StickerError, build_shared_stickers, contain, load_image
from exporters.line import export_line
from exporters.wechat import export_wechat
from sticker_processor import choose_banner


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

    def test_line_export_has_only_one_zip(self) -> None:
        (self.output / "line_sticker_package.zip").write_bytes(b"old")
        (self.output / "line_stickers.zip").write_bytes(b"old")
        zip_path = export_line(self.stickers, self.output, 9, 3)
        self.assertEqual(zip_path.name, "line_sticker.zip")
        self.assertFalse((self.output / "line_sticker_package.zip").exists())
        self.assertFalse((self.output / "line_stickers.zip").exists())
        self.assertEqual(list(self.output.glob("line*.zip")), [zip_path])
        with zipfile.ZipFile(zip_path) as archive:
            self.assertEqual(len(archive.namelist()), 18)
            self.assertIsNone(archive.testzip())

    def test_wechat_export_without_banner(self) -> None:
        zip_path, names, banner = export_wechat(self.stickers, self.output, None)
        self.assertIsNone(banner)
        self.assertNotIn("wechat/banner/banner.png", names)
        self.assertEqual(len(names), 16)
        with zipfile.ZipFile(zip_path) as archive:
            self.assertEqual(len(archive.namelist()), 16)
            self.assertNotIn("wechat/manifest.json", archive.namelist())
            self.assertIsNone(archive.testzip())

    def test_wechat_export_with_contained_banner(self) -> None:
        banner_path = self.output / "source_banner.png"
        Image.new("RGB", (1000, 200), "blue").save(banner_path)
        zip_path, names, banner = export_wechat(self.stickers, self.output, banner_path)
        self.assertIn("wechat/banner/banner.png", names)
        self.assertEqual(len(names), 17)
        self.assertIsNotNone(banner)
        assert banner is not None
        with Image.open(banner) as image:
            self.assertEqual(image.size, WECHAT_CONFIG.banner_size)
            self.assertEqual(image.mode, "RGBA")
        with zipfile.ZipFile(zip_path) as archive:
            self.assertIsNone(archive.testzip())


class DiscoveryTests(unittest.TestCase):
    def test_wechat_banner_name_is_detected_at_any_ratio(self) -> None:
        with tempfile.TemporaryDirectory() as folder_name:
            folder = Path(folder_name)
            Image.new("RGB", (800, 800), "white").save(folder / "Berry.png")
            named = folder / "wechat_banner.png"
            Image.new("RGB", (200, 900), "white").save(named)
            self.assertEqual(named_banner_candidates(folder, folder / "Berry.png"), [named])
            self.assertEqual(banner_candidates(folder, folder / "Berry.png"), [named])

    def test_banner_name_and_case_insensitive_webp_are_detected(self) -> None:
        with tempfile.TemporaryDirectory() as folder_name:
            folder = Path(folder_name)
            source = folder / "sheet.png"
            Image.new("RGB", (800, 800), "white").save(source)
            lower = folder / "banner.jpg"
            upper_png = folder / "BANNER.PNG"
            upper = folder / "BANNER.webp"
            Image.new("RGB", (300, 700), "red").save(lower)
            Image.new("RGB", (310, 700), "green").save(upper_png, format="PNG")
            Image.new("RGB", (320, 700), "blue").save(upper, format="WEBP")
            self.assertEqual(set(named_banner_candidates(folder, source)), {lower, upper_png, upper})

    def test_banner_png_name_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as folder_name:
            folder = Path(folder_name)
            source = folder / "sheet.png"
            banner = folder / "banner.png"
            Image.new("RGB", (800, 800), "white").save(source)
            Image.new("RGB", (100, 500), "black").save(banner)
            self.assertEqual(banner_candidates(folder, source), [banner])

    def test_arbitrary_name_with_target_or_near_ratio_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as folder_name:
            folder = Path(folder_name)
            source = folder / "sheet.png"
            exact = folder / "my_image.png"
            near = folder / "wechat01.png"
            Image.new("RGB", (800, 800), "white").save(source)
            Image.new("RGB", (1500, 800), "red").save(exact)
            Image.new("RGB", (1967, 1000), "blue").save(near)
            candidates = ratio_banner_candidates(folder, source)
            self.assertEqual(set(candidates), {exact, near})
            self.assertEqual(BANNER_RATIO_TOLERANCE, 0.05)

    def test_ratio_over_tolerance_is_not_detected(self) -> None:
        with tempfile.TemporaryDirectory() as folder_name:
            path = Path(folder_name) / "wide.png"
            Image.new("RGB", (2000, 1000), "white").save(path)
            self.assertFalse(is_banner_ratio_candidate(path))

    def test_sticker_sheet_is_excluded_from_banner(self) -> None:
        with tempfile.TemporaryDirectory() as folder_name:
            folder = Path(folder_name)
            source = folder / "sheet.png"
            Image.new("RGB", (1500, 800), "white").save(source)
            self.assertNotIn(source, banner_candidates(folder, source))

    def test_multiple_banners_can_be_selected(self) -> None:
        with tempfile.TemporaryDirectory() as folder_name:
            folder = Path(folder_name)
            first = folder / "cover.png"
            second = folder / "wechat01.png"
            Image.new("RGB", (750, 400), "white").save(first)
            Image.new("RGB", (900, 500), "white").save(second)
            with patch("builtins.input", return_value="2"):
                self.assertEqual(choose_candidate([first, second], True, "Banner"), second)

    def test_manual_banner_path_and_enter_to_skip(self) -> None:
        with tempfile.TemporaryDirectory() as folder_name:
            manual = Path(folder_name) / "manual-any-ratio.jpg"
            Image.new("RGB", (100, 900), "white").save(manual)
            self.assertEqual(choose_banner(manual, None, False, True), manual.resolve())
            with patch("builtins.input", side_effect=["/missing/banner.png", str(manual)]):
                self.assertEqual(choose_banner(None, None, True, True), manual.resolve())
            with patch("builtins.input", return_value=""):
                self.assertIsNone(choose_banner(None, None, True, True))

    def test_manual_override_skips_automatic_banner_selection(self) -> None:
        with tempfile.TemporaryDirectory() as folder_name:
            folder = Path(folder_name)
            sheet = folder / "sheet.png"
            Image.new("RGB", (800, 800), "white").save(sheet)
            Image.new("RGB", (750, 400), "red").save(folder / "banner.png")
            source, detected = resolve_source(folder, folder, True, detect_banner=False)
            self.assertEqual(source, sheet.resolve())
            self.assertIsNone(detected)

    def test_exif_orientation_is_used_for_ratio(self) -> None:
        with tempfile.TemporaryDirectory() as folder_name:
            path = Path(folder_name) / "rotated.jpg"
            exif = Image.Exif()
            exif[274] = 6
            Image.new("RGB", (400, 750), "white").save(path, exif=exif)
            self.assertEqual(image_dimensions(path), (750, 400))
            self.assertTrue(is_banner_ratio_candidate(path))


if __name__ == "__main__":
    unittest.main()
