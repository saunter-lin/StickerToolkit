from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from core.config import LINE_CONFIG
from core.images import build_shared_stickers, split_grid
from sticker_toolkit.core import ProcessingOptions, clean_grid_edge_fragments
from sticker_toolkit.services import StickerService


def empty_cells(size: tuple[int, int] = (100, 100)) -> list[Image.Image]:
    return [Image.new("RGBA", size, (0, 0, 0, 0)) for _ in range(16)]


def opaque_count(image: Image.Image, color: tuple[int, int, int]) -> int:
    return sum(
        alpha > 0 and (red, green, blue) == color
        for red, green, blue, alpha in image.convert("RGBA").get_flattened_data()
    )


class GridEdgeCleanupTests(unittest.TestCase):
    def test_top_neighbor_text_fragment_is_removed(self) -> None:
        cells = empty_cells()
        color = (180, 80, 30)
        ImageDraw.Draw(cells[0]).rectangle((30, 60, 69, 99), fill=(*color, 255))
        ImageDraw.Draw(cells[4]).rectangle((30, 0, 69, 8), fill=(*color, 255))
        ImageDraw.Draw(cells[4]).ellipse((25, 30, 75, 85), fill=(40, 90, 160, 255))
        cleaned = clean_grid_edge_fragments(cells)
        self.assertEqual(opaque_count(cleaned[4], color), 0)
        self.assertGreater(opaque_count(cleaned[0], color), 0)

    def test_bottom_neighbor_character_fragment_is_removed(self) -> None:
        cells = empty_cells()
        color = (80, 90, 100)
        ImageDraw.Draw(cells[8]).ellipse((35, 0, 65, 45), fill=(*color, 255))
        ImageDraw.Draw(cells[4]).rectangle((40, 92, 60, 99), fill=(*color, 255))
        ImageDraw.Draw(cells[4]).ellipse((25, 20, 75, 75), fill=(40, 90, 160, 255))
        cleaned = clean_grid_edge_fragments(cells)
        self.assertEqual(opaque_count(cleaned[4], color), 0)
        self.assertGreater(opaque_count(cleaned[8], color), 0)

    def test_left_and_right_half_character_fragments_are_removed(self) -> None:
        cells = empty_cells()
        color = (150, 70, 20)
        ImageDraw.Draw(cells[1]).rectangle((45, 25, 99, 70), fill=(*color, 255))
        ImageDraw.Draw(cells[2]).rectangle((0, 30, 8, 65), fill=(*color, 255))
        ImageDraw.Draw(cells[6]).rectangle((0, 25, 54, 70), fill=(*color, 255))
        ImageDraw.Draw(cells[5]).rectangle((91, 30, 99, 65), fill=(*color, 255))
        ImageDraw.Draw(cells[2]).ellipse((25, 25, 75, 80), fill=(40, 90, 160, 255))
        ImageDraw.Draw(cells[5]).ellipse((25, 25, 75, 80), fill=(40, 90, 160, 255))
        cleaned = clean_grid_edge_fragments(cells)
        self.assertEqual(opaque_count(cleaned[2], color), 0)
        self.assertEqual(opaque_count(cleaned[5], color), 0)

    def test_complete_text_near_edge_is_preserved(self) -> None:
        cells = empty_cells()
        color = (170, 80, 20)
        ImageDraw.Draw(cells[0]).rectangle((2, 20, 22, 75), fill=(*color, 255))
        before = opaque_count(cells[0], color)
        cleaned = clean_grid_edge_fragments(cells)
        self.assertEqual(opaque_count(cleaned[0], color), before)

    def test_connected_ear_or_tail_at_edge_is_preserved(self) -> None:
        cells = empty_cells()
        color = (70, 70, 75)
        draw = ImageDraw.Draw(cells[0])
        draw.ellipse((20, 20, 80, 85), fill=(*color, 255))
        draw.polygon(((20, 35), (0, 8), (35, 30)), fill=(*color, 255))
        before = opaque_count(cells[0], color)
        cleaned = clean_grid_edge_fragments(cells)
        self.assertEqual(opaque_count(cleaned[0], color), before)

    def test_independent_heart_and_punctuation_are_preserved(self) -> None:
        cells = empty_cells()
        draw = ImageDraw.Draw(cells[0])
        draw.ellipse((45, 45, 75, 80), fill=(60, 60, 60, 255))
        draw.polygon(((8, 20), (14, 14), (20, 20), (14, 30)), fill=(230, 40, 70, 255))
        draw.rectangle((86, 35, 90, 58), fill=(20, 20, 20, 255))
        before = cells[0].tobytes()
        cleaned = clean_grid_edge_fragments(cells)
        self.assertEqual(cleaned[0].tobytes(), before)

    def test_clean_sheet_does_not_regress(self) -> None:
        sheet = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
        draw = ImageDraw.Draw(sheet)
        for index in range(16):
            row, column = divmod(index, 4)
            left, top = column * 100, row * 100
            draw.ellipse((left + 18, top + 12, left + 82, top + 86), fill=(30, 80, 160, 255))
            draw.rectangle((left + 5, top + 30, left + 14, top + 65), fill=(150, 70, 20, 255))
        cells = split_grid(sheet)
        cleaned = clean_grid_edge_fragments(cells)
        self.assertEqual([cell.tobytes() for cell in cleaned], [cell.tobytes() for cell in cells])

    def test_relative_thresholds_support_other_divisible_sizes(self) -> None:
        sheet = Image.new("RGBA", (404, 356), "white")
        draw = ImageDraw.Draw(sheet)
        cell_width, cell_height = 101, 89
        for index in range(16):
            row, column = divmod(index, 4)
            left, top = column * cell_width, row * cell_height
            draw.ellipse(
                (left + 18, top + 12, left + cell_width - 18, top + cell_height - 12),
                fill=(30, 90, 160, 255),
            )
        stickers = build_shared_stickers(
            sheet, LINE_CONFIG.sticker_size, LINE_CONFIG.sticker_padding
        )
        self.assertEqual(len(stickers), 16)

    def test_service_removes_cross_cell_fragment_before_export(self) -> None:
        with tempfile.TemporaryDirectory() as folder_name:
            root = Path(folder_name)
            source = root / "AI 組圖.png"
            sheet = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
            draw = ImageDraw.Draw(sheet)
            for index in range(16):
                row, column = divmod(index, 4)
                left, top = column * 100, row * 100
                draw.ellipse(
                    (left + 30, top + 30, left + 70, top + 75),
                    fill=(30, 90, 160, 255),
                )
            contamination = (190, 70, 20)
            draw.rectangle((55, 8, 107, 26), fill=(*contamination, 255))
            sheet.save(source)
            result = StickerService().process(
                source,
                ProcessingOptions(
                    platform="both",
                    output_directory=root / "輸出 result",
                    create_preview=True,
                ),
            )
            for platform in ("line", "wechat"):
                exported = result.for_platform(platform)
                with Image.open(exported.sticker_files[1]) as sticker:
                    self.assertEqual(opaque_count(sticker, contamination), 0)
                self.assertTrue(exported.preview_file and exported.preview_file.is_file())
                self.assertTrue(exported.zip_file and exported.zip_file.is_file())


if __name__ == "__main__":
    unittest.main()
