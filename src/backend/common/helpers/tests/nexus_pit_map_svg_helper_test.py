import pytest

from backend.common.helpers.nexus_pit_map_svg_helper import NexusEventDetailsSVGHelper
from backend.common.nexus_api.types import Labels, PitMap


def test_template_values_renders_expected_sections() -> None:
    map_data: PitMap = {
        "size": {"x": 100, "y": 200},
        "pits": {
            "A1": {
                "position": {"x": 50, "y": 50},
                "size": {"x": 40, "y": 40},
                "team": "1678",
            }
        },
        "areas": {
            "a0": {
                "position": {"x": 20, "y": 150},
                "size": {"x": 30, "y": 30},
                "label": "Inspection",
            }
        },
        "labels": {
            "l0": {
                "position": {"x": 80, "y": 180},
                "size": {"x": 20, "y": 10},
                "label": "Field",
            }
        },
        "arrows": {
            "r0": {
                "position": {"x": 70, "y": 120},
                "size": {"x": 20, "y": 20},
                "type": "single",
            }
        },
        "walls": None,
    }

    values = NexusEventDetailsSVGHelper.template_values(map_data, "2026nyny")

    assert values["event_url"] == "https://frc.nexus/2026nyny/pits"
    assert "A1" in values["pit_elements"]
    assert "1678" in values["pit_elements"]
    assert "Inspection" in values["area_elements"]
    assert "Field" in values["label_elements"]
    assert "polygon" in values["arrow_elements"]


def test_template_values_applies_pit_rotation_angle() -> None:
    map_data: PitMap = {
        "size": {"x": 100, "y": 100},
        "pits": {
            "A1": {
                "position": {"x": 50, "y": 50},
                "size": {"x": 40, "y": 40},
                "angle": 90,
                "team": "1678",
            }
        },
        "areas": None,
        "labels": None,
        "arrows": None,
        "walls": None,
    }

    values = NexusEventDetailsSVGHelper.template_values(map_data, "2026nyny")

    assert 'transform="rotate(90 50 50)"' in values["pit_elements"]


def test_template_values_labels_carry_label_key_attribute() -> None:
    map_data: PitMap = {
        "size": {"x": 200, "y": 200},
        "labels": {
            "l0": {
                "position": {"x": 50, "y": 50},
                "size": {"x": 60, "y": 30},
                "label": "Hopper",
            },
            "l1": {
                "position": {"x": 150, "y": 150},
                "size": {"x": 60, "y": 30},
                "label": "JOHNSON",
            },
            "l2": {
                "position": {"x": 100, "y": 100},
                "size": {"x": 60, "y": 30},
                "label": "Inspection",
            },
        },
    }

    values = NexusEventDetailsSVGHelper.template_values(
        map_data,
        "2026joh",
        label_event_keys={"hopper": "2026hop", "johnson": "2026joh"},
    )

    assert 'data-label-key="2026hop"' in values["label_elements"]
    assert 'data-label-key="2026joh"' in values["label_elements"]
    assert "Inspection" in values["label_elements"]
    assert values["label_elements"].count("data-label-key=") == 2


def test_template_values_pits_carry_team_key_attribute() -> None:
    map_data: PitMap = {
        "size": {"x": 100, "y": 100},
        "pits": {
            "A1": {
                "position": {"x": 50, "y": 50},
                "size": {"x": 40, "y": 40},
                "team": "1678",
            },
            "A2": {
                "position": {"x": 50, "y": 50},
                "size": {"x": 40, "y": 40},
                "angle": 90,
                "team": "254",
            },
            "A3": {
                "position": {"x": 50, "y": 50},
                "size": {"x": 40, "y": 40},
            },
        },
        "areas": None,
        "labels": None,
        "arrows": None,
        "walls": None,
    }

    values = NexusEventDetailsSVGHelper.template_values(map_data, "2026nyny")

    assert 'data-team-key="frc1678"' in values["pit_elements"]
    assert 'data-team-key="frc254"' in values["pit_elements"]
    assert values["pit_elements"].count("data-team-key=") == 2


