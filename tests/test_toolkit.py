from __future__ import annotations

import shutil
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
    exact_banner_size_candidates,
    image_dimensions,
    is_banner_ratio_candidate,
    named_banner_candidates,
    ratio_banner_candidates,
    resolve_source,
)
from core.images import StickerError, build_shared_stickers, contain, load_image
from core.paths import ProjectPaths
from exporters.line import export_line
from exporters.wechat import export_wechat, validate_sticker_count
from sticker_processor import choose_banner
from sticker_toolkit.core import InvalidGridError, InvalidSourceImageError, ProcessingOptions
from sticker_toolkit.presets import LINE_PRESET, WECHAT_PRESET
from sticker_toolkit.services import StickerService
from sticker_toolkit.ui.cli.main import run_process


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
        self.paths = ProjectPaths.from_root(Path(self.temp.name))
        self.output = self.paths.output.root
        self.output.mkdir(parents=True)
        self.stickers = build_shared_stickers(
            sample_sheet(), LINE_CONFIG.sticker_size, LINE_CONFIG.sticker_padding
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_line_export_has_only_one_zip(self) -> None:
        (self.output / "line_sticker_package.zip").write_bytes(b"old")
        (self.output / "line_stickers.zip").write_bytes(b"old")
        zip_path = export_line(self.stickers, self.paths.output, 9, 3)
        self.assertEqual(zip_path.name, "line_sticker.zip")
        self.assertFalse((self.output / "line_sticker_package.zip").exists())
        self.assertFalse((self.output / "line_stickers.zip").exists())
        self.assertEqual(list(self.output.glob("line*.zip")), [zip_path])
        self.assertFalse(any((self.output / f"{index:02d}.png").exists() for index in range(1, 17)))
        self.assertFalse((self.output / "main.png").exists())
        self.assertFalse((self.output / "tab.png").exists())
        self.assertTrue(
            all(
                (self.paths.output.line_directory / f"{index:02d}.png").is_file()
                for index in range(1, 17)
            )
        )
        self.assertTrue((self.paths.output.line_directory / "main.png").is_file())
        self.assertTrue((self.paths.output.line_directory / "tab.png").is_file())
        with zipfile.ZipFile(zip_path) as archive:
            self.assertEqual(len(archive.namelist()), 18)
            self.assertTrue(all(name.startswith("line_sticker/") for name in archive.namelist()))
            self.assertIsNone(archive.testzip())

    def test_wechat_count_validation_accepts_sixteen(self) -> None:
        validate_sticker_count(16)

    def test_wechat_count_validation_rejects_below_eight(self) -> None:
        with self.assertRaisesRegex(StickerError, "8～24"):
            validate_sticker_count(7)

    def test_wechat_count_validation_rejects_above_twenty_four(self) -> None:
        with self.assertRaisesRegex(StickerError, "8～24"):
            validate_sticker_count(25)

    def test_wechat_export_without_banner_is_incomplete(self) -> None:
        result = export_wechat(self.stickers, self.paths.output, None)
        self.assertIsNone(result.banner_path)
        self.assertFalse(result.complete)
        self.assertNotIn("banner.png", result.zip_contents)
        self.assertEqual(len(result.zip_contents), 18)
        with zipfile.ZipFile(result.zip_path) as archive:
            self.assertEqual(len(archive.namelist()), 18)
            self.assertNotIn("wechat/manifest.json", archive.namelist())
            self.assertIsNone(archive.testzip())

    def test_wechat_assets_match_dimensions_formats_and_limits(self) -> None:
        banner_path = self.output / "source_banner.png"
        Image.new("RGB", (1000, 200), "blue").save(banner_path)
        result = export_wechat(self.stickers, self.paths.output, banner_path, cover_index=3)
        self.assertTrue(result.complete)
        self.assertIn("banner.png", result.zip_contents)
        self.assertEqual(len(result.zip_contents), 19)
        for index in range(1, 17):
            sticker = self.output / "wechat_sticker" / f"{index:02d}.png"
            with Image.open(sticker) as image:
                self.assertEqual(
                    (image.format, image.mode, image.size),
                    ("PNG", "RGBA", WECHAT_CONFIG.sticker_size),
                )
            self.assertLessEqual(sticker.stat().st_size, WECHAT_CONFIG.sticker_max_bytes)
        assert result.banner_path is not None
        with Image.open(result.banner_path) as image:
            self.assertEqual((image.format, image.size), ("PNG", WECHAT_CONFIG.banner_size))
        self.assertLessEqual(result.banner_path.stat().st_size, WECHAT_CONFIG.banner_max_bytes)
        with Image.open(result.cover_path) as image:
            self.assertEqual(
                (image.format, image.mode, image.size),
                ("PNG", "RGBA", WECHAT_CONFIG.cover_size),
            )
        self.assertLessEqual(result.cover_path.stat().st_size, WECHAT_CONFIG.cover_max_bytes)
        with Image.open(result.panel_icon_path) as image:
            self.assertEqual(
                (image.format, image.mode, image.size),
                ("PNG", "RGBA", WECHAT_CONFIG.panel_icon_size),
            )
        self.assertLessEqual(result.panel_icon_path.stat().st_size, WECHAT_CONFIG.panel_icon_max_bytes)
        with zipfile.ZipFile(result.zip_path) as archive:
            self.assertEqual(archive.namelist()[0], "01.png")
            self.assertFalse(any("/" in name for name in archive.namelist()))
            self.assertNotIn("manifest.json", archive.namelist())
            self.assertIsNone(archive.testzip())

    def test_wechat_zip_is_not_duplicated(self) -> None:
        old_zip = self.output / "wechat_sticker_package.zip"
        old_zip.write_bytes(b"old")
        result = export_wechat(self.stickers, self.paths.output, None)
        self.assertEqual(result.zip_path.name, "wechat_sticker.zip")
        self.assertFalse(old_zip.exists())
        self.assertEqual(list(self.output.glob("wechat*.zip")), [result.zip_path])

    def test_platform_exports_do_not_delete_each_other(self) -> None:
        wechat = export_wechat(self.stickers, self.paths.output, None)
        wechat_bytes = wechat.zip_path.read_bytes()
        export_line(self.stickers, self.paths.output, 1, 1)
        self.assertTrue(self.paths.output.wechat_directory.is_dir())
        self.assertEqual(wechat.zip_path.read_bytes(), wechat_bytes)

        line_bytes = self.paths.output.line_zip.read_bytes()
        export_wechat(self.stickers, self.paths.output, None)
        self.assertTrue(self.paths.output.line_directory.is_dir())
        self.assertEqual(self.paths.output.line_zip.read_bytes(), line_bytes)

    def test_wechat_config_matches_upload_specification(self) -> None:
        self.assertEqual(
            (
                WECHAT_CONFIG.min_sticker_count,
                WECHAT_CONFIG.max_sticker_count,
                WECHAT_CONFIG.default_sticker_count,
            ),
            (8, 24, 16),
        )
        self.assertEqual(WECHAT_CONFIG.sticker_size, (240, 240))
        self.assertEqual(WECHAT_CONFIG.sticker_max_bytes, 500 * 1024)
        self.assertEqual(WECHAT_CONFIG.banner_size, (750, 400))
        self.assertEqual(WECHAT_CONFIG.banner_max_bytes, 500 * 1024)
        self.assertEqual(WECHAT_CONFIG.banner_target_ratio, 1.875)
        self.assertEqual(WECHAT_CONFIG.banner_ratio_tolerance, 0.05)
        self.assertEqual(WECHAT_CONFIG.cover_size, (240, 240))
        self.assertEqual(WECHAT_CONFIG.cover_max_bytes, 500 * 1024)
        self.assertEqual(WECHAT_CONFIG.panel_icon_size, (50, 50))
        self.assertEqual(WECHAT_CONFIG.panel_icon_max_bytes, 100 * 1024)


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
            Image.new("RGB", (750, 400), "red").save(exact)
            Image.new("RGB", (1967, 1000), "blue").save(near)
            self.assertEqual(exact_banner_size_candidates(folder, source), [exact])
            self.assertEqual(ratio_banner_candidates(folder, source), [near])
            self.assertEqual(banner_candidates(folder, source), [exact])
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


class SharedPipelineTests(unittest.TestCase):
    def test_line_and_wechat_share_one_split_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as folder_name:
            folder = Path(folder_name)
            source = folder / "sheet.png"
            sample_sheet().save(source)
            with patch(
                "sticker_toolkit.services.sticker_service.build_shared_stickers",
                wraps=build_shared_stickers,
            ) as shared_pipeline:
                StickerService().process(
                    source,
                    ProcessingOptions(platform="both", output_directory=folder / "output"),
                )
            shared_pipeline.assert_called_once()
            self.assertTrue((folder / "output" / "preview" / "line" / "preview.png").is_file())
            self.assertTrue(
                (folder / "output" / "preview" / "wechat" / "wechat_preview.png").is_file()
            )
            self.assertFalse((folder / "preview").exists())
            self.assertFalse((folder / "output" / "preview" / "line" / "banner.png").exists())
            self.assertFalse((folder / "output" / "preview" / "wechat" / "main.png").exists())

    def test_platform_preview_cleanup_is_isolated_and_legacy_preview_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as folder_name:
            folder = Path(folder_name)
            source = folder / "sheet.png"
            sample_sheet().save(source)
            paths = ProjectPaths.from_root(folder)
            legacy_preview = folder / "preview"
            legacy_preview.mkdir()
            (legacy_preview / "old.png").write_bytes(b"old")

            service = StickerService()
            options = ProcessingOptions(platform="both", output_directory=paths.output.root)
            service.process(source, options)
            shutil.rmtree(legacy_preview)
            wechat_preview = paths.preview.wechat_directory / WECHAT_CONFIG.preview_name
            wechat_bytes = wechat_preview.read_bytes()
            service.process(
                source, ProcessingOptions(platform="line", output_directory=paths.output.root)
            )
            self.assertEqual(wechat_preview.read_bytes(), wechat_bytes)

            line_preview = paths.preview.line_directory / LINE_CONFIG.preview_name
            line_bytes = line_preview.read_bytes()
            service.process(
                source, ProcessingOptions(platform="wechat", output_directory=paths.output.root)
            )
            self.assertEqual(line_preview.read_bytes(), line_bytes)

            self.assertFalse(legacy_preview.exists())
            self.assertTrue(paths.preview.root.is_relative_to(paths.output.root))
            self.assertTrue(
                all(path.is_relative_to(paths.output.root) for path in paths.output.root.rglob("*"))
            )
            shutil.rmtree(paths.output.root)
            self.assertFalse(paths.output.root.exists())


class ServiceArchitectureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "sheet.png"
        sample_sheet().save(self.source)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_presets_have_distinct_platform_paths_and_previews(self) -> None:
        self.assertEqual(LINE_PRESET.output_folder_name, "line_sticker")
        self.assertEqual(WECHAT_PRESET.output_folder_name, "wechat_sticker")
        self.assertNotEqual(LINE_PRESET.preview_name, WECHAT_PRESET.preview_name)

    def test_service_runs_without_callback_and_creates_missing_output(self) -> None:
        output = self.root / "missing" / "output"
        result = StickerService().process(
            self.source, ProcessingOptions(platform="line", output_directory=output)
        )
        line = result.for_platform("line")
        resolved_output = output.resolve()
        self.assertEqual(line.output_directory, resolved_output / "line_sticker")
        self.assertEqual(
            line.preview_file, resolved_output / "preview" / "line" / "preview.png"
        )
        self.assertTrue(line.zip_file and line.zip_file.is_file())
        self.assertFalse((self.root / "preview").exists())
        self.assertFalse((self.root / "01.png").exists())

    def test_service_reports_monotonic_zero_to_hundred_progress(self) -> None:
        events: list[tuple[int, str]] = []
        StickerService().process(
            self.source,
            ProcessingOptions(platform="both", output_directory=self.root / "output"),
            lambda value, message: events.append((value, message)),
        )
        values = [value for value, _ in events]
        self.assertEqual(values[0], 0)
        self.assertEqual(values[-1], 100)
        self.assertEqual(values, sorted(values))
        self.assertTrue(all(0 <= value <= 100 and message for value, message in events))

    def test_options_callback_receives_selection_preview_after_single_split(self) -> None:
        received: list[Path] = []

        def select(options: ProcessingOptions, previews: tuple[Path, ...]) -> ProcessingOptions:
            received.extend(previews)
            self.assertTrue(all(path.is_file() for path in previews))
            return options

        with patch(
            "sticker_toolkit.services.sticker_service.build_shared_stickers",
            wraps=build_shared_stickers,
        ) as shared_pipeline:
            StickerService().process(
                self.source,
                ProcessingOptions(platform="both", output_directory=self.root / "output"),
                options_callback=select,
            )
        self.assertEqual(len(received), 2)
        shared_pipeline.assert_called_once()

    def test_invalid_source_and_grid_raise_specific_errors(self) -> None:
        with self.assertRaises(InvalidSourceImageError):
            StickerService().process(
                self.root / "missing.png",
                ProcessingOptions(output_directory=self.root / "output"),
            )
        with self.assertRaises(InvalidGridError):
            StickerService().process(
                self.source,
                ProcessingOptions(rows=2, columns=2, output_directory=self.root / "output"),
            )

    def test_preview_and_zip_can_be_disabled_without_root_output(self) -> None:
        output = self.root / "output"
        result = StickerService().process(
            self.source,
            ProcessingOptions(
                platform="line",
                output_directory=output,
                create_preview=False,
                create_zip=False,
            ),
        ).for_platform("line")
        self.assertIsNone(result.preview_file)
        self.assertIsNone(result.zip_file)
        self.assertFalse((output / "preview" / "line").exists())
        self.assertFalse((output / "line_sticker.zip").exists())

    def test_cli_adapter_calls_sticker_service(self) -> None:
        service = StickerService()
        with patch(
            "sticker_toolkit.ui.cli.main.StickerService.process",
            wraps=service.process,
        ) as process_call:
            run_process(
                self.source,
                None,
                "line",
                None,
                1,
                1,
                None,
                False,
                False,
                self.root / "output",
            )
        process_call.assert_called_once()

    def test_core_import_does_not_import_ui(self) -> None:
        import subprocess
        import sys

        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys, sticker_toolkit.core; "
                "assert not any(n.startswith('sticker_toolkit.ui') for n in sys.modules)",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
