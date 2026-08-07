from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from sticker_toolkit.core import (
    ProcessingOptions,
    color_to_hex,
    detect_solid_background_color,
    remove_connected_solid_background,
)
from sticker_toolkit.services import StickerService

BACKGROUND = (255, 248, 236)


def solid_sheet() -> Image.Image:
    image = Image.new("RGBA", (160, 160), (*BACKGROUND, 255))
    draw = ImageDraw.Draw(image)
    for index in range(16):
        row, column = divmod(index, 4)
        left, top = column * 40, row * 40
        draw.ellipse((left + 8, top + 6, left + 32, top + 34), fill=(40, 90, 160, 255))
    return image


class SolidBackgroundDetectionTests(unittest.TestCase):
    def test_detects_exact_solid_background(self) -> None:
        self.assertEqual(detect_solid_background_color(solid_sheet()), BACKGROUND)
        self.assertEqual(color_to_hex(BACKGROUND), "#FFF8EC")

    def test_near_corner_colors_use_a_reasonable_median(self) -> None:
        image = Image.new("RGB", (40, 40), BACKGROUND)
        pixels = image.load()
        assert pixels is not None
        pixels[0, 0] = (254, 248, 236)
        pixels[39, 0] = (255, 247, 236)
        pixels[0, 39] = (255, 248, 235)
        pixels[39, 39] = (255, 249, 236)
        detected = detect_solid_background_color(image)
        self.assertIsNotNone(detected)
        assert detected is not None
        self.assertTrue(all(abs(a - b) <= 1 for a, b in zip(detected, BACKGROUND, strict=True)))

    def test_inconsistent_corners_are_not_auto_detected(self) -> None:
        image = Image.new("RGB", (20, 20), BACKGROUND)
        image.putpixel((1, 1), (10, 20, 30))
        self.assertIsNone(detect_solid_background_color(image))


class ConnectedBackgroundRemovalTests(unittest.TestCase):
    def test_exact_background_becomes_transparent_rgba(self) -> None:
        result = remove_connected_solid_background(
            Image.new("RGB", (8, 8), BACKGROUND), BACKGROUND, 3
        )
        self.assertEqual(result.mode, "RGBA")
        self.assertIsNone(result.getchannel("A").getbbox())

    def test_tolerance_three_removes_small_difference(self) -> None:
        image = Image.new("RGB", (5, 5), BACKGROUND)
        image.putpixel((0, 2), (252, 250, 237))
        result = remove_connected_solid_background(image, BACKGROUND, 3)
        self.assertEqual(result.getpixel((0, 2))[3], 0)

    def test_pixel_outside_tolerance_is_preserved(self) -> None:
        image = Image.new("RGB", (5, 5), BACKGROUND)
        image.putpixel((0, 2), (251, 248, 236))
        result = remove_connected_solid_background(image, BACKGROUND, 3)
        self.assertEqual(result.getpixel((0, 2))[3], 255)

    def test_only_boundary_connected_region_is_removed(self) -> None:
        image = Image.new("RGB", (9, 9), BACKGROUND)
        draw = ImageDraw.Draw(image)
        draw.rectangle((2, 2, 6, 6), fill="black")
        draw.rectangle((3, 3, 5, 5), fill=BACKGROUND)
        result = remove_connected_solid_background(image, BACKGROUND, 3)
        self.assertEqual(result.getpixel((0, 0))[3], 0)
        self.assertEqual(result.getpixel((4, 4)), (*BACKGROUND, 255))

    def test_white_outline_and_white_fur_are_preserved(self) -> None:
        image = Image.new("RGB", (15, 15), BACKGROUND)
        draw = ImageDraw.Draw(image)
        draw.ellipse((3, 3, 11, 11), fill="white")
        draw.ellipse((5, 5, 9, 9), fill=(60, 60, 60))
        result = remove_connected_solid_background(image, BACKGROUND, 3)
        self.assertEqual(result.getpixel((7, 3)), (255, 255, 255, 255))
        self.assertEqual(result.getpixel((4, 7)), (255, 255, 255, 255))

    def test_existing_alpha_is_not_increased_or_replaced(self) -> None:
        image = Image.new("RGBA", (6, 6), (*BACKGROUND, 255))
        image.putpixel((3, 3), (20, 30, 40, 91))
        image.putpixel((2, 3), (0, 0, 0, 0))
        result = remove_connected_solid_background(image, BACKGROUND, 3)
        self.assertEqual(result.getpixel((3, 3)), (20, 30, 40, 91))
        self.assertEqual(result.getpixel((2, 3))[3], 0)


