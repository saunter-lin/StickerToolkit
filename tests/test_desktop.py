from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image, ImageDraw
from PySide6.QtCore import QEventLoop, QLocale, QSettings, QSize, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QColorDialog, QFileDialog, QMessageBox

from sticker_toolkit.core import ProcessingOptions, ProcessingResult
from sticker_toolkit.services import StickerService
from sticker_toolkit.ui.desktop import app as desktop_app
from sticker_toolkit.ui.desktop.controllers import StickerController
from sticker_toolkit.ui.desktop.main_window import (
    BACKGROUND_PRESET_CUSTOM,
    BACKGROUND_PRESET_DARKBLUE,
    BACKGROUND_PRESET_OFFWHITE,
    MainWindow,
)
from sticker_toolkit.ui.desktop.output_paths import (
    output_directory_from_root,
    suggested_output_directory,
)
from sticker_toolkit.ui.desktop.view_model import (
    DesktopFormData,
    DesktopValidationError,
    banner_enabled,
    build_processing_options,
)
from sticker_toolkit.ui.desktop.workers import StickerWorker


def sample_sheet(path: Path) -> None:
    sheet = Image.new("RGBA", (400, 400), "white")
    draw = ImageDraw.Draw(sheet)
    for index in range(16):
        row, column = divmod(index, 4)
        x, y = column * 100, row * 100
        draw.ellipse((x + 15, y + 10, x + 85, y + 88), fill=(40 + index * 8, 90, 160, 255))
    sheet.save(path)


class DesktopViewModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "sheet.png"
        sample_sheet(self.source)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def form(self, **changes: object) -> DesktopFormData:
        values: dict[str, object] = {
            "source_path": str(self.source),
            "platform": "line",
            "rows": 4,
            "columns": 4,
            "banner_path": "",
            "output_directory": str(self.root / "output"),
        }
        values.update(changes)
        return DesktopFormData(**values)  # type: ignore[arg-type]

    def test_source_platform_and_grid_are_required(self) -> None:
        for changes in (
            {"source_path": ""},
            {"platform": ""},
            {"rows": 0},
            {"columns": 0},
            {"rows": 3},
        ):
            with self.subTest(changes=changes), self.assertRaises(DesktopValidationError):
                build_processing_options(self.form(**changes))

    def test_banner_state_matches_platform(self) -> None:
        self.assertFalse(banner_enabled("line"))
        self.assertTrue(banner_enabled("wechat"))
        self.assertTrue(banner_enabled("both"))

    def test_form_builds_processing_options_including_banner(self) -> None:
        banner = self.root / "banner.png"
        Image.new("RGB", (750, 400), "blue").save(banner)
        options = build_processing_options(
            self.form(
                platform="both",
                banner_path=str(banner),
                create_preview=False,
                create_zip=False,
            )
        )
        self.assertEqual(options.platform, "both")
        self.assertEqual(options.banner_path, banner.resolve())
        self.assertFalse(options.create_preview)
        self.assertFalse(options.create_zip)

    def test_form_builds_solid_background_options(self) -> None:
        options = build_processing_options(
            self.form(
                remove_solid_background=True,
                auto_detect_solid_background=False,
                solid_background_color="#fff8ec",
                solid_background_tolerance=5,
            )
        )
        self.assertTrue(options.remove_solid_background)
        self.assertFalse(options.auto_detect_solid_background)
        self.assertEqual(options.solid_background_color, "#FFF8EC")
        self.assertEqual(options.solid_background_tolerance, 5)

    def test_background_tolerance_and_color_are_validated(self) -> None:
        with self.assertRaisesRegex(DesktopValidationError, "0～30"):
            build_processing_options(self.form(remove_solid_background=True, solid_background_tolerance=31))
        with self.assertRaisesRegex(DesktopValidationError, "#RRGGBB"):
            build_processing_options(self.form(remove_solid_background=True, solid_background_color="cream"))

    def test_output_directory_must_be_writable(self) -> None:
        with (
            patch(
                "sticker_toolkit.ui.desktop.view_model.output_directory_is_writable",
                return_value=False,
            ),
            self.assertRaisesRegex(DesktopValidationError, "無法寫入"),
        ):
            build_processing_options(self.form())

    def test_line_export_uses_output_below_selected_root(self) -> None:
        selected_root = self.root / "manual-root"
        options = build_processing_options(self.form(output_directory=str(selected_root)))
        result = StickerService().process(self.source, options).for_platform("line")
        self.assertEqual(
            result.output_directory,
            (selected_root / "output" / "line_sticker").resolve(),
        )
        self.assertTrue((selected_root / "output" / "preview" / "line").is_dir())
        self.assertTrue((selected_root / "output" / "line_sticker.zip").is_file())
        self.assertFalse((selected_root / "line_sticker").exists())


