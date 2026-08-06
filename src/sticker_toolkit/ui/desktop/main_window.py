"""Sticker Toolkit PySide6 主視窗。"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QSettings, QThread, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from sticker_toolkit.core import ProcessingResult
from sticker_toolkit.version import __version__

from .controllers import StickerController
from .output_paths import suggested_output_directory
from .platform_utils import open_in_file_manager
from .view_model import (
    DesktopFormData,
    DesktopValidationError,
    banner_enabled,
    result_summary,
    user_error_message,
)
from .workers import StickerWorker

logger = logging.getLogger(__name__)

PLATFORMS = (("LINE", "line"), ("微信", "wechat"), ("LINE＋微信", "both"))


class MainWindow(QMainWindow):
    def __init__(self, controller: StickerController | None = None) -> None:
        super().__init__()
        self.controller = controller or StickerController()
        self.settings = QSettings("StickerToolkit", "StickerToolkit")
        self._thread: QThread | None = None
        self._worker: StickerWorker | None = None
        self._last_result: ProcessingResult | None = None
        self._output_user_selected = False
        self._build_ui()
        self._restore_settings()
        self._update_banner_state()
        self._refresh_start_enabled()

    def _build_ui(self) -> None:
        self.setWindowTitle(f"Sticker Toolkit {__version__}")
        self.resize(760, 680)
        root = QWidget(self)
        layout = QVBoxLayout(root)
        layout.setSpacing(12)
        self.setCentralWidget(root)

        title = QLabel("Sticker Toolkit")
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        layout.addWidget(title)

        source_group = QGroupBox("來源圖片")
        source_layout = QHBoxLayout(source_group)
        self.source_edit = self._path_edit("尚未選擇來源圖片")
        self.source_button = QPushButton("選擇圖片")
        self.source_button.clicked.connect(self._choose_source)
        source_layout.addWidget(self.source_edit, 1)
        source_layout.addWidget(self.source_button)
        layout.addWidget(source_group)

        platform_group = QGroupBox("輸出平台")
        platform_layout = QFormLayout(platform_group)
        self.platform_combo = QComboBox()
        for label, value in PLATFORMS:
            self.platform_combo.addItem(label, value)
        self.platform_combo.currentIndexChanged.connect(self._update_banner_state)
        platform_layout.addRow("平台：", self.platform_combo)
        layout.addWidget(platform_group)

        grid_group = QGroupBox("圖片切割設定")
        grid_layout = QGridLayout(grid_group)
        self.rows_spin = QSpinBox()
        self.columns_spin = QSpinBox()
        for spin in (self.rows_spin, self.columns_spin):
            spin.setRange(1, 99)
            spin.setValue(4)
        grid_layout.addWidget(QLabel("行數："), 0, 0)
        grid_layout.addWidget(self.rows_spin, 0, 1)
        grid_layout.addWidget(QLabel("列數："), 0, 2)
        grid_layout.addWidget(self.columns_spin, 0, 3)
        layout.addWidget(grid_group)

        self.banner_group = QGroupBox("微信 Banner")
        banner_layout = QHBoxLayout(self.banner_group)
        self.banner_edit = self._path_edit("未選擇時沿用既有無 Banner 行為")
        self.banner_button = QPushButton("選擇")
        self.banner_clear_button = QPushButton("清除")
        self.banner_button.clicked.connect(self._choose_banner)
        self.banner_clear_button.clicked.connect(self.banner_edit.clear)
        banner_layout.addWidget(self.banner_edit, 1)
        banner_layout.addWidget(self.banner_button)
        banner_layout.addWidget(self.banner_clear_button)
        layout.addWidget(self.banner_group)

        output_group = QGroupBox("輸出位置")
        output_layout = QHBoxLayout(output_group)
        self.output_edit = self._path_edit("選擇來源圖片後自動建立輸出位置")
        self.output_button = QPushButton("選擇目錄")
        self.output_button.clicked.connect(self._choose_output)
        output_layout.addWidget(self.output_edit, 1)
        output_layout.addWidget(self.output_button)
        layout.addWidget(output_group)

        options_group = QGroupBox("處理選項")
        options_layout = QHBoxLayout(options_group)
        self.trim_checkbox = QCheckBox("去除空白邊")
        self.padding_checkbox = QCheckBox("保留安全留白")
        self.preview_checkbox = QCheckBox("建立預覽圖")
        self.zip_checkbox = QCheckBox("建立 ZIP")
        for checkbox in (
            self.trim_checkbox,
            self.padding_checkbox,
            self.preview_checkbox,
            self.zip_checkbox,
        ):
            checkbox.setChecked(True)
            options_layout.addWidget(checkbox)
        self.trim_checkbox.setEnabled(False)
        self.padding_checkbox.setEnabled(False)
        layout.addWidget(options_group)

        self.start_button = QPushButton("開始處理")
        self.start_button.setMinimumHeight(38)
        self.start_button.clicked.connect(self._start_processing)
        layout.addWidget(self.start_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.status_label = QLabel("等待開始")
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)

        self.result_text = QPlainTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("處理結果會顯示在這裡")
        self.result_text.setMinimumHeight(125)
        layout.addWidget(self.result_text)

        self.open_output_button = QPushButton("開啟輸出資料夾")
        self.open_output_button.setEnabled(False)
        self.open_output_button.clicked.connect(self._open_output)
        layout.addWidget(self.open_output_button)

    @staticmethod
    def _path_edit(placeholder: str) -> QLineEdit:
        edit = QLineEdit()
        edit.setReadOnly(True)
        edit.setPlaceholderText(placeholder)
        edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return edit

    def _restore_settings(self) -> None:
        platform = str(self.settings.value("platform", "line"))
        index = self.platform_combo.findData(platform)
        self.platform_combo.setCurrentIndex(index if index >= 0 else 0)
        mode = str(self.settings.value("output_directory_mode", ""))
        output = str(self.settings.value("last_manual_output_directory", ""))
        if mode == "manual" and output and Path(output).is_dir():
            self.output_edit.setText(output)
            self._output_user_selected = True
        geometry = self.settings.value("window_geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)

    def _dialog_directory(self, key: str) -> str:
        saved = str(self.settings.value(key, ""))
        return saved if Path(saved).is_dir() else str(Path.home())

    @Slot()
    def _choose_source(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "選擇貼圖合集",
            self._dialog_directory("last_source_directory"),
            "圖片 (*.png *.jpg *.jpeg *.webp)",
        )
        if not path:
            return
        source = Path(path)
        self._apply_source_path(source)

    def _apply_source_path(self, source: Path) -> None:
        """Apply a selected source and refresh only an automatic output suggestion."""
        self.source_edit.setText(str(source))
        self.settings.setValue("last_source_directory", str(source.parent))
        if not self._output_user_selected:
            self.output_edit.setText(str(suggested_output_directory(source)))
        self._refresh_start_enabled()

    @Slot()
    def _choose_banner(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "選擇微信 Banner",
            self._dialog_directory("last_source_directory"),
            "圖片 (*.png *.jpg *.jpeg *.webp)",
        )
        if path:
            self.banner_edit.setText(path)

    @Slot()
    def _choose_output(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "選擇輸出目錄", self._dialog_directory("last_manual_output_directory")
        )
        if path:
            self.output_edit.setText(path)
            self._output_user_selected = True
            self.settings.setValue("output_directory_mode", "manual")
            self.settings.setValue("last_manual_output_directory", path)
            self._refresh_start_enabled()

    @Slot()
    def _update_banner_state(self) -> None:
        enabled = banner_enabled(str(self.platform_combo.currentData())) and self._thread is None
        self.banner_group.setEnabled(enabled)
        self._refresh_start_enabled()

    def _form_data(self) -> DesktopFormData:
        return DesktopFormData(
            source_path=self.source_edit.text(),
            platform=str(self.platform_combo.currentData() or ""),
            rows=self.rows_spin.value(),
            columns=self.columns_spin.value(),
            banner_path=self.banner_edit.text(),
            output_directory=self.output_edit.text(),
            trim_enabled=self.trim_checkbox.isChecked(),
            create_preview=self.preview_checkbox.isChecked(),
            create_zip=self.zip_checkbox.isChecked(),
        )

    def _refresh_start_enabled(self) -> None:
        if not hasattr(self, "start_button"):
            return
        ready = bool(self.source_edit.text() and self.platform_combo.currentData())
        self.start_button.setEnabled(ready and self._thread is None)

    @Slot()
    def _start_processing(self) -> None:
        try:
            source, options = self.controller.build_request(self._form_data())
        except DesktopValidationError as exc:
            QMessageBox.warning(self, "輸入資料不完整", str(exc))
            return
        self.settings.setValue("platform", options.platform)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在啟動處理…")
        self.result_text.clear()
        self.open_output_button.setEnabled(False)
        self._set_processing(True)

        thread = QThread(self)
        worker = StickerWorker(self.controller, source, options)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress_changed.connect(self._on_progress)
        worker.completed.connect(self._on_completed)
        worker.failed.connect(self._on_failed)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_worker_finished)
        self._thread = thread
        self._worker = worker
        thread.start()

    def _set_processing(self, processing: bool) -> None:
        for widget in (
            self.source_button,
            self.platform_combo,
            self.rows_spin,
            self.columns_spin,
            self.banner_button,
            self.banner_clear_button,
            self.output_button,
            self.preview_checkbox,
            self.zip_checkbox,
        ):
            widget.setEnabled(not processing)
        self.start_button.setEnabled(not processing and bool(self.source_edit.text()))
        if not processing:
            self._update_banner_state()

    @Slot(int, str)
    def _on_progress(self, percent: int, message: str) -> None:
        self.progress_bar.setValue(max(0, min(100, percent)))
        self.status_label.setText(message)

    @Slot(object)
    def _on_completed(self, result: ProcessingResult) -> None:
        self._last_result = result
        self.progress_bar.setValue(100)
        self.status_label.setText("處理完成")
        self.result_text.setPlainText(result_summary(result))
        self.open_output_button.setEnabled(True)
        QMessageBox.information(self, "處理完成", "貼圖素材已成功輸出。")

    @Slot(object)
    def _on_failed(self, error: Exception) -> None:
        self._last_result = None
        self.status_label.setText("處理失敗")
        message = user_error_message(error)
        self.result_text.setPlainText(message)
        QMessageBox.critical(self, "處理失敗", message)

    @Slot()
    def _on_worker_finished(self) -> None:
        self._thread = None
        self._worker = None
        self._set_processing(False)

    @Slot()
    def _open_output(self) -> None:
        if self._last_result is None:
            return
        try:
            open_in_file_manager(Path(self.output_edit.text()))
        except OSError as exc:
            logger.exception("Unable to open output directory")
            QMessageBox.warning(self, "無法開啟輸出目錄", str(exc))

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._thread is not None:
            QMessageBox.information(self, "處理進行中", "請等待目前的圖片處理完成。")
            event.ignore()
            return
        self.settings.setValue("platform", self.platform_combo.currentData())
        self.settings.setValue("window_geometry", self.saveGeometry())
        super().closeEvent(event)
