import enum
import json
from pathlib import Path

import pytest

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.consts.webcast_status import WebcastStatus

SPEC_PATH = (
    Path(__file__).resolve().parents[4]
    / "backend"
    / "web"
    / "static"
    / "swagger"
    / "api_v3.json"
)


@pytest.fixture(scope="module")
def spec_schemas() -> dict:
    with SPEC_PATH.open() as f:
        spec = json.load(f)
    return spec["components"]["schemas"]


@pytest.mark.parametrize(
    "schema_name,enum_class",
    [
        ("AwardType", AwardType),
        ("EventType", EventType),
        ("PlayoffType", PlayoffType),
    ],
)
def test_spec_integer_enum_matches_python(
    spec_schemas: dict, schema_name: str, enum_class: type[enum.IntEnum]
) -> None:
    schema = spec_schemas[schema_name]
    expected_values = [member.value for member in enum_class]
    expected_names = [member.name for member in enum_class]

    assert schema["type"] == "integer"
    assert schema["enum"] == expected_values, (
        f"{schema_name}.enum in api_v3.json does not match "
        f"{enum_class.__name__} value order from Python"
    )
    assert schema["x-enum-varnames"] == expected_names, (
        f"{schema_name}.x-enum-varnames in api_v3.json does not match "
        f"{enum_class.__name__} member names from Python"
    )
    assert len(schema["enum"]) == len(schema["x-enum-varnames"])


@pytest.mark.parametrize(
    "schema_name,enum_class",
    [
        ("AllianceColor", AllianceColor),
        ("WebcastStatus", WebcastStatus),
    ],
)
def test_spec_string_enum_matches_python(
    spec_schemas: dict, schema_name: str, enum_class: type[enum.StrEnum]
) -> None:
    schema = spec_schemas[schema_name]
    expected_values = [member.value for member in enum_class]
    expected_names = [member.name for member in enum_class]

    assert schema["type"] == "string"
    assert schema["enum"] == expected_values, (
        f"{schema_name}.enum in api_v3.json does not match "
        f"{enum_class.__name__} value order from Python"
    )
    assert schema["x-enum-varnames"] == expected_names, (
        f"{schema_name}.x-enum-varnames in api_v3.json does not match "
        f"{enum_class.__name__} member names from Python"
    )
    assert len(schema["enum"]) == len(schema["x-enum-varnames"])
