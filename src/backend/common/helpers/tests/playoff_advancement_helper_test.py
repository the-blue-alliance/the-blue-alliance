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
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    organized_matches = MatchHelper.organized_matches(matches)[1]

    advancement = PlayoffAdvancementHelper.generatePlayoffAdvancement(
        event, organized_matches
    )
    assert advancement.bracket_table is not None
    assert advancement.playoff_advancement is None
    assert advancement.double_elim_matches is None
    assert advancement.playoff_template is None


def test_2015_event(test_data_importer) -> None:
    event = create_event("2015nyny", PlayoffType.AVG_SCORE_8_TEAM)
    matches = test_data_importer.parse_match_list(
        __file__, "data/2015nyny_matches.json"
    )
    organized_matches = MatchHelper.organized_matches(matches)[1]

    advancement = PlayoffAdvancementHelper.generatePlayoffAdvancement(
        event, organized_matches
    )
    assert advancement.bracket_table is not None
    assert advancement.playoff_advancement is not None
    assert advancement.double_elim_matches is None
    assert advancement.playoff_template == "playoff_table"


def test_round_robin(test_data_importer) -> None:
    event = create_event("2019cmptx", PlayoffType.ROUND_ROBIN_6_TEAM)
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019cmptx_matches.json"
    )
    organized_matches = MatchHelper.organized_matches(matches)[1]

    advancement = PlayoffAdvancementHelper.generatePlayoffAdvancement(
        event, organized_matches
    )
    assert advancement.bracket_table is not None
    assert advancement.playoff_advancement is not None
    assert advancement.double_elim_matches is None
    assert advancement.playoff_template == "playoff_round_robin_6_team"


def test_best_of_3_finals(test_data_importer) -> None:
    event = create_event("2019nyny", PlayoffType.BO3_FINALS)
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    organized_matches = MatchHelper.organized_matches(matches)[1]

    advancement = PlayoffAdvancementHelper.generatePlayoffAdvancement(
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

    advancement = PlayoffAdvancementHelper.generatePlayoffAdvancement(
        event, organized_matches
    )
    assert advancement.bracket_table is not None
    assert advancement.playoff_advancement is None
    assert advancement.double_elim_matches is None
    assert advancement.playoff_template is None