def test_template_values_highlights_frc_team_keys() -> None:
    map_data: PitMap = {
        "size": {"x": 100, "y": 100},
        "pits": {
            "A1": {
                "position": {"x": 50, "y": 50},
                "size": {"x": 40, "y": 40},
                "team": "1678",
            }
        },
        "areas": None,
        "labels": None,
        "arrows": None,
        "walls": None,
    }

    values = NexusEventDetailsSVGHelper.template_values(
        map_data,
        "2026nyny",
        highlight_team_keys={"frc1678"},
    )

    assert 'class="pit pit-highlighted"' in values["pit_elements"]


def test_template_values_requires_size() -> None:
    map_data: PitMap = {"pits": {}}
    with pytest.raises(ValueError):
        NexusEventDetailsSVGHelper.template_values(map_data, "2026nyny")


def test_highlighted_pits_render_last_so_neighbors_dont_cover_stroke() -> None:
    map_data: PitMap = {
        "size": {"x": 200, "y": 100},
        "pits": {
            "A1": {
                "position": {"x": 30, "y": 50},
                "size": {"x": 40, "y": 40},
                "team": "10922",
            },
            "B1": {
                "position": {"x": 80, "y": 50},
                "size": {"x": 40, "y": 40},
                "team": "1678",
            },
            "C1": {
                "position": {"x": 130, "y": 50},
                "size": {"x": 40, "y": 40},
                "team": "254",
            },
        },
        "areas": None,
        "labels": None,
        "arrows": None,
        "walls": None,
    }

    values = NexusEventDetailsSVGHelper.template_values(
        map_data,
        "2026nysu",
        highlight_team_keys={"frc10922"},
    )

    elements = values["pit_elements"]
    a1_index = elements.find('data-team-key="frc10922"')
    b1_index = elements.find('data-team-key="frc1678"')
    c1_index = elements.find('data-team-key="frc254"')
    assert 0 <= b1_index < c1_index < a1_index


def test_force_light_color_scheme_strips_dark_media_block() -> None:
    svg = (
        "<svg><style>\n"
        "    svg { --x: #fff; }\n"
        "    @media (prefers-color-scheme: dark) {\n"
        "      svg { --x: #000; }\n"
        "    }\n"
        "    .foo { fill: var(--x); }\n"
        "</style></svg>"
    )
    forced = NexusEventDetailsSVGHelper.force_light_color_scheme(svg)
    assert "@media" not in forced
    assert "--x: #fff" in forced
    assert "--x: #000" not in forced
    assert ".foo { fill: var(--x); }" in forced


def test_force_dark_color_scheme_makes_dark_block_unconditional() -> None:
    svg = (
        "<svg><style>\n"
        "    svg { --x: #fff; }\n"
        "    @media (prefers-color-scheme: dark) {\n"
        "      svg { --x: #000; }\n"
        "    }\n"
        "</style></svg>"
    )
    forced = NexusEventDetailsSVGHelper.force_dark_color_scheme(svg)
    assert "(prefers-color-scheme: dark)" not in forced
    assert "@media all" in forced
    assert "--x: #000" in forced


def test_force_light_color_scheme_is_a_noop_when_no_dark_block() -> None:
    svg = "<svg><style>svg { --x: #fff; }</style></svg>"
    assert NexusEventDetailsSVGHelper.force_light_color_scheme(svg) == svg


def test_template_values_handles_missing_sections() -> None:
    map_data: PitMap = {
        "size": {"x": 100, "y": 100},
    }

    values = NexusEventDetailsSVGHelper.template_values(map_data, "2026nyny")

    assert values["pit_elements"] == ""
    assert values["area_elements"] == ""
    assert values["label_elements"] == ""
    assert values["arrow_elements"] == ""


