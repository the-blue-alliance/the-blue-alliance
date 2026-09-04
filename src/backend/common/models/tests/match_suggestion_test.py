import json

import pytest
from pydantic import ValidationError

from backend.common.consts.comp_level import CompLevel
from backend.common.models.match_suggestion import (
    MatchSuggestion,
    MatchSuggestionComponents,
    MatchSuggestions,
)


def _suggestion() -> MatchSuggestion:
    return MatchSuggestion(
        match_key="2026cmptx_sf3m1",
        event_key="2026cmptx",
        event_name="Einstein Field",
        event_short_name="Einstein",
        comp_level=CompLevel.SF,
        set_number=3,
        match_number=1,
        display_name="SF3-1",
        red_team_numbers=[254, 1114, 2056],
        blue_team_numbers=[118, 148, 971],
        predicted_time=1777000000,
        scheduled_time=1776999000,
        rank=0,
        score=0.8125,
        components=MatchSuggestionComponents(
            favorites=1.0, significance=0.4, time_decay=0.9, performance=0.75
        ),
    )


def test_model_dump_is_json_serializable() -> None:
    suggestions = MatchSuggestions(
        updated_at=1777000000,
        suggestions={"2026cmptx_sf3m1": _suggestion()},
    )

    dumped = suggestions.model_dump(mode="json", by_alias=True)
    # Must survive the trip through the Firebase SDK's JSON encoder
    json.dumps(dumped)

    entry = dumped["suggestions"]["2026cmptx_sf3m1"]
    # Per-suggestion keys are published terse to keep the feed small
    assert entry["cl"] == "sf"
    # A StrEnum that dumped as an enum object rather than "sf" would silently
    # break the client
    assert isinstance(entry["cl"], str)
    assert entry["c"]["f"] == 1.0


def test_model_dump_defaults_to_empty_suggestions() -> None:
    dumped = MatchSuggestions(updated_at=1777000000).model_dump(
        mode="json", by_alias=True
    )
    # Root keys are written once per document, so they stay readable
    assert dumped == {"updated_at": 1777000000, "suggestions": {}}


def test_optional_times_dump_as_none() -> None:
    unscheduled = _suggestion().model_copy(
        update={"predicted_time": None, "scheduled_time": None}
    )
    dumped = unscheduled.model_dump(mode="json", by_alias=True)
    assert dumped["pt"] is None
    assert dumped["st"] is None


def test_json_schema_generates() -> None:
    schema = MatchSuggestions.model_json_schema()
    assert "updated_at" in schema["properties"]
    # The contract that a future json-schema-to-typescript codegen depends on
    assert "$ref" in schema["properties"]["suggestions"]["additionalProperties"]
    assert "MatchSuggestion" in schema["$defs"]
    assert "MatchSuggestionComponents" in schema["$defs"]


def test_missing_required_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        MatchSuggestion(match_key="2026cmptx_sf3m1")


def test_schema_matches_the_dumped_shape() -> None:
    # The exported schema drives client codegen, so its properties have to be
    # exactly the keys that end up in the payload
    props = MatchSuggestions.model_json_schema()["$defs"]["MatchSuggestion"][
        "properties"
    ]
    assert set(props) == set(_suggestion().model_dump(mode="json", by_alias=True))
