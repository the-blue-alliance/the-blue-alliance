import json
import os
from typing import cast

import pytest

from backend.common.nexus_api.types import PitMap
from backend.tasks_io.datafeeds.parsers.nexus_api.pit_map_parser import (
    NexusAPIPitMapParser,
)


@pytest.fixture(scope="module")
def pit_map_2026nyny() -> PitMap:
    fixture_path = os.path.join(os.path.dirname(__file__), "2026nyny_pit_map.json")
    with open(fixture_path) as f:
        return json.load(f)


def test_bad_format_returns_empty() -> None:
    parser = NexusAPIPitMapParser()
    result = parser.parse(cast(PitMap, ["not", "a", "dict"]))
    assert result == {}


def test_bad_format_string_returns_empty() -> None:
    parser = NexusAPIPitMapParser()
    result = parser.parse(cast(PitMap, "bad"))
    assert result == {}


def test_parse_minimal_valid_dict() -> None:
    parser = NexusAPIPitMapParser()
    minimal: PitMap = {
        "pits": {"A1": {"position": {"x": 0.0, "y": 0.0}, "size": {"x": 100, "y": 100}}}
    }
    result = parser.parse(minimal)
    assert result is minimal


def test_parse_real_response_size(pit_map_2026nyny: PitMap) -> None:
    parser = NexusAPIPitMapParser()
    result = parser.parse(pit_map_2026nyny)
    assert result["size"] == {"x": 868, "y": 1802}


def test_parse_real_response_pit_count(pit_map_2026nyny: PitMap) -> None:
    parser = NexusAPIPitMapParser()
    result = parser.parse(pit_map_2026nyny)
    assert len(result["pits"]) == 52


def test_parse_real_response_pit_with_team(pit_map_2026nyny: PitMap) -> None:
    """A1 is a regular pit with a team assignment."""
    parser = NexusAPIPitMapParser()
    result = parser.parse(pit_map_2026nyny)
    a1 = result["pits"]["A1"]
    assert a1["team"] == "4729"
    assert a1["size"] == {"x": 100, "y": 100}


def test_parse_real_response_pit_without_team(pit_map_2026nyny: PitMap) -> None:
    """A5 is a pit with no team key (unassigned pit)."""
    parser = NexusAPIPitMapParser()
    result = parser.parse(pit_map_2026nyny)
    a5 = result["pits"]["A5"]
    assert "team" not in a5


def test_parse_real_response_pit_with_angle(pit_map_2026nyny: PitMap) -> None:
    """U3 is a pit with an angle (rotated pit)."""
    parser = NexusAPIPitMapParser()
    result = parser.parse(pit_map_2026nyny)
    u3 = result["pits"]["U3"]
    assert "angle" in u3
    angle = u3["angle"]
    assert angle is not None
    assert abs(angle - 54.4301) < 1e-6
    assert u3["team"] == "4299"


def test_parse_real_response_areas(pit_map_2026nyny: PitMap) -> None:
    parser = NexusAPIPitMapParser()
    result = parser.parse(pit_map_2026nyny)
    areas = result["areas"]
    assert areas is not None
    assert set(areas.keys()) == {"a0", "a1", "a2", "a3"}
    assert areas["a0"]["label"] == "Inspection"


def test_parse_real_response_walls_null(pit_map_2026nyny: PitMap) -> None:
    parser = NexusAPIPitMapParser()
    result = parser.parse(pit_map_2026nyny)
    assert result.get("walls") is None


def test_parse_real_response_is_passthrough(pit_map_2026nyny: PitMap) -> None:
    """Parser should return the same object, not a copy."""
    parser = NexusAPIPitMapParser()
    result = parser.parse(pit_map_2026nyny)
    assert result is pit_map_2026nyny
