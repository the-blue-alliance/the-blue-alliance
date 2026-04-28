import pytest

from backend.common.helpers.nexus_pit_map_svg_helper import NexusEventDetailsSVGHelper
from backend.common.nexus_api.types import PitMap


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