def test_template_values_rejects_non_numeric_size() -> None:
    map_data: PitMap = {"size": {"x": "100", "y": 100}}  # pyre-ignore[55]

    with pytest.raises(ValueError, match="Expected numeric size.x, got '100'"):
        NexusEventDetailsSVGHelper.template_values(map_data, "2026nyny")


def test_template_values_rejects_map_item_without_size() -> None:
    map_data: PitMap = {
        "size": {"x": 100, "y": 100},
        "pits": {"A1": {"position": {"x": 50, "y": 50}, "team": "1678"}},
    }

    with pytest.raises(ValueError, match="Invalid map item"):
        NexusEventDetailsSVGHelper.template_values(map_data, "2026nyny")


def test_thin_walls_enclosing_a_label_expand_it() -> None:
    """
    Four thin walls form a box around a label. Rotated walls are rendered
    with a rotate transform and are treated as vertical when computing the
    enclosure. The enclosed label grows towards the box, which shows up as
    a larger font size than the label's own 60x30 box would allow.
    """
    map_data: PitMap = {
        "size": {"x": 300, "y": 300},
        "walls": {
            "top": {"position": {"x": 150, "y": 50}, "size": {"x": 200, "y": 4}},
            "bottom": {"position": {"x": 150, "y": 250}, "size": {"x": 200, "y": 4}},
            # Horizontal wall rotated 90 degrees: vertical on the left
            "left": {
                "position": {"x": 50, "y": 150},
                "size": {"x": 200, "y": 4},
                "angle": 90,
            },
            "right": {"position": {"x": 250, "y": 150}, "size": {"x": 4, "y": 200}},
            # Thick wall, ignored for label placement
            "block": {"position": {"x": 150, "y": 150}, "size": {"x": 50, "y": 50}},
        },
        "labels": {
            "l0": {
                "position": {"x": 150, "y": 150},
                "size": {"x": 60, "y": 30},
                "label": "Field",
            }
        },
    }

    values = NexusEventDetailsSVGHelper.template_values(map_data, "2026nyny")

    assert values["wall_elements"].count('class="wall"') == 5
    assert 'transform="rotate(90 50 150)"' in values["wall_elements"]
    # Enclosure is (52, 52, 196, 196); width grows to 107.6 and height to
    # 88.1, so the font is 88.1 * 0.38 rather than 30 * 0.38 (floored at 12)
    assert 'font-size="33.478"' in values["label_elements"]
    assert 'x="150" y="150"' in values["label_elements"]
    assert ">Field</tspan>" in values["label_elements"]


def test_label_rect_avoids_canvas_overflow_and_thin_walls() -> None:
    """
    Each label picks whichever of its centered/raw rectangles overflows the
    canvas least and overlaps thin walls least. The rendered text position
    reveals which rectangle won.
    """
    map_data: PitMap = {
        "size": {"x": 300, "y": 300},
        "walls": {
            "w": {"position": {"x": 100, "y": 100}, "size": {"x": 100, "y": 4}},
        },
        "labels": {
            # Centered rect would start at x=-10: raw rect wins
            "left": {
                "position": {"x": 10, "y": 200},
                "size": {"x": 40, "y": 20},
                "label": "Left",
            },
            # Centered rect would start at y=-5: raw rect wins
            "top": {
                "position": {"x": 150, "y": 5},
                "size": {"x": 40, "y": 20},
                "label": "Top",
            },
            # Both overflow the bottom edge; the centered rect overflows less
            "bottom": {
                "position": {"x": 150, "y": 295},
                "size": {"x": 40, "y": 20},
                "label": "Bottom",
            },
            # Centered rect crosses the thin wall: raw rect wins
            "wall": {
                "position": {"x": 100, "y": 110},
                "size": {"x": 40, "y": 20},
                "label": "Wall",
            },
        },
    }

    values = NexusEventDetailsSVGHelper.template_values(map_data, "2026nyny")

    labels = values["label_elements"]
    assert 'x="30" y="210"' in labels  # raw (10, 200) + half size
    assert 'x="170" y="15"' in labels  # raw (150, 5) + half size
    assert 'x="150" y="295"' in labels  # centered (130, 285) + half size
    assert 'x="120" y="120"' in labels  # raw (100, 110) + half size


