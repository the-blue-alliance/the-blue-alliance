import json
import os

import pytest

from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.playoff_advancement_helper import (
    PlayoffAdvancementHelper,
)
from backend.common.models.event import Event
from backend.common.models.keys import EventKey


@pytest.fixture(autouse=True)
def auto_add_ndb_context(ndb_context) -> None:
    pass


def create_event(event_key: EventKey, playoff_type: PlayoffType) -> Event:
    return Event(
        id=event_key,
        event_type_enum=EventType.OFFSEASON,
        year=int(event_key[:4]),
        official=True,
        playoff_type=playoff_type,
    )


def test_standard_bracket(test_data_importer) -> None:
    event = create_event("2019nyny", PlayoffType.BRACKET_8_TEAM)
    test_data_importer.import_event_alliances(
        __file__, "data/2019nyny_alliances.json", "2019nyny"
    )
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    organized_matches = MatchHelper.organized_matches(matches)[1]

    advancement = PlayoffAdvancementHelper.generate_playoff_advancement(
        event, organized_matches
    )
    with open(
        f"{os.path.dirname(__file__)}/data/expected_advancement_2019nyny.json", "r"
    ) as f:
        expected_advancement = json.load(f)

    assert json.loads(json.dumps(advancement)) == expected_advancement

    apiv3_response = (
        PlayoffAdvancementHelper.create_playoff_advancement_response_for_apiv3(
            event, advancement.playoff_advancement, advancement.bracket_table
        )
    )
    with open(
        f"{os.path.dirname(__file__)}/data/expected_advancement_apiv3_2019nyny.json",
        "r",
    ) as f:
        expected_advancement_apiv3 = json.load(f)
    assert apiv3_response == expected_advancement_apiv3


def test_2015_event(test_data_importer) -> None:
    event = create_event("2015nyny", PlayoffType.AVG_SCORE_8_TEAM)
    test_data_importer.import_event_alliances(
        __file__, "data/2015nyny_alliances.json", "2015nyny"
    )
    matches = test_data_importer.parse_match_list(
        __file__, "data/2015nyny_matches.json"
    )
    organized_matches = MatchHelper.organized_matches(matches)[1]

    advancement = PlayoffAdvancementHelper.generate_playoff_advancement(
        event, organized_matches
    )
    with open(
        f"{os.path.dirname(__file__)}/data/expected_advancement_2015nyny.json", "r"
    ) as f:
        expected_advancement = json.load(f)

    assert json.loads(json.dumps(advancement)) == expected_advancement

    apiv3_response = (
        PlayoffAdvancementHelper.create_playoff_advancement_response_for_apiv3(
            event, advancement.playoff_advancement, advancement.bracket_table
        )
    )
    with open(
        f"{os.path.dirname(__file__)}/data/expected_advancement_apiv3_2015nyny.json",
        "r",
    ) as f:
        expected_advancement_apiv3 = json.load(f)
    assert apiv3_response == expected_advancement_apiv3


@pytest.mark.parametrize(
    "event_key", ["2017cmpmo", "2018cmptx", "2019cmptx", "2022cmptx"]
)
def test_round_robin(test_data_importer, event_key) -> None:
    event = create_event(event_key, PlayoffType.ROUND_ROBIN_6_TEAM)
    test_data_importer.import_event_alliances(
        __file__, f"data/{event_key}_alliances.json", event_key
    )
    matches = test_data_importer.parse_match_list(
        __file__, f"data/{event_key}_matches.json"
    )
    organized_matches = MatchHelper.organized_matches(matches)[1]

    advancement = PlayoffAdvancementHelper.generate_playoff_advancement(
        event, organized_matches
    )

    with open(
        f"{os.path.dirname(__file__)}/data/expected_advancement_{event_key}.json", "r"
    ) as f:
        expected_advancement = json.load(f)

    assert json.loads(json.dumps(advancement)) == expected_advancement

    apiv3_response = (
        PlayoffAdvancementHelper.create_playoff_advancement_response_for_apiv3(
            event, advancement.playoff_advancement, advancement.bracket_table
        )
    )
    with open(
        f"{os.path.dirname(__file__)}/data/expected_advancement_apiv3_{event_key}.json",
        "r",
    ) as f:
        expected_advancement_apiv3 = json.load(f)
    assert apiv3_response == expected_advancement_apiv3


def test_best_of_3_finals(test_data_importer) -> None:
    event = create_event("2019nyny", PlayoffType.BO3_FINALS)
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    organized_matches = MatchHelper.organized_matches(matches)[1]

    advancement = PlayoffAdvancementHelper.generate_playoff_advancement(
        event, organized_matches
    )
    assert advancement.bracket_table is not None
    assert advancement.playoff_advancement is None
    assert advancement.double_elim_matches is None
    assert advancement.playoff_template is None


def test_best_of_5_finals(test_data_importer) -> None:
    event = create_event("2019nyny", PlayoffType.BO5_FINALS)
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    organized_matches = MatchHelper.organized_matches(matches)[1]

    advancement = PlayoffAdvancementHelper.generate_playoff_advancement(
        event, organized_matches
    )
    assert advancement.bracket_table is not None
    assert advancement.playoff_advancement is None
    assert advancement.double_elim_matches is None
    assert advancement.playoff_template is None


def test_legacy_double_elim(test_data_importer) -> None:
    event = create_event("2017wiwi", PlayoffType.LEGACY_DOUBLE_ELIM_8_TEAM)
    matches = test_data_importer.parse_match_list(
        __file__, "data/2017wiwi_matches.json"
    )
    organized_matches = MatchHelper.organized_matches(matches)[1]
    advancement = PlayoffAdvancementHelper.generate_playoff_advancement(
        event, organized_matches
    )
    assert advancement.bracket_table is not None
    assert advancement.playoff_advancement is None
    assert advancement.double_elim_matches is not None
    assert advancement.playoff_template is None


def test_double_elim(test_data_importer) -> None:
    event = create_event("2022cctets", PlayoffType.DOUBLE_ELIM_8_TEAM)
    matches = test_data_importer.parse_match_list(
        __file__, "data/2022cctest_matches.json"
    )
    organized_matches = MatchHelper.organized_matches(matches)[1]
    advancement = PlayoffAdvancementHelper.generate_playoff_advancement(
        event, organized_matches
    )
    assert advancement.bracket_table is not None
    assert advancement.playoff_advancement is None
    assert advancement.double_elim_matches is not None
    assert advancement.playoff_template is None
