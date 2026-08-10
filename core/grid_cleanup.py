"""Conservative cleanup for fragments that cross fixed grid boundaries."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Literal, cast

from PIL import Image

Edge = Literal["top", "right", "bottom", "left"]


@dataclass
class _Component:
    identifier: int
    pixels: list[int]
    bbox: tuple[int, int, int, int]
    contacts: dict[Edge, int]

    @property
    def area(self) -> int:
        return len(self.pixels)


@dataclass
class _CellAnalysis:
    image: Image.Image
    labels: list[int]
    components: list[_Component]
    primary_identifier: int | None


def _analyze(source: Image.Image) -> _CellAnalysis:
    image = source.convert("RGBA")
    width, height = image.size
    values = image.getchannel("A").tobytes()
    labels = [-1] * (width * height)
    components: list[_Component] = []

    for start, opacity in enumerate(values):
        if opacity == 0 or labels[start] != -1:
            continue
        identifier = len(components)
        labels[start] = identifier
        queue = deque([start])
        pixels: list[int] = []
        left = right = start % width
        top = bottom = start // width
        contacts: dict[Edge, int] = {"top": 0, "right": 0, "bottom": 0, "left": 0}
        while queue:
            index = queue.popleft()
            pixels.append(index)
            x, y = index % width, index // width
            left, right = min(left, x), max(right, x)
            top, bottom = min(top, y), max(bottom, y)
            if y == 0:
                contacts["top"] += 1
            if x == width - 1:
                contacts["right"] += 1
            if y == height - 1:
                contacts["bottom"] += 1
            if x == 0:
                contacts["left"] += 1
            for ny in range(max(0, y - 1), min(height, y + 2)):
                for nx in range(max(0, x - 1), min(width, x + 2)):
                    neighbor = ny * width + nx
                    if values[neighbor] and labels[neighbor] == -1:
                        labels[neighbor] = identifier
                        queue.append(neighbor)
        components.append(
            _Component(identifier, pixels, (left, top, right + 1, bottom + 1), contacts)
        )

    primary = max(components, key=lambda component: component.area).identifier if components else None
    return _CellAnalysis(image, labels, components, primary)


def _penetration(component: _Component, edge: Edge, size: tuple[int, int]) -> int:
    left, top, right, bottom = component.bbox
    width, height = size
    if edge == "top":
        return bottom
    if edge == "right":
        return width - left
    if edge == "bottom":
        return height - top
    return right


def _is_likely_fragment(
    minor: _Component,
    major: _Component,
    edge: Edge,
    cell: _CellAnalysis,
    overlap: int,
) -> bool:
    """Use several conservative signals; ambiguity always keeps the component."""
    width, height = cell.image.size
    cell_area = width * height
    edge_length = height if edge in {"left", "right"} else width
    depth_limit = width if edge in {"left", "right"} else height
    relative_area = minor.area / major.area
    cell_area_ratio = minor.area / cell_area
    depth_ratio = _penetration(minor, edge, cell.image.size) / depth_limit
    contact = minor.contacts[edge]

    if (
        major.area <= minor.area
        or relative_area > 0.35
        or cell_area_ratio > 0.04
        or depth_ratio > 0.18
        or contact == 0
        or overlap < max(1, round(min(contact, edge_length) * 0.15))
    ):
        return False
    if minor.identifier == cell.primary_identifier and cell_area_ratio >= 0.01:
        return False

    score = 0
    score += 2 if relative_area <= 0.20 else 1
    score += 2 if depth_ratio <= 0.10 else 1
    score += 2 if cell_area_ratio <= 0.015 else 1
    if overlap / max(1, contact) >= 0.40:
        score += 1
    if sum(value > 0 for value in minor.contacts.values()) >= 2:
        score += 1
    return score >= 4


def _record_pair(
    pairs: dict[tuple[int, int], int], first_identifier: int, second_identifier: int
) -> None:
    if first_identifier >= 0 and second_identifier >= 0:
        key = (first_identifier, second_identifier)
        pairs[key] = pairs.get(key, 0) + 1


def _compare_neighbors(
    first: _CellAnalysis,
    second: _CellAnalysis,
    first_edge: Edge,
    second_edge: Edge,
) -> tuple[set[int], set[int]]:
    first_width, first_height = first.image.size
    second_width, second_height = second.image.size
    pairs: dict[tuple[int, int], int] = {}
    if first_edge in {"left", "right"}:
        first_x = first_width - 1 if first_edge == "right" else 0
        second_x = second_width - 1 if second_edge == "right" else 0
        for y in range(min(first_height, second_height)):
            _record_pair(
                pairs,
                first.labels[y * first_width + first_x],
                second.labels[y * second_width + second_x],
            )
    else:
        first_y = first_height - 1 if first_edge == "bottom" else 0
        second_y = second_height - 1 if second_edge == "bottom" else 0
        for x in range(min(first_width, second_width)):
            _record_pair(
                pairs,
                first.labels[first_y * first_width + x],
                second.labels[second_y * second_width + x],
            )

    remove_first: set[int] = set()
    remove_second: set[int] = set()
    for (first_identifier, second_identifier), overlap in pairs.items():
        first_component = first.components[first_identifier]
        second_component = second.components[second_identifier]
        if first_component.area < second_component.area:
            if _is_likely_fragment(
                first_component, second_component, first_edge, first, overlap
            ):
                remove_first.add(first_identifier)
        elif second_component.area < first_component.area and _is_likely_fragment(
            second_component, first_component, second_edge, second, overlap
        ):
            remove_second.add(second_identifier)
    return remove_first, remove_second


def clean_grid_edge_fragments(
    cells: list[Image.Image], rows: int = 4, columns: int = 4
) -> list[Image.Image]:
    """Remove only strongly supported neighboring-cell fragments from prepared cells."""
    if len(cells) != rows * columns:
        raise ValueError("格子數量與指定列數、行數不一致。")
    analyses = [_analyze(cell) for cell in cells]
    removals: list[set[int]] = [set() for _ in cells]

    for row in range(rows):
        for column in range(columns - 1):
            first_index = row * columns + column
            second_index = first_index + 1
            first_remove, second_remove = _compare_neighbors(
                analyses[first_index], analyses[second_index], "right", "left"
            )
            removals[first_index].update(first_remove)
            removals[second_index].update(second_remove)
    for row in range(rows - 1):
        for column in range(columns):
            first_index = row * columns + column
            second_index = first_index + columns
            first_remove, second_remove = _compare_neighbors(
                analyses[first_index], analyses[second_index], "bottom", "top"
            )
            removals[first_index].update(first_remove)
            removals[second_index].update(second_remove)

    cleaned: list[Image.Image] = []
    for analysis, identifiers in zip(analyses, removals, strict=True):
        if identifiers:
            pixels = analysis.image.load()
            if pixels is None:
                raise ValueError("無法存取圖片像素。")
            width = analysis.image.width
            for identifier in identifiers:
                for index in analysis.components[identifier].pixels:
                    x, y = index % width, index // width
                    red, green, blue, _alpha = cast(
                        tuple[int, int, int, int], pixels[x, y]
                    )
                    pixels[x, y] = (red, green, blue, 0)
        cleaned.append(analysis.image)
    return cleaned