def test_find_label_enclosure_edge_cases() -> None:
    helper = NexusEventDetailsSVGHelper

    # A label without a position has no enclosure
    assert helper._find_label_enclosure({"label": "x"}, []) is None

    # Walls touching the label center on both sides leave no room
    thin_walls = [
        (0.0, 48.0, 200.0, 4.0),  # top
        (0.0, 148.0, 200.0, 4.0),  # bottom
        (96.0, 50.0, 4.0, 100.0),  # left, ends exactly at x=100
        (100.0, 50.0, 4.0, 100.0),  # right, starts exactly at x=100
    ]
    label: Labels = {"position": {"x": 100, "y": 100}, "size": {"x": 10, "y": 10}}
    assert helper._find_label_enclosure(label, thin_walls) is None

    # Widening the right wall's position gives a real enclosure
    thin_walls[3] = (140.0, 50.0, 4.0, 100.0)
    assert helper._find_label_enclosure(label, thin_walls) == (100.0, 52.0, 40.0, 96.0)


def test_area_text_wraps_and_truncates_long_labels() -> None:
    map_data: PitMap = {
        "size": {"x": 300, "y": 300},
        "areas": {
            "long": {
                "position": {"x": 100, "y": 100},
                "size": {"x": 60, "y": 40},
                "label": "Alpha Beta Gamma Delta Epsilon Zeta",
            },
            "empty": {
                "position": {"x": 200, "y": 200},
                "size": {"x": 60, "y": 40},
                "label": "   ",
            },
            "wide": {
                "position": {"x": 150, "y": 250},
                "size": {"x": 200, "y": 40},
                "label": "Pit Admin Desk",
            },
        },
    }

    values = NexusEventDetailsSVGHelper.template_values(map_data, "2026nyny")

    areas = values["area_elements"]
    # Short words in a wide area share a single line
    assert '<tspan x="150" dy="0">Pit Admin Desk</tspan>' in areas
    # Six words do not fit even at the minimum font size, so the text is cut
    # to three lines with an ellipsis on the last one
    assert '<tspan x="100" dy="0">Alpha</tspan>' in areas
    assert '<tspan x="100" dy="11.5">Beta</tspan>' in areas
    assert '<tspan x="100" dy="11.5">Gamm…</tspan>' in areas
    assert "Delta" not in areas
    assert 'font-size="10"' in areas
    # A blank label renders the area rectangle without any text
    assert areas.count('class="area-rect"') == 3
    assert areas.count("<text") == 2


def test_double_arrow_renders_ten_points() -> None:
    map_data: PitMap = {
        "size": {"x": 300, "y": 300},
        "arrows": {
            "single": {
                "position": {"x": 50, "y": 50},
                "size": {"x": 20, "y": 40},
                "type": "single",
            },
            "double": {
                "position": {"x": 150, "y": 50},
                "size": {"x": 20, "y": 40},
                "type": "double",
                "angle": 45,
            },
        },
    }

    values = NexusEventDetailsSVGHelper.template_values(map_data, "2026nyny")

    polygons = values["arrow_elements"].split("<polygon")[1:]
    assert len(polygons) == 2
    double, single = polygons  # sorted by key
    assert single.split('points="')[1].split('"')[0].count(",") == 7
    assert double.split('points="')[1].split('"')[0].count(",") == 10
    assert 'transform="rotate(45 150 50)"' in double


def test_force_light_color_scheme_is_a_noop_without_block_braces() -> None:
    svg = "<svg><style>@media (prefers-color-scheme: dark)</style></svg>"
    assert NexusEventDetailsSVGHelper.force_light_color_scheme(svg) == svg
