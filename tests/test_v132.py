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
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from core.config import LINE_CONFIG
from core.images import build_shared_stickers
from core.paths import ProjectPaths
from exporters.line import export_line
from exporters.wechat import export_wechat
from sticker_toolkit.core import ProcessingOptions, StickerToolkitError
from sticker_toolkit.services import StickerService
from sticker_toolkit.ui.desktop.main_window import MainWindow
from sticker_toolkit.ui.desktop.view_model import (
    DesktopFormData,
    DesktopValidationError,
    build_processing_options,
)

CREAM = (255, 248, 236)


def make_single(path: Path, color: tuple[int, int, int], *, jpeg: bool = False) -> None:
    image = Image.new("RGB", (120, 90), CREAM)
    ImageDraw.Draw(image).rectangle((30, 15, 89, 74), fill=color)
    image.save(path, quality=95 if jpeg else None)


def make_sheet() -> Image.Image:
    sheet = Image.new("RGBA", (400, 400), "white")
    draw = ImageDraw.Draw(sheet)
    for index in range(16):
        row, column = divmod(index, 4)
        x, y = column * 100, row * 100
        draw.ellipse((x + 20, y + 20, x + 80, y + 80), fill=(20, 50 + index * 8, 180, 255))
    return sheet


class WeChatBatchServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.banner = self.root / "taiwan_phrase.png"
        Image.new("RGB", (750, 400), "navy").save(self.banner)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def sources(self, suffixes: tuple[str, ...] | None = None) -> tuple[Path, ...]:
        suffixes = suffixes or (".png",) * 16
        result: list[Path] = []
        for index, suffix in enumerate(suffixes, 1):
            path = self.root / f"source_{index:02d}{suffix}"
            make_single(path, (20 + index * 8, 60, 160), jpeg=suffix.lower() in {".jpg", ".jpeg"})
            result.append(path)
        return tuple(result)

    def process(self, sources: tuple[Path, ...], **changes: object):
        values: dict[str, object] = {
            "input_mode": "wechat_batch",
            "batch_source_paths": sources,
            "platform": "wechat",
            "banner_path": self.banner,
            "output_directory": self.root / "output",
            "remove_solid_background": True,
            "solid_background_tolerance": 15,
        }
        values.update(changes)
        return StickerService().process(sources[0], ProcessingOptions(**values))

    def test_png_jpeg_and_mixed_batches_export_in_order(self) -> None:
        cases = (
            ("png", (".png",) * 16),
            ("jpeg", (".jpg",) * 16),
            ("mixed", tuple(".png" if index % 2 else ".jpg" for index in range(16))),
        )
        for label, suffixes in cases:
            with self.subTest(label=label):
                sources = self.sources(suffixes)
                result = self.process(sources)
                exported = result.for_platform("wechat")
                self.assertEqual(exported.output_directory.name, "taiwan_phrase_wechat_sticker")
                self.assertEqual(
                    [path.name for path in exported.sticker_files], [f"{i:02d}.png" for i in range(1, 17)]
                )
                with Image.open(exported.sticker_files[0]) as first:
                    self.assertEqual(first.getpixel((0, 0))[3], 0)
                    red = first.getpixel((120, 120))[0]
                    self.assertAlmostEqual(red, 28, delta=12)

    def test_batch_failure_identifies_index_filename_and_reason(self) -> None:
        sources = list(self.sources())
        broken = self.root / "broken input.jpg"
        broken.write_bytes(b"not an image")
        sources[4] = broken
        with self.assertRaisesRegex(StickerToolkitError, r"第 05 張.*broken input\.jpg.*處理失敗"):
            self.process(tuple(sources))

    def test_batch_uses_automatic_and_manual_background_settings(self) -> None:
        sources = self.sources()
        automatic = self.process(sources)
        self.assertEqual(Image.open(automatic.for_platform("wechat").sticker_files[0]).getpixel((0, 0))[3], 0)
        manual = self.process(
            sources,
            auto_detect_solid_background=False,
            solid_background_color="#FFF8EC",
            solid_background_tolerance=3,
            output_directory=self.root / "manual",
        )
        self.assertEqual(Image.open(manual.for_platform("wechat").sticker_files[0]).getpixel((0, 0))[3], 0)

    def test_batch_requires_exactly_sixteen_and_banner(self) -> None:
        sources = self.sources()
        for selected in (sources[:15], sources + (sources[0],)):
            with (
                self.subTest(count=len(selected)),
                self.assertRaisesRegex(StickerToolkitError, str(len(selected))),
            ):
                self.process(selected)
        with self.assertRaisesRegex(StickerToolkitError, "Banner"):
            self.process(sources, banner_path=None)

    def test_reordered_sources_control_output_numbering(self) -> None:
        sources = self.sources()
        reordered = (sources[1], sources[0], *sources[2:])
        result = self.process(reordered)
        with Image.open(result.for_platform("wechat").sticker_files[0]) as first:
            self.assertAlmostEqual(first.getpixel((120, 120))[0], 36, delta=4)

    def test_normalize_preserves_aspect_and_safe_margin(self) -> None:
        sources = self.sources()
        result = self.process(sources)
        with Image.open(result.for_platform("wechat").sticker_files[0]) as sticker:
            bbox = sticker.getchannel("A").getbbox()
            self.assertIsNotNone(bbox)
            assert bbox is not None
            self.assertEqual(bbox[2] - bbox[0], bbox[3] - bbox[1])
            self.assertGreater(min(bbox[0], bbox[1]), 0)
            self.assertLess(max(bbox[2], bbox[3]), 240)

    def test_zip_contains_existing_wechat_assets_and_preview(self) -> None:
        result = self.process(self.sources())
        exported = result.for_platform("wechat")
        self.assertTrue(exported.preview_file and exported.preview_file.is_file())
        self.assertTrue(exported.cover_file and exported.cover_file.is_file())
        self.assertTrue(exported.panel_icon_file and exported.panel_icon_file.is_file())
        self.assertTrue(exported.banner_file and exported.banner_file.is_file())
        assert exported.zip_file is not None
        with zipfile.ZipFile(exported.zip_file) as archive:
            self.assertEqual(archive.namelist()[:16], [f"{i:02d}.png" for i in range(1, 17)])
            self.assertIn("cover.png", archive.namelist())
            self.assertIn("panel_icon.png", archive.namelist())
            self.assertIn("banner.png", archive.namelist())


class CustomCoverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.paths = ProjectPaths.from_root(self.root)
        self.paths.output.root.mkdir(parents=True)
        self.stickers = build_shared_stickers(
            make_sheet(), LINE_CONFIG.sticker_size, LINE_CONFIG.sticker_padding
        )
        self.cover = self.root / "custom cover.png"
        Image.new("RGBA", (500, 200), (240, 20, 80, 255)).save(self.cover)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_line_custom_cover_and_automatic_cover(self) -> None:
        export_line(self.stickers, self.paths.output, 1, 1)
        automatic = Image.open(self.paths.output.line_directory / "main.png").getpixel((120, 120))
        export_line(self.stickers, self.paths.output, 1, 1, self.cover)
        custom = Image.open(self.paths.output.line_directory / "main.png")
        self.assertEqual(custom.size, (240, 240))
        self.assertEqual(custom.getpixel((120, 120))[:3], (240, 20, 80))
        self.assertNotEqual(automatic[:3], custom.getpixel((120, 120))[:3])

    def test_wechat_custom_cover_keeps_panel_existing_behavior(self) -> None:
        result = export_wechat(self.stickers, self.paths.output, None, 1, self.cover)
        with Image.open(result.cover_path) as cover:
            self.assertEqual(cover.size, (240, 240))
            self.assertEqual(cover.getpixel((120, 120))[:3], (240, 20, 80))
        with Image.open(result.panel_icon_path) as panel:
            self.assertNotEqual(panel.getpixel((25, 25))[:3], (240, 20, 80))


class BatchDesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        QSettings("StickerToolkit", "StickerToolkit").clear()
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.paths = []
        for index in range(16):
            path = self.root / f"item {index:02d}.png"
            make_single(path, (40 + index, 80, 160))
            self.paths.append(path)
        self.banner = self.root / "batch banner.png"
        Image.new("RGB", (750, 400), "blue").save(self.banner)
        self.window = MainWindow()

    def tearDown(self) -> None:
        with patch.object(QMessageBox, "information"):
            self.window.close()
        self.temp.cleanup()

    def test_mode_count_and_move_update_form_order(self) -> None:
        self.window.input_mode_combo.setCurrentIndex(self.window.input_mode_combo.findData("wechat_batch"))
        self.window._apply_batch_source_paths(self.paths)
        self.window.banner_edit.setText(str(self.banner))
        self.window._refresh_start_enabled()
        self.assertEqual(self.window.batch_count_label.text(), "已選擇 16 / 16 張")
        self.assertTrue(self.window.start_button.isEnabled())
        self.window.batch_list.setCurrentRow(1)
        self.window._move_batch_item(-1)
        self.assertEqual(Path(self.window._form_data().batch_source_paths[0]), self.paths[1])

    def test_batch_output_defaults_to_first_source_parent(self) -> None:
        self.window.input_mode_combo.setCurrentIndex(
            self.window.input_mode_combo.findData("wechat_batch")
        )
        other = self.root / "其他資料夾"
        other.mkdir()
        other_path = other / "different.png"
        make_single(other_path, (80, 90, 160))
        self.window._apply_batch_source_paths([self.paths[0], other_path])
        self.assertEqual(self.window.output_edit.text(), str(self.paths[0].parent))
        self.window.batch_list.setCurrentRow(1)
        self.window._move_batch_item(-1)
        self.assertEqual(self.window.output_edit.text(), str(other_path.parent))

    def test_remove_fifth_reindexes_without_deleting_original(self) -> None:
        self.window.input_mode_combo.setCurrentIndex(
            self.window.input_mode_combo.findData("wechat_batch")
        )
        extra = self.root / "item 16.png"
        make_single(extra, (100, 80, 160))
        selected = [*self.paths, extra]
        removed = selected[4]
        self.window._apply_batch_source_paths(selected)
        self.window.batch_list.setCurrentRow(4)
        self.window._remove_batch_item()
        self.assertTrue(removed.is_file())
        self.assertEqual(self.window.batch_count_label.text(), "已選擇 16 / 16 張")
        self.assertEqual(self.window._batch_source_paths[4], selected[5])
        item = self.window.batch_list.item(4)
        assert item is not None
        self.assertEqual(item.text(), f"05  {selected[5].name}")

    def test_move_remove_preserve_manual_output_and_form_order(self) -> None:
        self.window.input_mode_combo.setCurrentIndex(
            self.window.input_mode_combo.findData("wechat_batch")
        )
        extra = self.root / "item 16.png"
        make_single(extra, (100, 80, 160))
        expected = [*self.paths, extra]
        self.window._apply_batch_source_paths(expected)
        manual = self.root / "自訂 Batch 輸出"
        manual.mkdir()
        with patch.object(QFileDialog, "getExistingDirectory", return_value=str(manual)):
            self.window._choose_output()

        self.window.batch_list.setCurrentRow(4)
        self.window._remove_batch_item()
        del expected[4]
        self.window.batch_list.setCurrentRow(5)
        self.window._move_batch_item(-1)
        expected[4], expected[5] = expected[5], expected[4]

        self.assertEqual(self.window.output_edit.text(), str(manual))
        self.assertEqual(
            self.window._form_data().batch_source_paths,
            tuple(str(path) for path in expected),
        )

    def test_selecting_seventeen_is_allowed_then_start_validates_count(self) -> None:
        self.window.input_mode_combo.setCurrentIndex(
            self.window.input_mode_combo.findData("wechat_batch")
        )
        extra = self.root / "item 16.png"
        make_single(extra, (100, 80, 160))
        selected = [*self.paths, extra]
        with (
            patch.object(
                QFileDialog,
                "getOpenFileNames",
                return_value=([str(path) for path in selected], "圖片"),
            ),
            patch.object(QMessageBox, "warning") as warning,
        ):
            self.window._choose_source()
            warning.assert_not_called()

        self.assertEqual(self.window.batch_count_label.text(), "已選擇 17 / 16 張")
        self.window.banner_edit.setText(str(self.banner))
        self.window._refresh_start_enabled()
        self.assertTrue(self.window.start_button.isEnabled())
        with patch.object(QMessageBox, "warning") as warning:
            self.window._start_processing()
        self.assertIsNone(self.window._thread)
        self.assertIn("移除", warning.call_args.args[2])

        self.window.batch_list.setCurrentRow(16)
        self.window._remove_batch_item()
        source, options = self.window.controller.build_request(self.window._form_data())
        result = self.window.controller.process(source, options)
        exported = result.for_platform("wechat")
        self.assertEqual(len(exported.sticker_files), 16)
        self.assertEqual(
            [path.name for path in exported.sticker_files], [f"{index:02d}.png" for index in range(1, 17)]
        )

    def test_view_model_blocks_wrong_count_and_builds_custom_covers(self) -> None:
        base = dict(
            source_path=str(self.paths[0]),
            platform="wechat",
            rows=4,
            columns=4,
            banner_path=str(self.banner),
            output_directory=str(self.root / "output"),
            input_mode="wechat_batch",
        )
        with self.assertRaisesRegex(DesktopValidationError, "15"):
            build_processing_options(
                DesktopFormData(**base, batch_source_paths=tuple(map(str, self.paths[:15])))
            )
        extra = self.root / "item 16.png"
        make_single(extra, (100, 80, 160))
        with self.assertRaisesRegex(DesktopValidationError, "17.*移除"):
            build_processing_options(
                DesktopFormData(
                    **base, batch_source_paths=tuple(map(str, [*self.paths, extra]))
                )
            )
        options = build_processing_options(
            DesktopFormData(
                **base,
                batch_source_paths=tuple(map(str, self.paths)),
                wechat_cover_path=str(self.paths[2]),
            )
        )
        self.assertEqual(options.wechat_cover_path, self.paths[2].resolve())


if __name__ == "__main__":
    unittest.main()