class DesktopOutputPathTests(unittest.TestCase):
    def test_suggested_output_uses_source_stem(self) -> None:
        cases = {
            "berry.png": "berry_output",
            "中文 貼圖.JPG": "中文 貼圖_output",
            "my.sticker.sheet.PNG": "my.sticker.sheet_output",
        }
        for source_name, expected in cases.items():
            with self.subTest(source_name=source_name):
                source = Path("/source") / source_name
                self.assertEqual(suggested_output_directory(source), Path("/source") / expected)

    def test_output_root_adds_output_directory_once(self) -> None:
        self.assertEqual(
            output_directory_from_root(Path("/chosen/root")),
            Path("/chosen/root/output"),
        )
        self.assertEqual(
            output_directory_from_root(Path("/chosen/output")),
            Path("/chosen/output"),
        )
        self.assertEqual(
            output_directory_from_root(Path("/chosen/OUTPUT")),
            Path("/chosen/OUTPUT"),
        )


class DesktopWorkerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "sheet.png"
        sample_sheet(self.source)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_worker_emits_progress_and_completed(self) -> None:
        progress: list[int] = []
        completed: list[ProcessingResult] = []
        failed: list[Exception] = []
        worker = StickerWorker(
            StickerController(),
            self.source,
            ProcessingOptions(platform="line", output_directory=self.root / "output"),
        )
        worker.progress_changed.connect(lambda value, _message: progress.append(value))
        worker.completed.connect(completed.append)
        worker.failed.connect(failed.append)
        worker.run()
        self.assertEqual(progress[0], 0)
        self.assertEqual(progress[-1], 100)
        self.assertEqual(len(completed), 1)
        self.assertFalse(failed)

    def test_worker_emits_failed(self) -> None:
        controller = StickerController()
        controller.service = Mock()
        controller.service.process.side_effect = RuntimeError("boom")
        errors: list[Exception] = []
        worker = StickerWorker(
            controller,
            self.source,
            ProcessingOptions(output_directory=self.root / "output"),
        )
        worker.failed.connect(errors.append)
        worker.run()
        self.assertEqual(str(errors[0]), "boom")

    def test_worker_integrates_all_platform_options(self) -> None:
        for platform in ("line", "wechat", "both"):
            output = self.root / platform / "output"
            completed: list[ProcessingResult] = []
            worker = StickerWorker(
                StickerController(StickerService()),
                self.source,
                ProcessingOptions(platform=platform, output_directory=output),
            )
            worker.completed.connect(completed.append)
            worker.run()
            self.assertEqual(len(completed), 1)
            self.assertTrue((output / "preview").is_dir())
            self.assertFalse((self.root / platform / "01.png").exists())
            if platform in {"line", "both"}:
                self.assertTrue((output / "line_sticker.zip").is_file())
            if platform in {"wechat", "both"}:
                self.assertTrue((output / "wechat_sticker.zip").is_file())


class MainWindowStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])
        cls.settings_temp = tempfile.TemporaryDirectory()
        QSettings.setDefaultFormat(QSettings.Format.IniFormat)
        QSettings.setPath(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            cls.settings_temp.name,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.settings_temp.cleanup()

    @staticmethod
    def _clear_desktop_settings() -> None:
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
            settings.sync()

    def setUp(self) -> None:
        self._clear_desktop_settings()
        for settings in (
            QSettings("StickerToolkit", "StickerToolkit"),
            QSettings(
                QSettings.Format.IniFormat,
                QSettings.Scope.UserScope,
                "StickerToolkit",
                "StickerToolkit",
            ),
        ):
            settings.setValue("language", "zh_TW")
            settings.sync()
        self.window = MainWindow()
        self.test_temp = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        if self.window._thread is not None:
            self.window._thread.quit()
            self.window._thread.wait(5_000)
            self.window._thread = None
        with patch.object(QMessageBox, "information"):
            self.window.close()
        self.window.settings.clear()
        self.window.settings.sync()
        self.test_temp.cleanup()

    def wait_for_worker(self) -> None:
        thread = self.window._thread
        if thread is None:
            return
        loop = QEventLoop()
        timed_out = False

        def timeout() -> None:
            nonlocal timed_out
            timed_out = True
            loop.quit()

        thread.finished.connect(loop.quit)
        QTimer.singleShot(10_000, timeout)
        loop.exec()
        QApplication.processEvents()
        if timed_out:
            self.fail("桌面 worker 未在期限內完成")

    def test_background_controls_are_disabled_until_feature_is_checked(self) -> None:
        self.assertFalse(self.window.remove_background_checkbox.isChecked())
        self.assertFalse(self.window.background_preset_combo.isEnabled())
        self.assertFalse(self.window.background_tolerance_spin.isEnabled())
        self.window.remove_background_checkbox.setChecked(True)
        self.assertTrue(self.window.background_preset_combo.isEnabled())
        self.assertTrue(self.window.background_tolerance_spin.isEnabled())

    def test_background_presets_use_fixed_colors_and_native_swatches(self) -> None:
        combo = self.window.background_preset_combo
        self.assertEqual(combo.iconSize(), QSize(32, 16))
        for preset, color in (
            (BACKGROUND_PRESET_OFFWHITE, "#FFF8EC"),
            (BACKGROUND_PRESET_DARKBLUE, "#003366"),
        ):
            index = combo.findData(preset)
            combo.setCurrentIndex(index)
            self.assertEqual(self.window._solid_background_color, color)
            swatch = combo.itemIcon(index).pixmap(QSize(32, 16)).toImage()
            self.assertEqual(swatch.size(), QSize(32, 16))
            self.assertEqual(swatch.pixelColor(5, 5).name().upper(), color)
            self.assertEqual(swatch.pixelColor(0, 0).name().upper(), "#808080")

    def test_source_selection_keeps_selected_preset_color(self) -> None:
        source = Path(self.test_temp.name) / "純色 合集.png"
        Image.new("RGB", (80, 80), (255, 248, 236)).save(source)
        self.window.remove_background_checkbox.setChecked(True)
        self.window.background_preset_combo.setCurrentIndex(
            self.window.background_preset_combo.findData(BACKGROUND_PRESET_DARKBLUE)
        )
        self.window._apply_source_path(source)
        self.assertEqual(self.window._solid_background_color, "#003366")
        form = self.window._form_data()
        self.assertFalse(form.auto_detect_solid_background)
        self.assertEqual(form.solid_background_color, "#003366")

    def test_custom_color_updates_separately_and_persists(self) -> None:
        combo = self.window.background_preset_combo
        combo.setCurrentIndex(combo.findData(BACKGROUND_PRESET_CUSTOM))
        with patch.object(QColorDialog, "getColor", return_value=QColor("#287A65")):
            combo.activated.emit(combo.currentIndex())
        self.assertEqual(self.window._solid_background_color, "#287A65")
        self.assertEqual(self.window.settings.value("solid_background_custom_color"), "#287A65")
        self.assertIn("#287A65", combo.currentText())

        combo.setCurrentIndex(combo.findData(BACKGROUND_PRESET_DARKBLUE))
        self.assertEqual(self.window._solid_background_color, "#003366")
        combo.setCurrentIndex(combo.findData(BACKGROUND_PRESET_CUSTOM))
        self.assertEqual(self.window._solid_background_color, "#287A65")

        with patch.object(QMessageBox, "information"):
            self.window.close()
        self.window = MainWindow()
        self.assertEqual(
            self.window.background_preset_combo.currentData(), BACKGROUND_PRESET_CUSTOM
        )
        self.assertEqual(self.window._solid_background_color, "#287A65")

    def test_custom_color_can_be_updated_immediately(self) -> None:
        combo = self.window.background_preset_combo
        combo.setCurrentIndex(combo.findData(BACKGROUND_PRESET_CUSTOM))
        with patch.object(QColorDialog, "getColor", return_value=QColor("#882244")):
            self.window._choose_background_color()
        self.assertEqual(self.window._custom_background_color, "#882244")
        self.assertEqual(self.window._solid_background_color, "#882244")
        self.assertIn("#882244", combo.currentText())
        swatch = combo.itemIcon(combo.currentIndex()).pixmap(QSize(32, 16)).toImage()
        self.assertEqual(swatch.pixelColor(5, 5).name().upper(), "#882244")

    def test_each_background_preset_persists(self) -> None:
        for preset in (
            BACKGROUND_PRESET_OFFWHITE,
            BACKGROUND_PRESET_DARKBLUE,
            BACKGROUND_PRESET_CUSTOM,
        ):
            with self.subTest(preset=preset):
                combo = self.window.background_preset_combo
                combo.setCurrentIndex(combo.findData(preset))
                with patch.object(QMessageBox, "information"):
                    self.window.close()
                self.window = MainWindow()
                self.assertEqual(self.window.background_preset_combo.currentData(), preset)

    def test_legacy_background_settings_migrate_safely(self) -> None:
        with patch.object(QMessageBox, "information"):
            self.window.close()
        self._clear_desktop_settings()
        settings = QSettings("StickerToolkit", "StickerToolkit")
        settings.setValue("language", "zh_TW")
        settings.setValue("auto_detect_solid_background", False)
        settings.setValue("solid_background_color", "#287A65")
        settings.sync()
        self.window = MainWindow()
        self.assertEqual(
            self.window.background_preset_combo.currentData(), BACKGROUND_PRESET_CUSTOM
        )
        self.assertEqual(self.window._solid_background_color, "#287A65")

        with patch.object(QMessageBox, "information"):
            self.window.close()
        self._clear_desktop_settings()
        settings = QSettings("StickerToolkit", "StickerToolkit")
        settings.setValue("solid_background_preset", "invalid")
        settings.setValue("solid_background_custom_color", "not-a-color")
        settings.setValue("solid_background_color", "broken")
        settings.sync()
        self.window = MainWindow()
        self.assertEqual(
            self.window.background_preset_combo.currentData(), BACKGROUND_PRESET_OFFWHITE
        )
        self.assertEqual(self.window._solid_background_color, "#FFF8EC")

    def test_start_disabled_without_source(self) -> None:
        self.assertFalse(self.window.start_button.isEnabled())
        self.assertEqual(self.window.output_edit.text(), "")

    def test_first_launch_uses_system_language_and_saved_language_wins(self) -> None:
        with patch.object(QMessageBox, "information"):
            self.window.close()
        self._clear_desktop_settings()
        with patch(
            "sticker_toolkit.ui.desktop.main_window.QLocale.system",
            return_value=QLocale("zh_CN"),
        ):
            self.window = MainWindow()
        self.assertEqual(self.window.language, "zh_CN")
        self.assertEqual(self.window.start_button.text(), "开始处理")

        self.window.language_combo.setCurrentIndex(self.window.language_combo.findData("en"))
        with patch.object(QMessageBox, "information"):
            self.window.close()
        with patch(
            "sticker_toolkit.ui.desktop.main_window.QLocale.system",
            return_value=QLocale("zh_TW"),
        ):
            self.window = MainWindow()
        self.assertEqual(self.window.language, "en")
        self.assertEqual(self.window.start_button.text(), "Start Processing")

    def test_language_switch_updates_ui_without_changing_form_state(self) -> None:
        source = Path(self.test_temp.name) / "貼圖 sheet.png"
        output = Path(self.test_temp.name) / "輸出 root"
        self.window.source_edit.setText(str(source))
        self.window.output_edit.setText(str(output))
        self.window.platform_combo.setCurrentIndex(self.window.platform_combo.findData("both"))
        self.window.background_tolerance_spin.setValue(12)
        self.window.remove_background_checkbox.setChecked(True)

        self.window.language_combo.setCurrentIndex(self.window.language_combo.findData("en"))
        self.assertEqual(self.window.start_button.text(), "Start Processing")
        self.assertEqual(self.window.source_edit.text(), str(source))
        self.assertEqual(self.window.output_edit.text(), str(output))
        self.assertEqual(self.window.platform_combo.currentData(), "both")
        self.assertEqual(self.window.background_tolerance_spin.value(), 12)
        self.assertTrue(self.window.remove_background_checkbox.isChecked())

        self.window.language_combo.setCurrentIndex(self.window.language_combo.findData("zh_CN"))
        self.assertEqual(self.window.start_button.text(), "开始处理")
        self.assertEqual(self.window.settings.value("language"), "zh_CN")
        self.assertEqual(self.window.platform_combo.currentData(), "both")

    def test_windows_uses_user_scope_ini_settings(self) -> None:
        with patch("sticker_toolkit.ui.desktop.main_window.sys.platform", "win32"):
            windows_window = MainWindow()
        try:
            self.assertEqual(windows_window.settings.format(), QSettings.Format.IniFormat)
        finally:
            with patch.object(QMessageBox, "information"):
                windows_window.close()

    def test_wide_window_centers_bounded_content_and_keeps_grid_compact(self) -> None:
        self.window.resize(1920, 1080)
        self.window.show()
        QApplication.processEvents()

        central_width = self.window.scroll_area.viewport().width()
        content = self.window.content_widget
        self.assertLessEqual(content.width(), 1080)
        self.assertGreaterEqual(content.width(), 760)
        left_gap = content.x()
        right_gap = central_width - content.geometry().right() - 1
        self.assertLessEqual(abs(left_gap - right_gap), 1)

        self.assertLess(self.window.columns_spin.geometry().right(), self.window.grid_group.width() // 2)
        for widget in (
            self.window.rows_spin,
            self.window.columns_spin,
            self.window.source_button,
            self.window.output_button,
        ):
            self.assertGreaterEqual(widget.width(), widget.minimumSizeHint().width())

    def test_short_window_scrolls_all_content_without_horizontal_scrollbar(self) -> None:
        self.window.resize(900, 500)
        self.window.show()
        QApplication.processEvents()

        vertical = self.window.scroll_area.verticalScrollBar()
        horizontal = self.window.scroll_area.horizontalScrollBar()
        self.assertGreater(vertical.maximum(), 0)
        self.assertEqual(horizontal.maximum(), 0)
        self.assertTrue(vertical.isVisible())
        self.assertFalse(horizontal.isVisible())

        vertical.setValue(vertical.maximum())
        QApplication.processEvents()
        self.assertEqual(vertical.value(), vertical.maximum())
        self.assertTrue(self.window.open_output_button.isVisible())

    def test_unhandled_exception_is_logged_and_shown(self) -> None:
        error = RuntimeError("boom")
        with (
            patch.object(desktop_app.logger, "critical") as critical,
            patch.object(QMessageBox, "critical") as message,
        ):
            desktop_app._show_unhandled_exception(RuntimeError, error, None)
        critical.assert_called_once()
        message.assert_called_once()
        self.assertIn("RuntimeError: boom", message.call_args.args[2])

    def test_automatic_output_updates_with_each_source(self) -> None:
        first = Path(self.test_temp.name) / "berry.png"
        second = Path(self.test_temp.name) / "中文.貼圖.PNG"
        self.window._apply_source_path(first)
        self.assertEqual(self.window.output_edit.text(), str(first.parent / "berry_output"))
        self.window._apply_source_path(second)
        self.assertEqual(self.window.output_edit.text(), str(second.parent / "中文.貼圖_output"))

    def test_manual_output_is_not_replaced_by_new_source(self) -> None:
        manual = Path(self.test_temp.name) / "自訂輸出"
        manual.mkdir()
        with patch.object(QFileDialog, "getExistingDirectory", return_value=str(manual)):
            self.window._choose_output()
        self.window._apply_source_path(Path(self.test_temp.name) / "another.sheet.png")
        self.assertEqual(self.window.output_edit.text(), str(manual))
        self.assertTrue(self.window._output_user_selected)
        self.assertIsNone(self.window.settings.value("output_directory_mode"))
        self.assertIsNone(self.window.settings.value("last_manual_output_directory"))

    def test_manual_output_is_not_restored_in_a_new_session(self) -> None:
        manual = Path(self.test_temp.name) / "saved"
        manual.mkdir()
        self.window.settings.setValue("output_directory_mode", "manual")
        self.window.settings.setValue("last_manual_output_directory", str(manual))
        self.window.language_combo.setCurrentIndex(self.window.language_combo.findData("en"))
        with patch.object(QMessageBox, "information"):
            self.window.close()
        self.window = MainWindow()
        self.assertEqual(self.window.output_edit.text(), "")
        self.assertFalse(self.window._output_user_selected)
        self.assertIsNone(self.window.settings.value("output_directory_mode"))
        self.assertIsNone(self.window.settings.value("last_manual_output_directory"))
        self.assertEqual(self.window.language, "en")
        source = Path(self.test_temp.name) / "source-c.png"
        self.window._apply_source_path(source)
        self.assertEqual(self.window.output_edit.text(), str(source.parent / "source-c_output"))

    def test_banner_controls_follow_platform(self) -> None:
        self.window.platform_combo.setCurrentIndex(self.window.platform_combo.findData("line"))
        self.assertFalse(self.window.banner_group.isEnabled())
        self.window.platform_combo.setCurrentIndex(self.window.platform_combo.findData("wechat"))
        self.assertTrue(self.window.banner_group.isEnabled())
        self.window.platform_combo.setCurrentIndex(self.window.platform_combo.findData("both"))
        self.assertTrue(self.window.banner_group.isEnabled())

    def test_controls_disable_and_restore_for_processing(self) -> None:
        self.window.source_edit.setText("/tmp/source.png")
        self.window._set_processing(True)
        self.assertFalse(self.window.source_button.isEnabled())
        self.assertFalse(self.window.platform_combo.isEnabled())
        self.assertFalse(self.window.start_button.isEnabled())
        self.window._set_processing(False)
        self.assertTrue(self.window.source_button.isEnabled())
        self.assertTrue(self.window.platform_combo.isEnabled())
        self.assertTrue(self.window.start_button.isEnabled())

    def test_controls_restore_after_completion_and_failure(self) -> None:
        self.window.source_edit.setText("/tmp/source.png")
        self.window._set_processing(True)
        result = ProcessingResult(Path("/tmp/source.png"), ())
        with patch.object(QMessageBox, "information"):
            self.window._on_completed(result)
        self.window._thread = None
        self.window._on_worker_finished()
        self.assertTrue(self.window.source_button.isEnabled())

    def test_window_runs_success_and_failure_in_background(self) -> None:
        root = Path(self.test_temp.name)
        source = root / "sheet.png"
        sample_sheet(source)
        self.window.source_edit.setText(str(source))
        self.window.output_edit.setText(str(root / "output"))
        self.window._refresh_start_enabled()
        with patch.object(QMessageBox, "information"):
            self.window._start_processing()
            self.assertFalse(self.window.source_button.isEnabled())
            self.wait_for_worker()
        self.assertEqual(self.window.progress_bar.value(), 100)
        self.assertTrue(self.window.source_button.isEnabled())
        self.assertTrue((root / "output" / "line_sticker.zip").is_file())

        broken = root / "broken.png"
        broken.write_bytes(b"not an image")
        self.window.source_edit.setText(str(broken))
        with patch.object(QMessageBox, "critical"):
            self.window._start_processing()
            self.wait_for_worker()
        self.assertEqual(self.window.status_label.text(), "處理失敗")
        self.assertTrue(self.window.source_button.isEnabled())

        self.window._set_processing(True)
        with patch.object(QMessageBox, "critical"):
            self.window._on_failed(RuntimeError("boom"))
        self.window._thread = None
        self.window._on_worker_finished()
        self.assertTrue(self.window.source_button.isEnabled())
