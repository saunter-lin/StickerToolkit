"""Sticker Toolkit PySide6 主視窗。"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import cast

from PySide6.QtCore import QLocale, QSettings, Qt, QThread, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from sticker_toolkit.core import (
    ProcessingResult,
    color_to_hex,
    detect_solid_background_color,
    load_image,
)
from sticker_toolkit.version import __version__

from .controllers import StickerController
from .i18n import (
    LANGUAGE_LABELS,
    normalize_language,
    tr,
    translate_progress,
    translate_user_message,
    translate_visible_text,
)
from .output_paths import output_directory_from_root, suggested_output_directory
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
CONTENT_MAX_WIDTH = 1080


class MainWindow(QMainWindow):
    def __init__(self, controller: StickerController | None = None) -> None:
        super().__init__()
        self.controller = controller or StickerController()
        if sys.platform == "win32":
            self.settings = QSettings(
                QSettings.Format.IniFormat,
                QSettings.Scope.UserScope,
                "StickerToolkit",
                "StickerToolkit",
            )
        else:
            self.settings = QSettings("StickerToolkit", "StickerToolkit")
        self._thread: QThread | None = None
        self._worker: StickerWorker | None = None
        self._last_result: ProcessingResult | None = None
        self._last_error: Exception | None = None
        self._output_user_selected = False
        self._solid_background_color = "#FFF8EC"
        self._batch_source_paths: list[Path] = []
        self._last_input_mode = "sheet"
        saved_language = self.settings.value("language")
        self.language = normalize_language(
            str(saved_language) if saved_language is not None else None,
            QLocale.system().name(),
        )
        self._last_progress_message = ""
        self.line_cover_mode_combo: QComboBox
        self.line_cover_edit: QLineEdit
        self.line_cover_button: QPushButton
        self.wechat_cover_mode_combo: QComboBox
        self.wechat_cover_edit: QLineEdit
        self.wechat_cover_button: QPushButton
        self._build_ui()
        self._restore_settings()
        self._update_input_mode()
        self._update_banner_state()
        self._update_cover_state()
        self._update_background_state()
        self._refresh_start_enabled()

        self._retranslate_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle(f"Sticker Toolkit {__version__}")
        self.resize(800, 980)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addStretch(1)
        self.content_widget = QWidget(root)
        self.content_widget.setMinimumWidth(760)
        self.content_widget.setMaximumWidth(CONTENT_MAX_WIDTH)
        self.content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        root_layout.addWidget(self.content_widget, 100)
        root_layout.addStretch(1)
        layout = QVBoxLayout(self.content_widget)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        layout.setSpacing(12)
        self.scroll_area.setWidget(root)
        self.setCentralWidget(self.scroll_area)

        header = QHBoxLayout()
        title = QLabel("Sticker Toolkit")
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        header.addWidget(title)
        header.addStretch(1)
        self.language_label = QLabel("Language:")
        self.language_combo = QComboBox()
        for code, label in LANGUAGE_LABELS.items():
            self.language_combo.addItem(label, code)
        language_index = self.language_combo.findData(self.language)
        self.language_combo.setCurrentIndex(language_index if language_index >= 0 else 0)
        self.language_combo.currentIndexChanged.connect(self._change_language)
        header.addWidget(self.language_label)
        header.addWidget(self.language_combo)
        layout.addLayout(header)

        mode_group = QGroupBox("輸入模式")
        mode_layout = QFormLayout(mode_group)
        self.input_mode_combo = QComboBox()
        self.input_mode_combo.addItem("整合圖", "sheet")
        self.input_mode_combo.addItem("WeChat 批次單圖", "wechat_batch")
        self.input_mode_combo.currentIndexChanged.connect(self._update_input_mode)
        mode_layout.addRow("模式：", self.input_mode_combo)
        layout.addWidget(mode_group)

        source_group = QGroupBox("來源圖片")
        source_layout = QVBoxLayout(source_group)
        source_row = QHBoxLayout()
        self.source_edit = self._path_edit("尚未選擇來源圖片")
        self.source_button = QPushButton("選擇圖片")
        self.source_button.clicked.connect(self._choose_source)
        source_row.addWidget(self.source_edit, 1)
        source_row.addWidget(self.source_button)
        source_layout.addLayout(source_row)
        self.batch_count_label = QLabel("已選擇 0 / 16 張")
        self.batch_list = QListWidget()
        self.batch_list.setMaximumHeight(150)
        batch_buttons = QHBoxLayout()
        self.batch_up_button = QPushButton("↑ 上移")
        self.batch_down_button = QPushButton("↓ 下移")
        self.batch_remove_button = QPushButton("移除")
        self.batch_up_button.clicked.connect(lambda: self._move_batch_item(-1))
        self.batch_down_button.clicked.connect(lambda: self._move_batch_item(1))
        self.batch_remove_button.clicked.connect(self._remove_batch_item)
        batch_buttons.addWidget(self.batch_count_label)
        batch_buttons.addStretch(1)
        batch_buttons.addWidget(self.batch_up_button)
        batch_buttons.addWidget(self.batch_down_button)
        batch_buttons.addWidget(self.batch_remove_button)
        source_layout.addWidget(self.batch_list)
        source_layout.addLayout(batch_buttons)
        layout.addWidget(source_group)

        platform_group = QGroupBox("輸出平台")
        platform_layout = QFormLayout(platform_group)
        self.platform_combo = QComboBox()
        for label, value in PLATFORMS:
            self.platform_combo.addItem(label, value)
        self.platform_combo.currentIndexChanged.connect(self._update_banner_state)
        platform_layout.addRow("平台：", self.platform_combo)
        layout.addWidget(platform_group)

        self.line_cover_group = self._build_cover_group("LINE 封面圖片", "line")
        self.wechat_cover_group = self._build_cover_group("WeChat 封面圖片", "wechat")
        layout.addWidget(self.line_cover_group)
        layout.addWidget(self.wechat_cover_group)

        self.grid_group = QGroupBox("圖片切割設定")
        grid_layout = QHBoxLayout(self.grid_group)
        self.rows_spin = QSpinBox()
        self.columns_spin = QSpinBox()
        for spin in (self.rows_spin, self.columns_spin):
            spin.setRange(1, 99)
            spin.setValue(4)
            spin.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        grid_layout.addWidget(QLabel("行數："))
        grid_layout.addWidget(self.rows_spin)
        grid_layout.addSpacing(24)
        grid_layout.addWidget(QLabel("列數："))
        grid_layout.addWidget(self.columns_spin)
        grid_layout.addStretch(1)
        layout.addWidget(self.grid_group)

        self.banner_group = QGroupBox("微信 Banner")
        banner_layout = QHBoxLayout(self.banner_group)
        self.banner_edit = self._path_edit("未選擇時沿用既有無 Banner 行為")
        self.banner_button = QPushButton("選擇")
        self.banner_clear_button = QPushButton("清除")
        self.banner_button.clicked.connect(self._choose_banner)
        self.banner_clear_button.clicked.connect(self._clear_banner)
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

        self.background_group = QGroupBox("純色背景轉透明")
        background_layout = QFormLayout(self.background_group)
        self.remove_background_checkbox = QCheckBox("去除純色背景")
        self.remove_background_checkbox.setToolTip(
            "只移除與畫布外部連通的指定背景色，適合固定純色背景的貼圖合集；不是 AI 去背。"
        )
        self.auto_background_checkbox = QCheckBox("自動偵測背景色（推薦）")
        self.auto_background_checkbox.setChecked(True)
        self.background_color_label = QLabel("#FFF8EC")
        self.background_color_button = QPushButton("選擇顏色")
        color_row = QHBoxLayout()
        color_row.addWidget(self.background_color_label)
        color_row.addWidget(self.background_color_button)
        color_row.addStretch(1)
        color_widget = QWidget()
        color_widget.setLayout(color_row)
        self.background_tolerance_spin = QSpinBox()
        self.background_tolerance_spin.setRange(0, 30)
        self.background_tolerance_spin.setValue(3)
        self.background_tolerance_spin.setToolTip(
            "數值越高，越容易移除近似背景色，但也可能誤刪淺色細節。"
            "純色 PNG 建議 3～5；JPEG 或有壓縮色差的圖片可使用 10～15。"
        )
        background_layout.addRow(self.remove_background_checkbox)
        background_layout.addRow(self.auto_background_checkbox)
        background_layout.addRow("背景色：", color_widget)
        background_layout.addRow("容差：", self.background_tolerance_spin)
        self.remove_background_checkbox.stateChanged.connect(self._update_background_state)
        self.auto_background_checkbox.stateChanged.connect(self._update_background_state)
        self.background_color_button.clicked.connect(self._choose_background_color)
        layout.addWidget(self.background_group)

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

    def _t(self, key: str, **kwargs: object) -> str:
        return tr(self.language, key, **kwargs)

    @Slot()
    def _change_language(self) -> None:
        self.language = normalize_language(str(self.language_combo.currentData() or "en"))
        self.settings.setValue("language", self.language)
        self.settings.sync()
        self._retranslate_ui()

    def _retranslate_ui(self) -> None:
        self.setWindowTitle(self._t("window.title", version=__version__))
        self.language_label.setText(self._t("language.label"))
        for widget_type in (QLabel, QPushButton, QCheckBox):
            for widget in self.findChildren(widget_type):
                if widget is self.language_label:
                    continue
                text = widget.property("text")
                if isinstance(text, str):
                    widget.setProperty("text", translate_visible_text(self.language, text))
                if widget.toolTip():
                    widget.setToolTip(translate_visible_text(self.language, widget.toolTip()))
        for group in self.findChildren(QGroupBox):
            group.setTitle(translate_visible_text(self.language, group.title()))
            if group.toolTip():
                group.setToolTip(translate_visible_text(self.language, group.toolTip()))
        for edit in self.findChildren(QLineEdit):
            edit.setPlaceholderText(translate_visible_text(self.language, edit.placeholderText()))
        for combo in self.findChildren(QComboBox):
            if combo is self.language_combo:
                continue
            current = combo.currentData()
            for index in range(combo.count()):
                combo.setItemText(
                    index,
                    translate_visible_text(self.language, combo.itemText(index)),
                )
            combo.setCurrentIndex(combo.findData(current))
        self.batch_count_label.setText(self._t("batch.count", count=len(self._batch_source_paths)))
        self.source_button.setText(
            self._t("button.choose_16")
            if self.input_mode_combo.currentData() == "wechat_batch"
            else self._t("button.choose_image")
        )
        if self._last_progress_message:
            self.status_label.setText(translate_progress(self.language, self._last_progress_message))
        else:
            self.status_label.setText(translate_visible_text(self.language, self.status_label.text()))
        if self._last_result is not None:
            self.result_text.setPlainText(result_summary(self._last_result, self.language))
        elif self._last_error is not None:
            self.result_text.setPlainText(
                translate_user_message(self.language, user_error_message(self._last_error, self.language))
            )
        self._update_cover_state()
        self._refresh_detected_background_color()

    def _build_cover_group(self, title: str, key: str) -> QGroupBox:
        group = QGroupBox(title)
        layout = QHBoxLayout(group)
        mode = QComboBox()
        mode.addItem("自動產生", "auto")
        mode.addItem("自選圖片", "custom")
        edit = self._path_edit("自動產生")
        button = QPushButton("選擇")
        setattr(self, f"{key}_cover_mode_combo", mode)
        setattr(self, f"{key}_cover_edit", edit)
        setattr(self, f"{key}_cover_button", button)
        mode.currentIndexChanged.connect(self._update_cover_state)
        button.clicked.connect(lambda _checked=False, name=key: self._choose_cover(name))
        layout.addWidget(mode)
        layout.addWidget(edit, 1)
        layout.addWidget(button)
        return group

    @staticmethod
    def _path_edit(placeholder: str) -> QLineEdit:
        edit = QLineEdit()
        edit.setReadOnly(True)
        edit.setPlaceholderText(placeholder)
        edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return edit

    def _restore_settings(self) -> None:
        input_mode = str(self.settings.value("input_mode", "sheet"))
        mode_index = self.input_mode_combo.findData(input_mode)
        self.input_mode_combo.setCurrentIndex(mode_index if mode_index >= 0 else 0)
        platform = str(self.settings.value("platform", "line"))
        index = self.platform_combo.findData(platform)
        self.platform_combo.setCurrentIndex(index if index >= 0 else 0)
        self.remove_background_checkbox.setChecked(
            cast(bool, self.settings.value("remove_solid_background", False, type=bool))
        )
        self.auto_background_checkbox.setChecked(
            cast(bool, self.settings.value("auto_detect_solid_background", True, type=bool))
        )
        self.background_tolerance_spin.setValue(
            int(str(self.settings.value("solid_background_tolerance", 3)))
        )
        self._solid_background_color = str(self.settings.value("solid_background_color", "#FFF8EC")).upper()
        self.background_color_label.setText(self._solid_background_color)
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
        if self.input_mode_combo.currentData() == "wechat_batch":
            paths, _ = QFileDialog.getOpenFileNames(
                self,
                self._t("dialog.choose_batch"),
                self._dialog_directory("last_source_directory"),
                self._t("dialog.images"),
            )
            if paths:
                self._apply_batch_source_paths([Path(path) for path in paths])
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            self._t("dialog.choose_sheet"),
            self._dialog_directory("last_source_directory"),
            self._t("dialog.images_webp"),
        )
        if path:
            self._apply_source_path(Path(path))

    def _apply_batch_source_paths(self, paths: list[Path]) -> None:
        self._batch_source_paths = list(paths)
        self.batch_list.clear()
        for index, path in enumerate(paths, 1):
            self.batch_list.addItem(f"{index:02d}  {path.name}")
        self.batch_count_label.setText(self._t("batch.count", count=len(paths)))
        self.source_edit.setText(str(paths[0]) if paths else "")
        if paths:
            self.settings.setValue("last_source_directory", str(paths[0].parent))
            if not self._output_user_selected:
                self.output_edit.setText(str(paths[0].parent))
        self._refresh_detected_background_color()
        self._refresh_start_enabled()

    def _move_batch_item(self, offset: int) -> None:
        row = self.batch_list.currentRow()
        target = row + offset
        if row < 0 or target < 0 or target >= len(self._batch_source_paths):
            return
        self._batch_source_paths[row], self._batch_source_paths[target] = (
            self._batch_source_paths[target],
            self._batch_source_paths[row],
        )
        self._apply_batch_source_paths(self._batch_source_paths.copy())
        self.batch_list.setCurrentRow(target)

    @Slot()
    def _remove_batch_item(self) -> None:
        row = self.batch_list.currentRow()
        if row < 0 or row >= len(self._batch_source_paths):
            return
        del self._batch_source_paths[row]
        self._apply_batch_source_paths(self._batch_source_paths.copy())
        if self._batch_source_paths:
            self.batch_list.setCurrentRow(min(row, len(self._batch_source_paths) - 1))

    @Slot()
    def _update_input_mode(self) -> None:
        if not hasattr(self, "batch_list"):
            return
        mode = str(self.input_mode_combo.currentData() or "sheet")
        changed = mode != self._last_input_mode
        self._last_input_mode = mode
        batch = mode == "wechat_batch"
        for widget in (
            self.batch_list,
            self.batch_count_label,
            self.batch_up_button,
            self.batch_down_button,
            self.batch_remove_button,
        ):
            widget.setVisible(batch)
        self.source_edit.setVisible(not batch)
        self.source_button.setText(self._t("button.choose_16") if batch else self._t("button.choose_image"))
        self.rows_spin.setEnabled(not batch and self._thread is None)
        self.columns_spin.setEnabled(not batch and self._thread is None)
        if batch:
            index = self.platform_combo.findData("wechat")
            self.platform_combo.setCurrentIndex(index)
            self.platform_combo.setEnabled(False)
            self.source_edit.setText(str(self._batch_source_paths[0]) if self._batch_source_paths else "")
            if not self._batch_source_paths and not self._output_user_selected:
                self.output_edit.clear()
        else:
            self.platform_combo.setEnabled(self._thread is None)
            if changed:
                self._batch_source_paths = []
                self.batch_list.clear()
                self.batch_count_label.setText(self._t("batch.count", count=0))
                self.source_edit.clear()
                if not self._output_user_selected:
                    self.output_edit.clear()
        self._update_banner_state()
        self._update_cover_state()
        self._refresh_start_enabled()

    def _apply_source_path(self, source: Path) -> None:
        """Apply a selected source and refresh only an automatic output suggestion."""
        self.source_edit.setText(str(source))
        self.settings.setValue("last_source_directory", str(source.parent))
        if not self._output_user_selected:
            self.output_edit.setText(str(suggested_output_directory(source)))
        self._refresh_detected_background_color()
        self._refresh_start_enabled()

    @Slot()
    def _choose_background_color(self) -> None:
        selected = QColorDialog.getColor(parent=self, title=self._t("dialog.choose_background"))
        if selected.isValid():
            self._solid_background_color = selected.name().upper()
            self.background_color_label.setText(self._solid_background_color)

    def _refresh_detected_background_color(self) -> None:
        if not (
            self.remove_background_checkbox.isChecked()
            and self.auto_background_checkbox.isChecked()
            and self.source_edit.text()
        ):
            self.background_color_label.setText(self._solid_background_color)
            return
        try:
            detected = detect_solid_background_color(load_image(Path(self.source_edit.text()), "貼圖合集"))
        except Exception:  # UI 預覽失敗不阻止稍後的表單錯誤處理
            logger.exception("Unable to preview the detected solid background color")
            detected = None
        if detected is None:
            self.background_color_label.setText(
                self._t("background.fallback", color=self._solid_background_color)
            )
        else:
            self.background_color_label.setText(self._t("background.detected", color=color_to_hex(detected)))

    @Slot()
    def _update_background_state(self) -> None:
        enabled = self.remove_background_checkbox.isChecked() and self._thread is None
        automatic = self.auto_background_checkbox.isChecked()
        self.auto_background_checkbox.setEnabled(enabled)
        self.background_color_button.setEnabled(enabled and not automatic)
        self.background_tolerance_spin.setEnabled(enabled)
        self._refresh_detected_background_color()

    @Slot()
    def _choose_cover(self, key: str) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self._t("dialog.choose_cover"),
            self._dialog_directory("last_source_directory"),
            self._t("dialog.images"),
        )
        if path:
            getattr(self, f"{key}_cover_edit").setText(path)
            self._refresh_start_enabled()

    @Slot()
    def _update_cover_state(self) -> None:
        if not hasattr(self, "line_cover_group"):
            return
        platform = str(self.platform_combo.currentData())
        processing = self._thread is not None
        for key, enabled in (
            ("line", platform in {"line", "both"}),
            ("wechat", platform in {"wechat", "both"}),
        ):
            group = getattr(self, f"{key}_cover_group")
            mode = getattr(self, f"{key}_cover_mode_combo")
            edit = getattr(self, f"{key}_cover_edit")
            button = getattr(self, f"{key}_cover_button")
            group.setEnabled(enabled and not processing)
            custom = mode.currentData() == "custom"
            button.setEnabled(enabled and custom and not processing)
            edit.setPlaceholderText(
                self._t("placeholder.cover.choose") if custom else self._t("placeholder.cover.auto")
            )
            if not custom:
                edit.clear()
        self._refresh_start_enabled()

    @Slot()
    def _choose_banner(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self._t("dialog.choose_banner"),
            self._dialog_directory("last_source_directory"),
            self._t("dialog.images_webp"),
        )
        if path:
            self.banner_edit.setText(path)
            self._refresh_start_enabled()

    @Slot()
    def _clear_banner(self) -> None:
        self.banner_edit.clear()
        self._refresh_start_enabled()

    @Slot()
    def _choose_output(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, self._t("dialog.choose_output"), self._dialog_directory("last_manual_output_directory")
        )
        if path:
            self.output_edit.setText(path)
            self._output_user_selected = True
            self.settings.setValue("output_directory_mode", "manual")
            self.settings.setValue("last_manual_output_directory", path)
            self.settings.sync()
            self._refresh_start_enabled()

    @Slot()
    def _update_banner_state(self) -> None:
        enabled = banner_enabled(str(self.platform_combo.currentData())) and self._thread is None
        self.banner_group.setEnabled(enabled)
        self._update_cover_state()
        self._refresh_start_enabled()

    def _form_data(self) -> DesktopFormData:
        return DesktopFormData(
            source_path=self.source_edit.text(),
            input_mode=str(self.input_mode_combo.currentData() or "sheet"),
            batch_source_paths=tuple(str(path) for path in self._batch_source_paths),
            platform=str(self.platform_combo.currentData() or ""),
            rows=self.rows_spin.value(),
            columns=self.columns_spin.value(),
            banner_path=self.banner_edit.text(),
            output_directory=self.output_edit.text(),
            line_cover_path=self.line_cover_edit.text(),
            wechat_cover_path=self.wechat_cover_edit.text(),
            trim_enabled=self.trim_checkbox.isChecked(),
            create_preview=self.preview_checkbox.isChecked(),
            create_zip=self.zip_checkbox.isChecked(),
            remove_solid_background=self.remove_background_checkbox.isChecked(),
            auto_detect_solid_background=self.auto_background_checkbox.isChecked(),
            solid_background_color=self._solid_background_color,
            solid_background_tolerance=self.background_tolerance_spin.value(),
        )

    def _refresh_start_enabled(self) -> None:
        if not hasattr(self, "start_button"):
            return
        batch = self.input_mode_combo.currentData() == "wechat_batch"
        ready = bool(self.source_edit.text() and self.platform_combo.currentData())
        if batch:
            ready = bool(self._batch_source_paths) and bool(self.banner_edit.text())
        if self.line_cover_mode_combo.currentData() == "custom" and self.platform_combo.currentData() in {
            "line",
            "both",
        }:
            ready = ready and bool(self.line_cover_edit.text())
        if self.wechat_cover_mode_combo.currentData() == "custom" and self.platform_combo.currentData() in {
            "wechat",
            "both",
        }:
            ready = ready and bool(self.wechat_cover_edit.text())
        self.start_button.setEnabled(ready and self._thread is None)

    @Slot()
    def _start_processing(self) -> None:
        try:
            source, options = self.controller.build_request(self._form_data())
        except DesktopValidationError as exc:
            QMessageBox.warning(
                self, self._t("dialog.input_incomplete"), translate_user_message(self.language, str(exc))
            )
            return
        self.settings.setValue("input_mode", options.input_mode)
        self.settings.setValue("platform", options.platform)
        self.progress_bar.setValue(0)
        self._last_progress_message = ""
        self.status_label.setText(self._t("status.starting"))
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
            self.input_mode_combo,
            self.batch_up_button,
            self.batch_down_button,
            self.batch_remove_button,
            self.platform_combo,
            self.rows_spin,
            self.columns_spin,
            self.banner_button,
            self.banner_clear_button,
            self.output_button,
            self.preview_checkbox,
            self.zip_checkbox,
            self.remove_background_checkbox,
            self.auto_background_checkbox,
            self.background_color_button,
            self.background_tolerance_spin,
            self.line_cover_mode_combo,
            self.line_cover_button,
            self.wechat_cover_mode_combo,
            self.wechat_cover_button,
        ):
            widget.setEnabled(not processing)
        self.start_button.setEnabled(not processing and bool(self.source_edit.text()))
        if not processing:
            self._update_input_mode()
            self._update_banner_state()
            self._update_cover_state()
            self._update_background_state()

    @Slot(int, str)
    def _on_progress(self, percent: int, message: str) -> None:
        self.progress_bar.setValue(max(0, min(100, percent)))
        self._last_progress_message = message
        self.status_label.setText(translate_progress(self.language, message))

    @Slot(object)
    def _on_completed(self, result: ProcessingResult) -> None:
        self._last_result = result
        self._last_error = None
        self.progress_bar.setValue(100)
        self.status_label.setText(self._t("status.completed"))
        self.result_text.setPlainText(result_summary(result, self.language))
        self.open_output_button.setEnabled(True)
        QMessageBox.information(self, self._t("dialog.completed.title"), self._t("dialog.completed.body"))

    @Slot(object)
    def _on_failed(self, error: Exception) -> None:
        self._last_result = None
        self._last_error = error
        self.status_label.setText(self._t("status.failed"))
        message = translate_user_message(self.language, user_error_message(error, self.language))
        self.result_text.setPlainText(message)
        QMessageBox.critical(self, self._t("dialog.failed"), message)

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
            open_in_file_manager(output_directory_from_root(Path(self.output_edit.text())))
        except OSError as exc:
            logger.exception("Unable to open output directory")
            QMessageBox.warning(self, self._t("dialog.output_failed"), str(exc))

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._thread is not None:
            QMessageBox.information(self, self._t("dialog.processing"), self._t("dialog.processing_wait"))
            event.ignore()
            return
        self.settings.setValue("input_mode", self.input_mode_combo.currentData())
        self.settings.setValue("platform", self.platform_combo.currentData())
        self.settings.setValue("remove_solid_background", self.remove_background_checkbox.isChecked())
        self.settings.setValue("auto_detect_solid_background", self.auto_background_checkbox.isChecked())
        self.settings.setValue("solid_background_color", self._solid_background_color)
        self.settings.setValue("solid_background_tolerance", self.background_tolerance_spin.value())
        self.settings.setValue("language", self.language)
        self.settings.setValue("window_geometry", self.saveGeometry())
        self.settings.sync()
        super().closeEvent(event)
