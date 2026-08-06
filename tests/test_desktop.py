from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image, ImageDraw
from PySide6.QtCore import QEventLoop, QSettings, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from sticker_toolkit.core import ProcessingOptions, ProcessingResult
from sticker_toolkit.services import StickerService
from sticker_toolkit.ui.desktop.controllers import StickerController
from sticker_toolkit.ui.desktop.main_window import MainWindow
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

    def setUp(self) -> None:
        QSettings("StickerToolkit", "StickerToolkit").clear()
        self.window = MainWindow()
        self.test_temp = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        if self.window._thread is not None:
            self.window._thread.quit()
            self.window._thread.wait(5_000)
            self.window._thread = None
        with patch.object(QMessageBox, "information"):
            self.window.close()
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

    def test_start_disabled_without_source(self) -> None:
        self.assertFalse(self.window.start_button.isEnabled())

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