class SolidBackgroundPipelineTests(unittest.TestCase):
    def test_options_are_disabled_by_default(self) -> None:
        options = ProcessingOptions()
        self.assertFalse(options.remove_solid_background)
        self.assertTrue(options.auto_detect_solid_background)
        self.assertEqual(options.solid_background_color, "#FFF8EC")
        self.assertEqual(options.solid_background_tolerance, 3)

    def test_disabled_feature_matches_existing_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as folder_name:
            root = Path(folder_name)
            source = root / "sheet.png"
            solid_sheet().save(source)
            first = StickerService().process(
                source,
                ProcessingOptions(
                    platform="line",
                    output_directory=root / "first",
                    create_preview=False,
                    create_zip=False,
                ),
            )
            second = StickerService().process(
                source,
                ProcessingOptions(
                    platform="line",
                    output_directory=root / "second",
                    create_preview=False,
                    create_zip=False,
                    remove_solid_background=False,
                ),
            )
            first_files = first.for_platform("line").sticker_files
            second_files = second.for_platform("line").sticker_files
            self.assertEqual(
                [path.read_bytes() for path in first_files],
                [path.read_bytes() for path in second_files],
            )

    def test_auto_detection_removes_cream_background_behind_a_white_outer_border(self) -> None:
        with tempfile.TemporaryDirectory() as folder_name:
            root = Path(folder_name)
            source = root / "bordered_sheet.png"
            sheet = solid_sheet()
            bordered = Image.new("RGB", (162, 162), "white")
            bordered.paste(sheet.convert("RGB"), (1, 1))
            bordered.save(source)
            result = StickerService().process(
                source,
                ProcessingOptions(
                    platform="line",
                    output_directory=root / "output",
                    create_preview=False,
                    create_zip=False,
                    remove_solid_background=True,
                ),
            )
            sticker = Image.open(result.for_platform("line").sticker_files[0]).convert("RGBA")
            self.assertEqual(sticker.getpixel((0, 0))[3], 0)
            self.assertFalse(
                any(
                    alpha > 0 and (red, green, blue) == BACKGROUND
                    for red, green, blue, alpha in sticker.get_flattened_data()
                )
            )

    def test_enabled_feature_exports_both_platforms_and_previews_with_unicode_path(self) -> None:
        with tempfile.TemporaryDirectory() as folder_name:
            root = Path(folder_name) / "中文 貼圖"
            root.mkdir()
            source = root / "合集 圖.png"
            solid_sheet().save(source)
            output = root / "輸出 結果"
            result = StickerService().process(
                source,
                ProcessingOptions(
                    platform="both",
                    output_directory=output,
                    remove_solid_background=True,
                ),
            )
            self.assertEqual(len(result.for_platform("line").sticker_files), 16)
            self.assertEqual(len(result.for_platform("wechat").sticker_files), 16)
            self.assertTrue((output / "line_sticker.zip").is_file())
            self.assertTrue((output / "wechat_sticker.zip").is_file())
            self.assertTrue((output / "preview" / "line" / "preview.png").is_file())
            self.assertTrue(
                (output / "preview" / "wechat" / "wechat_preview.png").is_file()
            )
            line_image = Image.open(result.for_platform("line").sticker_files[0])
            self.assertEqual(line_image.mode, "RGBA")
            self.assertEqual(line_image.getpixel((0, 0))[3], 0)


if __name__ == "__main__":
    unittest.main()
