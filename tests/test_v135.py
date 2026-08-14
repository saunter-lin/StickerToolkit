from __future__ import annotations

import os
import tempfile
import unittest
import zipfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image, ImageDraw
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from core.config import LINE_ANIMATED_CONFIG, LINE_CONFIG, WECHAT_CONFIG
from core.paths import ProjectPaths
from exporters.line import export_line
from exporters.wechat import export_wechat
from sticker_toolkit.core import ProcessingOptions
from sticker_toolkit.services import StickerService
from sticker_toolkit.ui.desktop.main_window import MainWindow


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
        index = self.window.platform_combo.findData("line_animated")
        self.assertGreaterEqual(index, 0)
        self.window.platform_combo.setCurrentIndex(index)
        self.assertEqual(self.window.platform_combo.currentText(), "LINE 動圖")
        self.assertFalse(self.window.line_cover_group.isEnabled())
        self.assertFalse(self.window.wechat_cover_group.isEnabled())
        self.assertFalse(self.window.banner_group.isEnabled())

        self.window.language_combo.setCurrentIndex(self.window.language_combo.findData("zh_CN"))
        self.assertEqual(self.window.platform_combo.currentText(), "LINE 动图")
        self.window.language_combo.setCurrentIndex(self.window.language_combo.findData("en"))
        self.assertEqual(self.window.platform_combo.currentText(), "LINE Animated")

    def test_sheet_output_path_refresh_and_manual_override(self) -> None:
        first = Path("/tmp/source-a.png")
        second = Path("/tmp/source-b.png")
        self.window._apply_source_path(first)
        self.assertEqual(self.window.output_edit.text(), "/tmp/source-a_output")
        self.window._apply_source_path(second)
        self.assertEqual(self.window.output_edit.text(), "/tmp/source-b_output")
        self.window._output_user_selected = True
        self.window.output_edit.setText("/tmp/custom-output")
        self.window._apply_source_path(first)
        self.assertEqual(self.window.output_edit.text(), "/tmp/custom-output")


class V135ConfigTests(unittest.TestCase):
    def test_line_animated_config_is_isolated(self) -> None:
        self.assertEqual(LINE_ANIMATED_CONFIG.sticker_size, (270, 270))
        self.assertEqual(LINE_CONFIG.sticker_size, (370, 320))
