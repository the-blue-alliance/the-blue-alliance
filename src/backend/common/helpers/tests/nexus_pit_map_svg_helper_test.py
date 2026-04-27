import pytest

from backend.common.helpers.nexus_pit_map_svg_helper import NexusPitMapSVGHelper


def test_template_values_renders_expected_sections() -> None:
    map_data = {
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

    values = NexusPitMapSVGHelper.template_values(map_data, "2026nyny")

    assert values["event_url"] == "https://frc.nexus/en/event/2026nyny/pits"
    assert "A1" in values["pit_elements"]
    assert "1678" in values["pit_elements"]
    assert "Inspection" in values["area_elements"]
    assert "Field" in values["label_elements"]
    assert "polygon" in values["arrow_elements"]


def test_template_values_applies_pit_rotation_angle() -> None:
    map_data = {
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

    values = NexusPitMapSVGHelper.template_values(map_data, "2026nyny")

    assert 'transform="rotate(90 50 50)"' in values["pit_elements"]


def test_template_values_requires_size() -> None:
    with pytest.raises(ValueError):
        NexusPitMapSVGHelper.template_values({"pits": {}}, "2026nyny")


def test_template_values_rejects_bad_section_type() -> None:
    with pytest.raises(ValueError):
        NexusPitMapSVGHelper.template_values(
            {
                "size": {"x": 100, "y": 100},
                "pits": [],
            },
            "2026nyny",
        )
