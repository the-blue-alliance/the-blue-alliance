import math
from typing import Mapping, TypedDict, TypeVar
from xml.sax.saxutils import escape

from backend.common.nexus_api.types import (
    Areas,
    Arrows,
    Labels,
    MapElement,
    PitMap,
    Pits,
)

T = TypeVar("T")


class NexusEventDetailsTemplateValues(TypedDict):
    svg_namespace: str
    outer_width: str
    outer_height: str
    view_box: str
    padding: str
    canvas_width: str
    canvas_height: str
    map_translate: str
    footer_top: str
    footer_line_x2: str
    footer_link_y: str
    footer_text_y: str
    event_url: str
    wall_elements: str
    area_elements: str
    pit_elements: str
    label_elements: str
    arrow_elements: str
    logo_element: str


class NexusEventDetailsSVGHelper:
    SVG_NAMESPACE = "http://www.w3.org/2000/svg"
    PADDING = 24
    FOOTER_HEIGHT = 96
    LOGO_SIZE = 54

    @classmethod
    def template_values(
        cls,
        map_data: PitMap,
        nexus_event_code: str,
        highlight_team_keys: set[str] | None = None,
        label_event_keys: dict[str, str] | None = None,
    ) -> NexusEventDetailsTemplateValues:
        size = map_data.get("size")
        if not isinstance(size, dict):
            raise ValueError("Map response is missing size metadata")

        canvas_width = cls._as_number(size.get("x"), name="size.x")
        canvas_height = cls._as_number(size.get("y"), name="size.y")

        walls = cls._dict_or_empty(map_data.get("walls"))
        areas = cls._dict_or_empty(map_data.get("areas"))
        pits = cls._dict_or_empty(map_data.get("pits"))
        labels = cls._dict_or_empty(map_data.get("labels"))
        arrows = cls._dict_or_empty(map_data.get("arrows"))
        normalized_highlight_team_keys = {
            team_key.lower() for team_key in (highlight_team_keys or set())
        }
        normalized_label_event_keys = {
            label.lower(): event_key
            for label, event_key in (label_event_keys or {}).items()
        }

        wall_rects = [cls._get_wall_rect(walls[wall_key]) for wall_key in sorted(walls)]
        thin_wall_rects = [
            rect
            for rect in wall_rects
            if min(rect[2], rect[3]) <= 30 and max(rect[2], rect[3]) <= 400
        ]

        outer_width = canvas_width + cls.PADDING * 2
        outer_height = canvas_height + cls.PADDING * 2 + cls.FOOTER_HEIGHT
        footer_top = canvas_height + cls.PADDING * 2
        logo_x = outer_width - cls.PADDING - cls.LOGO_SIZE
        logo_y = footer_top + (cls.FOOTER_HEIGHT - cls.LOGO_SIZE) / 2

        return {
            "svg_namespace": cls.SVG_NAMESPACE,
            "outer_width": cls._fmt_number(outer_width),
            "outer_height": cls._fmt_number(outer_height),
            "view_box": f"0 0 {cls._fmt_number(outer_width)} {cls._fmt_number(outer_height)}",
            "padding": cls._fmt_number(cls.PADDING),
            "canvas_width": cls._fmt_number(canvas_width),
            "canvas_height": cls._fmt_number(canvas_height),
            "map_translate": f"translate({cls._fmt_number(cls.PADDING)} {cls._fmt_number(cls.PADDING)})",
            "footer_top": cls._fmt_number(footer_top),
            "footer_line_x2": cls._fmt_number(outer_width - cls.PADDING),
            "footer_link_y": cls._fmt_number(footer_top + 30),
            "footer_text_y": cls._fmt_number(footer_top + 58),
            "event_url": f"https://frc.nexus/{nexus_event_code}/pits",
            "wall_elements": "".join(
                cls._render_wall(walls[wall_key]) for wall_key in sorted(walls)
            ),
            "area_elements": "".join(
                cls._render_area(areas[area_key]) for area_key in sorted(areas)
            ),
            "pit_elements": "".join(
                cls._render_pit(
                    pit_key,
                    pits[pit_key],
                    normalized_highlight_team_keys,
                )
                for pit_key in sorted(pits)
            ),
            "label_elements": "".join(
                cls._render_label(
                    labels[label_key],
                    thin_wall_rects,
                    canvas_width,
                    canvas_height,
                    normalized_label_event_keys,
                )
                for label_key in sorted(labels)
            ),
            "arrow_elements": "".join(
                cls._render_arrow(arrows[arrow_key]) for arrow_key in sorted(arrows)
            ),
            "logo_element": cls._svg_icon(logo_x, logo_y, cls.LOGO_SIZE, 0.22),
        }

    @staticmethod
    def _dict_or_empty(value: dict[str, T] | None) -> dict[str, T]:
        return value or {}

    @staticmethod
    def _as_number(value: object, *, name: str) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        raise ValueError(f"Expected numeric {name}, got {value!r}")

    @staticmethod
    def _fmt_number(value: float) -> str:
        rounded = round(value, 4)
        if math.isclose(rounded, round(rounded)):
            return str(int(round(rounded)))
        return f"{rounded:.4f}".rstrip("0").rstrip(".")

    @classmethod
    def _get_position_size(
        cls, item: Mapping[str, object]
    ) -> tuple[float, float, float, float]:
        position = item.get("position")
        size = item.get("size")
        if not isinstance(position, dict) or not isinstance(size, dict):
            raise ValueError(f"Invalid map item: {item!r}")

        x = cls._as_number(position.get("x"), name="position.x")
        y = cls._as_number(position.get("y"), name="position.y")
        width = cls._as_number(size.get("x"), name="size.x")
        height = cls._as_number(size.get("y"), name="size.y")
        return x, y, width, height

    @classmethod
    def _get_centered_position_size(
        cls, item: Mapping[str, object]
    ) -> tuple[float, float, float, float]:
        x, y, width, height = cls._get_position_size(item)
        return x - width / 2, y - height / 2, width, height

    @classmethod
    def _get_wall_rect(cls, wall: MapElement) -> tuple[float, float, float, float]:
        x, y, width, height = cls._get_centered_position_size(wall)
        angle = cls._as_number(wall.get("angle", 0), name="angle")
        if math.isclose(abs(angle) % 180, 90):
            center_x = x + width / 2
            center_y = y + height / 2
            width, height = height, width
            x = center_x - width / 2
            y = center_y - height / 2
        return x, y, width, height

    @staticmethod
    def _intersection_area(
        first: tuple[float, float, float, float],
        second: tuple[float, float, float, float],
    ) -> float:
        first_x, first_y, first_width, first_height = first
        second_x, second_y, second_width, second_height = second
        overlap_width = min(first_x + first_width, second_x + second_width) - max(
            first_x, second_x
        )
        overlap_height = min(first_y + first_height, second_y + second_height) - max(
            first_y, second_y
        )
        if overlap_width <= 0 or overlap_height <= 0:
            return 0.0
        return overlap_width * overlap_height

    @staticmethod
    def _overflow_area(
        rect: tuple[float, float, float, float],
        canvas_width: float,
        canvas_height: float,
    ) -> float:
        x, y, width, height = rect
        overflow = 0.0
        if x < 0:
            overflow += -x * height
        if y < 0:
            overflow += -y * width
        if x + width > canvas_width:
            overflow += (x + width - canvas_width) * height
        if y + height > canvas_height:
            overflow += (y + height - canvas_height) * width
        return overflow

    @classmethod
    def _choose_label_rect(
        cls,
        label: Labels,
        thin_walls: list[tuple[float, float, float, float]],
        canvas_width: float,
        canvas_height: float,
    ) -> tuple[float, float, float, float]:
        centered = cls._get_centered_position_size(label)
        raw = cls._get_position_size(label)
        candidates = [centered, raw]

        def score(rect: tuple[float, float, float, float]) -> float:
            penalty = cls._overflow_area(rect, canvas_width, canvas_height) * 1000
            penalty += sum(
                cls._intersection_area(rect, wall_rect) for wall_rect in thin_walls
            )
            return penalty

        return min(candidates, key=score)

    @classmethod
    def _find_label_enclosure(
        cls,
        label: Labels,
        thin_walls: list[tuple[float, float, float, float]],
    ) -> tuple[float, float, float, float] | None:
        position = label.get("position")
        if not isinstance(position, dict):
            return None

        center_x = cls._as_number(position.get("x"), name="position.x")
        center_y = cls._as_number(position.get("y"), name="position.y")

        horizontal_walls = [wall for wall in thin_walls if wall[2] >= wall[3]]
        vertical_walls = [wall for wall in thin_walls if wall[3] > wall[2]]

        top_wall = None
        bottom_wall = None
        left_wall = None
        right_wall = None

        for wall in horizontal_walls:
            x, y, width, height = wall
            if x <= center_x <= x + width:
                if y + height <= center_y and (top_wall is None or y > top_wall[1]):
                    top_wall = wall
                if y >= center_y and (bottom_wall is None or y < bottom_wall[1]):
                    bottom_wall = wall

        for wall in vertical_walls:
            x, y, width, height = wall
            if y <= center_y <= y + height:
                if x + width <= center_x and (left_wall is None or x > left_wall[0]):
                    left_wall = wall
                if x >= center_x and (right_wall is None or x < right_wall[0]):
                    right_wall = wall

        if not all([top_wall, bottom_wall, left_wall, right_wall]):
            return None

        assert top_wall is not None
        assert bottom_wall is not None
        assert left_wall is not None
        assert right_wall is not None

        left = left_wall[0] + left_wall[2]
        right = right_wall[0]
        top = top_wall[1] + top_wall[3]
        bottom = bottom_wall[1]
        if right <= left or bottom <= top:
            return None

        return left, top, right - left, bottom - top

    @classmethod
    def _svg_rect(
        cls,
        x: float,
        y: float,
        width: float,
        height: float,
        *,
        class_name: str | None = None,
        rx: float = 0,
        opacity: float | None = None,
        transform: str | None = None,
    ) -> str:
        class_attr = f' class="{class_name}"' if class_name else ""
        rx_attr = f' rx="{cls._fmt_number(rx)}"' if rx else ""
        opacity_attr = (
            f' opacity="{cls._fmt_number(opacity)}"' if opacity is not None else ""
        )
        transform_attr = f' transform="{transform}"' if transform else ""
        return (
            f"<rect{class_attr} "
            f'x="{cls._fmt_number(x)}" y="{cls._fmt_number(y)}" '
            f'width="{cls._fmt_number(width)}" height="{cls._fmt_number(height)}"{rx_attr}'
            f"{opacity_attr}{transform_attr} />"
        )

    @classmethod
    def _svg_text(
        cls,
        x: float,
        y: float,
        text: str,
        *,
        font_size: float,
        class_name: str | None = None,
        weight: str | None = None,
        anchor: str = "middle",
        dominant_baseline: str = "middle",
    ) -> str:
        class_attr = f' class="{class_name}"' if class_name else ""
        weight_attr = f' font-weight="{weight}"' if weight else ""
        return (
            f"<text{class_attr} "
            f'x="{cls._fmt_number(x)}" y="{cls._fmt_number(y)}" '
            f'font-size="{cls._fmt_number(font_size)}" text-anchor="{anchor}" '
            f'dominant-baseline="{dominant_baseline}"{weight_attr}>{escape(text)}</text>'
        )

    @classmethod
    def _svg_wrapped_text(
        cls,
        x: float,
        y: float,
        width: float,
        height: float,
        text: str,
        *,
        font_size: float,
        class_name: str | None = None,
        weight: str | None = None,
        max_lines: int = 3,
        min_font_size: float = 10,
        width_tolerance: float = 0.98,
    ) -> str:
        words = text.split()
        if not words:
            return ""

        def wrap_lines(current_font_size: float) -> list[str]:
            estimated_chars = max(1, int(width / (current_font_size * 0.6)))
            wrapped: list[str] = []
            current = words[0]

            for word in words[1:]:
                candidate = f"{current} {word}"
                if len(candidate) <= estimated_chars:
                    current = candidate
                else:
                    wrapped.append(current)
                    current = word

            wrapped.append(current)
            return wrapped

        current_font_size = font_size
        lines = wrap_lines(current_font_size)

        while current_font_size > min_font_size:
            line_height = current_font_size * 1.15
            total_height = len(lines) * line_height
            max_line_width = max(len(line) * current_font_size * 0.6 for line in lines)
            if (
                len(lines) <= max_lines
                and total_height <= height * 0.9
                and max_line_width <= width * width_tolerance
            ):
                break
            current_font_size = max(min_font_size, current_font_size - 1)
            lines = wrap_lines(current_font_size)

        if len(lines) > max_lines:
            lines = lines[:max_lines]
            last_line = lines[-1]
            if len(last_line) > 1:
                lines[-1] = last_line[:-1].rstrip() + "…"

        line_height = current_font_size * 1.15
        start_y = y + (height - (len(lines) - 1) * line_height) / 2
        spans = []
        for index, line in enumerate(lines):
            dy = "0" if index == 0 else cls._fmt_number(line_height)
            spans.append(
                f'<tspan x="{cls._fmt_number(x)}" dy="{dy}">{escape(line)}</tspan>'
            )

        class_attr = f' class="{class_name}"' if class_name else ""
        weight_attr = f' font-weight="{weight}"' if weight else ""
        return (
            f"<text{class_attr} "
            f'x="{cls._fmt_number(x)}" y="{cls._fmt_number(start_y)}" '
            f'font-size="{cls._fmt_number(current_font_size)}" '
            f'text-anchor="middle" dominant-baseline="middle"{weight_attr}>'
            f'{"".join(spans)}</text>'
        )

    @classmethod
    def _render_pit(
        cls,
        pit_key: str,
        pit: Pits,
        highlight_team_keys: set[str],
    ) -> str:
        x, y, width, height = cls._get_centered_position_size(pit)
        angle = cls._as_number(pit.get("angle", 0), name="angle")
        team = str(pit.get("team", "")).strip()
        team_key = f"frc{team}" if team else ""
        is_highlighted = bool(team_key and team_key.lower() in highlight_team_keys)
        center_x = x + width / 2
        center_y = y + height / 2
        elements = [
            cls._svg_rect(x, y, width, height, class_name="pit-rect"),
            cls._svg_text(
                center_x,
                y + height * 0.26,
                pit_key,
                font_size=min(width, height) * 0.3,
                class_name="pit-title",
                weight="700",
            ),
        ]
        if team:
            elements.append(
                cls._svg_text(
                    center_x,
                    y + height * 0.62,
                    team,
                    font_size=min(width, height) * 0.28,
                    class_name="pit-team",
                    weight="700",
                )
            )

        content = "".join(elements)
        group_class = "pit pit-highlighted" if is_highlighted else "pit"
        team_attr = f' data-team-key="frc{escape(team)}"' if team else ""
        transform_attr = ""
        if not math.isclose(angle, 0):
            transform_attr = (
                f' transform="rotate({cls._fmt_number(angle)} '
                f'{cls._fmt_number(center_x)} {cls._fmt_number(center_y)})"'
            )

        return f'<g class="{group_class}"{team_attr}{transform_attr}>{content}</g>'

    @classmethod
    def _render_area(cls, area: Areas) -> str:
        x, y, width, height = cls._get_centered_position_size(area)
        label = str(area.get("label", "")).strip()
        return "".join(
            [
                cls._svg_rect(
                    x,
                    y,
                    width,
                    height,
                    class_name="area-rect",
                    rx=8,
                    opacity=0.98,
                ),
                cls._svg_wrapped_text(
                    x + width / 2,
                    y,
                    width - 12,
                    height,
                    label,
                    font_size=max(12, min(width, height) * 0.18),
                    class_name="area-text",
                    weight="700",
                ),
            ]
        )

    @classmethod
    def _render_wall(cls, wall: MapElement) -> str:
        angle = cls._as_number(wall.get("angle", 0), name="angle")
        x, y, width, height = cls._get_centered_position_size(wall)
        center_x = x + width / 2
        center_y = y + height / 2
        transform = None
        if not math.isclose(angle, 0):
            transform = (
                f"rotate({cls._fmt_number(angle)} {cls._fmt_number(center_x)} "
                f"{cls._fmt_number(center_y)})"
            )
        return cls._svg_rect(
            x,
            y,
            width,
            height,
            class_name="wall",
            transform=transform,
        )

    @classmethod
    def _render_label(
        cls,
        label: Labels,
        thin_walls: list[tuple[float, float, float, float]],
        canvas_width: float,
        canvas_height: float,
        label_event_keys: dict[str, str],
    ) -> str:
        x, y, width, height = cls._choose_label_rect(
            label,
            thin_walls,
            canvas_width,
            canvas_height,
        )

        enclosure = cls._find_label_enclosure(label, thin_walls)
        if enclosure is not None:
            enclosure_x, enclosure_y, enclosure_width, enclosure_height = enclosure
            expansion = 0.35
            width = width + (enclosure_width - width) * expansion
            height = height + (enclosure_height - height) * expansion
            x = enclosure_x + (enclosure_width - width) / 2
            y = enclosure_y + (enclosure_height - height) / 2

        text = str(label.get("label", "")).strip()
        font_size = max(12, min(width, height) * 0.38)
        rendered = cls._svg_wrapped_text(
            x + width / 2,
            y,
            width,
            height,
            text,
            font_size=font_size,
            class_name="label-text",
            weight="700",
            max_lines=3,
            width_tolerance=0.98,
        )
        event_key = label_event_keys.get(text.lower()) if text else None
        if not event_key:
            return rendered
        return f'<g data-label-key="{escape(event_key)}">{rendered}</g>'

    @classmethod
    def _render_arrow(cls, arrow: Arrows) -> str:
        x, y, width, height = cls._get_centered_position_size(arrow)
        angle = cls._as_number(arrow.get("angle", 0), name="angle")
        arrow_type = str(arrow.get("type", "single")).strip().lower()
        center_x = x + width / 2
        center_y = y + height / 2
        left = x + width * 0.22
        right = x + width * 0.78
        top = y + height * 0.12
        bottom = y + height * 0.88
        shaft_left = x + width * 0.38
        shaft_right = x + width * 0.62

        if arrow_type == "double":
            shaft_top = y + height * 0.30
            shaft_bottom = y + height * 0.70
            points = [
                (center_x, top),
                (right, shaft_top),
                (shaft_right, shaft_top),
                (shaft_right, shaft_bottom),
                (right, shaft_bottom),
                (center_x, bottom),
                (left, shaft_bottom),
                (shaft_left, shaft_bottom),
                (shaft_left, shaft_top),
                (left, shaft_top),
            ]
        else:
            shaft_top = y + height * 0.45
            points = [
                (center_x, top),
                (right, shaft_top),
                (shaft_right, shaft_top),
                (shaft_right, bottom),
                (shaft_left, bottom),
                (shaft_left, shaft_top),
                (left, shaft_top),
            ]

        point_string = " ".join(
            f"{cls._fmt_number(px)},{cls._fmt_number(py)}" for px, py in points
        )
        return (
            f'<polygon class="arrow" points="{point_string}" '
            f'transform="rotate({cls._fmt_number(angle)} {cls._fmt_number(center_x)} '
            f'{cls._fmt_number(center_y)})" />'
        )

    _DARK_MEDIA_QUERY = "@media (prefers-color-scheme: dark)"

    @classmethod
    def force_light_color_scheme(cls, svg: str) -> str:
        """Strip the dark-mode @media block so the SVG always renders light colors.

        Used when checking in golden fixtures so PR review renders consistently.
        """
        start = svg.find(cls._DARK_MEDIA_QUERY)
        if start == -1:
            return svg
        brace_start = svg.find("{", start)
        if brace_start == -1:
            return svg
        depth = 1
        i = brace_start + 1
        while i < len(svg) and depth > 0:
            if svg[i] == "{":
                depth += 1
            elif svg[i] == "}":
                depth -= 1
            i += 1
        line_start = svg.rfind("\n", 0, start) + 1
        end = i
        if end < len(svg) and svg[end] == "\n":
            end += 1
        return svg[:line_start] + svg[end:]

    @classmethod
    def force_dark_color_scheme(cls, svg: str) -> str:
        """Make the dark-mode @media block always apply, forcing dark colors."""
        return svg.replace(cls._DARK_MEDIA_QUERY, "@media all")

    @classmethod
    def _svg_icon(cls, x: float, y: float, size: float, opacity: float) -> str:
        return (
            f'<g transform="translate({cls._fmt_number(x)} {cls._fmt_number(y)})" '
            f'opacity="{cls._fmt_number(opacity)}">'
            f'<svg x="0" y="0" width="{cls._fmt_number(size)}" '
            f'height="{cls._fmt_number(size)}" viewBox="0 0 86 86" '
            f'xmlns="{cls.SVG_NAMESPACE}">'
            '<path d="M41.0447 2.08864C41.4978 -0.0171729 44.5022 -0.0171749 44.9553 2.08864L49.4708 23.0783C49.765 24.4458 51.3362 25.0966 52.5112 24.3376L70.5461 12.6887C72.3555 11.52 74.48 13.6445 73.3113 15.4539L61.6624 33.4888C60.9034 34.6638 61.5542 36.235 62.9217 36.5292L83.9114 41.0447C86.0172 41.4978 86.0172 44.5022 83.9114 44.9553L62.9217 49.4708C61.5542 49.765 60.9034 51.3362 61.6624 52.5112L73.3113 70.5461C74.48 72.3555 72.3555 74.48 70.5461 73.3113L52.5112 61.6624C51.3362 60.9034 49.765 61.5542 49.4708 62.9217L44.9553 83.9114C44.5022 86.0172 41.4978 86.0172 41.0447 83.9114L36.5292 62.9217C36.235 61.5542 34.6638 60.9034 33.4888 61.6624L15.4539 73.3113C13.6445 74.48 11.52 72.3555 12.6887 70.5461L24.3376 52.5112C25.0966 51.3362 24.4458 49.765 23.0783 49.4708L2.08864 44.9553C-0.0171729 44.5022 -0.0171749 41.4978 2.08864 41.0447L23.0783 36.5292C24.4458 36.235 25.0966 34.6638 24.3376 33.4888L12.6887 15.4539C11.52 13.6445 13.6445 11.52 15.4539 12.6887L33.4888 24.3376C34.6638 25.0966 36.235 24.4458 36.5292 23.0783L41.0447 2.08864Z" fill="url(#nexus-logo-gradient)"/>'
            '<defs><linearGradient id="nexus-logo-gradient" x1="35.6147" y1="24.246" x2="50.9101" y2="61.9304" gradientUnits="userSpaceOnUse"><stop stop-color="#0d6efd"/><stop offset="1" stop-color="#dc3545"/></linearGradient></defs>'
            "</svg></g>"
        )
