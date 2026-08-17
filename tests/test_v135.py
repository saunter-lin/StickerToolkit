from __future__ import annotations

import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image, ImageDraw
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from core.config import LINE_ANIMATED_CONFIG, LINE_CONFIG, WECHAT_CONFIG
from core.paths import ProjectPaths
from exporters.line import export_line, prepare_line_tab_image
from exporters.wechat import export_wechat, prepare_wechat_panel_icon_image
from sticker_toolkit.core import ProcessingOptions, StickerToolkitError
from sticker_toolkit.services import StickerService
from sticker_toolkit.services.output_service import export_cover_result
from sticker_toolkit.ui.desktop.main_window import MainWindow
from sticker_toolkit.ui.desktop.view_model import DesktopFormData, DesktopValidationError, validate_form


def make_sheet(path: Path) -> None:
    image = Image.new("RGBA", (400, 400), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    for index in range(16):
        row, column = divmod(index, 4)
        x, y = column * 100, row * 100
        draw.ellipse((x + 18, y + 14, x + 82, y + 86), fill=(50 + index * 8, 90, 160, 255))
    image.save(path)


class V135ExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "sheet.png"
        make_sheet(self.source)
        self.stickers = [Image.new("RGBA", (370, 320), (20 + i, 80, 160, 255)) for i in range(16)]
        self.paths = ProjectPaths.from_output(self.root / "direct-output")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_line_animated_outputs_270_png_frames_only(self) -> None:
        output = self.root / "animated-output"
        result = (
            StickerService()
            .process(
                self.source,
                ProcessingOptions(platform="line_animated", output_directory=output),
            )
            .for_platform("line_animated")
        )
        self.assertEqual(len(result.sticker_files), 16)
        self.assertIsNone(result.main_file)
        self.assertIsNone(result.tab_file)
        self.assertFalse((result.output_directory / "main.png").exists())
        self.assertFalse((result.output_directory / "tab.png").exists())
        for path in result.sticker_files:
            with Image.open(path) as image:
                self.assertEqual((image.format, image.mode, image.size), ("PNG", "RGBA", (270, 270)))
                self.assertEqual(image.getpixel((0, 0))[3], 0)
        assert result.zip_file is not None
        with zipfile.ZipFile(result.zip_file) as archive:
            self.assertEqual(len(archive.namelist()), 16)
            self.assertNotIn("line_sticker/main.png", archive.namelist())
            self.assertNotIn("line_sticker/tab.png", archive.namelist())

    def test_static_line_and_wechat_dimensions_are_unchanged(self) -> None:
        for platform, expected in (
            ("line", LINE_CONFIG.sticker_size),
            ("wechat", WECHAT_CONFIG.sticker_size),
        ):
            with self.subTest(platform=platform):
                result = (
                    StickerService()
                    .process(
                        self.source,
                        ProcessingOptions(platform=platform, output_directory=self.root / platform),
                    )
                    .for_platform(platform)
                )
                with Image.open(result.sticker_files[0]) as image:
                    self.assertEqual(image.size, expected)

    def test_custom_line_main_is_the_source_for_tab(self) -> None:
        custom = self.root / "custom-main.png"
        Image.new("RGBA", (500, 200), (240, 20, 80, 255)).save(custom)
        export_line(self.stickers, self.paths.output, 1, 1, custom)
        with Image.open(self.paths.output.line_directory / "tab.png") as tab:
            self.assertEqual(tab.size, LINE_CONFIG.tab_size)
            self.assertEqual(tab.getpixel((tab.width // 2, tab.height // 2))[:3], (240, 20, 80))

    def test_custom_wechat_cover_is_the_source_for_panel_icon(self) -> None:
        custom = self.root / "custom-cover.png"
        Image.new("RGBA", (500, 200), (240, 20, 80, 255)).save(custom)
        result = export_wechat(self.stickers, self.paths.output, None, 1, custom)
        with Image.open(result.panel_icon_path) as icon:
            self.assertEqual(icon.size, WECHAT_CONFIG.panel_icon_size)
            self.assertEqual(icon.getpixel((icon.width // 2, icon.height // 2))[:3], (240, 20, 80))

    def test_sheet_wechat_auto_banner_and_custom_banner(self) -> None:
        automatic = (
            StickerService()
            .process(
                self.source,
                ProcessingOptions(platform="wechat", output_directory=self.root / "auto"),
            )
            .for_platform("wechat")
        )
        assert automatic.banner_file is not None
        with Image.open(automatic.banner_file) as banner:
            self.assertEqual(banner.size, WECHAT_CONFIG.banner_size)

        custom = self.root / "custom-banner.png"
        Image.new("RGB", WECHAT_CONFIG.banner_size, (10, 40, 220)).save(custom)
        selected = (
            StickerService()
            .process(
                self.source,
                ProcessingOptions(
                    platform="wechat",
                    output_directory=self.root / "custom",
                    banner_path=custom,
                ),
            )
            .for_platform("wechat")
        )
        assert selected.banner_file is not None
        with Image.open(selected.banner_file) as banner:
            self.assertEqual(banner.getpixel((375, 200))[:3], (10, 40, 220))

    def test_main_cover_mode_exports_four_derived_assets_from_png(self) -> None:
        source = self.root / "single.png"
        image = Image.new("RGBA", (420, 180), (0, 0, 0, 0))
        ImageDraw.Draw(image).rectangle((80, 20, 340, 160), fill=(210, 35, 90, 220))
        image.save(source)
        result = (
            StickerService()
            .process(
                source,
                ProcessingOptions(
                    platform="main_cover",
                    input_mode="main_cover",
                    output_directory=self.root / "covers",
                ),
            )
            .for_platform("main_cover")
        )
        expected = {
            "main.png": LINE_CONFIG.main_size,
            "tab.png": LINE_CONFIG.tab_size,
            "cover.png": WECHAT_CONFIG.cover_size,
            "panel_icon.png": WECHAT_CONFIG.panel_icon_size,
        }
        self.assertEqual({path.name for path in result.output_directory.iterdir()}, set(expected))
        self.assertEqual(result.sticker_files, ())
        for name, size in expected.items():
            with Image.open(result.output_directory / name) as exported:
                self.assertEqual((exported.format, exported.mode, exported.size), ("PNG", "RGBA", size))
        assert result.main_file is not None and result.tab_file is not None
        assert result.cover_file is not None and result.panel_icon_file is not None
        with Image.open(result.main_file) as main, Image.open(result.tab_file) as tab:
            expected_tab = prepare_line_tab_image(main.convert("RGBA"))
            self.assertEqual(tab.tobytes(), expected_tab.tobytes())
        with Image.open(result.cover_file) as cover, Image.open(result.panel_icon_file) as panel:
            expected_panel = prepare_wechat_panel_icon_image(cover.convert("RGBA"))
            self.assertEqual(panel.tobytes(), expected_panel.tobytes())

    def test_main_cover_mode_accepts_jpeg(self) -> None:
        source = self.root / "single.jpg"
        Image.new("RGB", (320, 240), (20, 120, 200)).save(source)
        result = StickerService().process(
            source,
            ProcessingOptions(
                platform="main_cover",
                input_mode="main_cover",
                output_directory=self.root / "jpeg-covers",
            ),
        )
        self.assertEqual(len(tuple(result.for_platform("main_cover").output_directory.glob("*.png"))), 4)

    def test_main_cover_mode_rejects_damaged_image_safely(self) -> None:
        source = self.root / "damaged.png"
        source.write_bytes(b"not an image")
        with self.assertRaises(StickerToolkitError):
            StickerService().process(
                source,
                ProcessingOptions(
                    platform="main_cover",
                    input_mode="main_cover",
                    output_directory=self.root / "damaged-output",
                ),
            )

    def test_sheet_does_not_dispatch_or_create_standalone_cover_output(self) -> None:
        output = self.root / "sheet-only-output"
        with patch(
            "sticker_toolkit.services.sticker_service.export_cover_result",
            wraps=export_cover_result,
        ) as standalone_export:
            result = StickerService().process(
                self.source,
                ProcessingOptions(platform="both", input_mode="sheet", output_directory=output),
            )
        standalone_export.assert_not_called()
        self.assertFalse((output / "cover_output").exists())
        line_main = result.for_platform("line").main_file
        wechat_cover = result.for_platform("wechat").cover_file
        assert line_main is not None and wechat_cover is not None
        self.assertTrue(line_main.is_file())
        self.assertTrue(wechat_cover.is_file())

    def test_main_cover_dispatches_standalone_generator_only(self) -> None:
        source = self.root / "standalone.png"
        Image.new("RGBA", (300, 180), (25, 90, 210, 255)).save(source)
        output_root = self.root / "standalone-root"
        with patch(
            "sticker_toolkit.services.sticker_service.export_cover_result",
            wraps=export_cover_result,
        ) as standalone_export:
            result = StickerService().process(
                source,
                ProcessingOptions(
                    platform="main_cover",
                    input_mode="main_cover",
                    output_directory=output_root,
                ),
            )
        standalone_export.assert_called_once()
        exported = result.for_platform("main_cover")
        self.assertEqual(exported.output_directory, output_root.resolve() / "cover_output")
        self.assertEqual(exported.sticker_files, ())
        self.assertFalse((output_root / "output").exists())


class V135DesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        for settings in (
            QSettings("StickerToolkit", "StickerToolkit"),
            QSettings(
                QSettings.Format.IniFormat,
                QSettings.Scope.UserScope,
                "StickerToolkit",
                "StickerToolkit",
            ),
        ):
            settings.clear()
            settings.setValue("language", "zh_TW")
            settings.sync()
        self.window = MainWindow()

    def tearDown(self) -> None:
        self.window.close()

    def test_line_animated_selector_and_platform_ui_state(self) -> None:
        index = self.window.input_mode_combo.findData("line_animated")
        self.assertGreaterEqual(index, 0)
        self.window.input_mode_combo.setCurrentIndex(index)
        self.assertEqual(self.window.input_mode_combo.currentText(), "LINE 動圖")
        self.assertFalse(self.window.line_cover_group.isEnabled())
        self.assertFalse(self.window.wechat_cover_group.isEnabled())
        self.assertFalse(self.window.banner_group.isEnabled())

        self.window.language_combo.setCurrentIndex(self.window.language_combo.findData("zh_CN"))
        self.assertEqual(self.window.input_mode_combo.currentText(), "LINE 动图")
        self.window.language_combo.setCurrentIndex(self.window.language_combo.findData("en"))
        self.assertEqual(self.window.input_mode_combo.currentText(), "LINE Animated")

    def test_four_input_modes_and_main_cover_ui(self) -> None:
        self.assertEqual(
            [self.window.input_mode_combo.itemData(index) for index in range(4)],
            ["sheet", "wechat_batch", "line_animated", "main_cover"],
        )
        self.window.input_mode_combo.setCurrentIndex(
            self.window.input_mode_combo.findData("main_cover")
        )
        self.assertFalse(self.window.source_group.isHidden())
        self.assertFalse(self.window.output_group.isHidden())
        self.assertFalse(self.window.platform_group.isVisible())
        self.assertFalse(self.window.grid_group.isVisible())
        self.assertFalse(self.window.banner_group.isVisible())
        self.assertFalse(self.window.options_group.isVisible())
        self.assertFalse(self.window.background_group.isVisible())
        self.assertEqual(self.window.start_button.text(), "產生 Main / Cover")

    def test_main_cover_requires_source(self) -> None:
        with self.assertRaises(DesktopValidationError):
            validate_form(
                DesktopFormData(
                    source_path="",
                    platform="main_cover",
                    rows=4,
                    columns=4,
                    banner_path="",
                    output_directory=tempfile.gettempdir(),
                    input_mode="main_cover",
                )
            )

    def test_main_cover_request_keeps_cover_output_outside_standard_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "single-cover.png"
            output_root = root / "single-cover-root"
            Image.new("RGBA", (100, 100), (20, 80, 160, 255)).save(source)
            self.window.input_mode_combo.setCurrentIndex(
                self.window.input_mode_combo.findData("main_cover")
            )
            self.window.source_edit.setText(str(source))
            self.window.output_edit.setText(str(output_root))
            _, options = self.window.controller.build_request(self.window._form_data())
            self.assertEqual(options.output_directory, output_root.resolve())

    def test_legacy_line_animated_setting_migrates_to_input_mode(self) -> None:
        self.window.close()
        for settings in (
            QSettings("StickerToolkit", "StickerToolkit"),
            QSettings(
                QSettings.Format.IniFormat,
                QSettings.Scope.UserScope,
                "StickerToolkit",
                "StickerToolkit",
            ),
        ):
            settings.setValue("input_mode", "sheet")
            settings.setValue("platform", "line_animated")
            settings.sync()
        self.window = MainWindow()
        self.assertEqual(self.window.input_mode_combo.currentData(), "line_animated")

    def test_sheet_output_path_refresh_and_manual_override(self) -> None:
        temporary_root = Path(tempfile.gettempdir())
        first = temporary_root / "source-a.png"
        second = temporary_root / "source-b.png"
        self.window._apply_source_path(first)
        self.assertEqual(Path(self.window.output_edit.text()), temporary_root / "source-a_output")
        self.window._apply_source_path(second)
        self.assertEqual(Path(self.window.output_edit.text()), temporary_root / "source-b_output")
        self.window._output_user_selected = True
        custom_output = temporary_root / "custom-output"
        self.window.output_edit.setText(str(custom_output))
        self.window._apply_source_path(first)
        self.assertEqual(Path(self.window.output_edit.text()), custom_output)


class V135ConfigTests(unittest.TestCase):
    def test_line_animated_config_is_isolated(self) -> None:
        self.assertEqual(LINE_ANIMATED_CONFIG.sticker_size, (270, 270))
        self.assertEqual(LINE_CONFIG.sticker_size, (370, 320))
