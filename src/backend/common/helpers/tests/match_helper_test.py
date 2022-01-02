import json
import random

import pytest
from google.appengine.ext import ndb

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import DoubleElimBracket
from backend.common.helpers.match_helper import MatchHelper
from backend.common.models.event import Event
from backend.common.models.match import Match


@pytest.fixture(autouse=True)
def auto_add_ndb_context(ndb_context) -> None:
    pass


def test_natural_sorted_matches(test_data_importer) -> None:
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )

    random.shuffle(matches)
    matches = MatchHelper.natural_sorted_matches(matches)
    # Spot check - f, qf, qm, sf. Matches in comp level should be in order
    spot_check_indexes = [0, 1, 2, 3, 4, 13, 14, 90, 91, 92]
    spot_check_match_keys = [matches[i].key_name for i in spot_check_indexes]
    expected_match_keys = [
        "2019nyny_f1m1",
        "2019nyny_f1m2",
        "2019nyny_qf1m1",
        "2019nyny_qf1m2",
        "2019nyny_qf2m1",
        "2019nyny_qm1",
        "2019nyny_qm2",
        "2019nyny_sf1m1",
        "2019nyny_sf1m2",
        "2019nyny_sf2m1",
    ]
    assert spot_check_match_keys == expected_match_keys


def test_organized_matches_counts(test_data_importer) -> None:
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )

    count, organized_matches = MatchHelper.organized_matches(matches)
    assert count == 94
    assert len(organized_matches[CompLevel.QM]) == 77
    assert len(organized_matches[CompLevel.QF]) == 11
    assert len(organized_matches[CompLevel.EF]) == 0
    assert len(organized_matches[CompLevel.SF]) == 4
    assert len(organized_matches[CompLevel.F]) == 2


def test_organized_matches_sorted(test_data_importer) -> None:
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )

    _, organized_matches = MatchHelper.organized_matches(matches)
    quals = organized_matches[CompLevel.QM]
    quarters = organized_matches[CompLevel.QF]
    assert all(
        quals[i].match_number <= quals[i + 1].match_number
        for i in range(len(quals) - 1)
    )
    assert all(
        quarters[i].set_number <= quarters[i + 1].set_number
        for i in range(len(quarters) - 1)
    )


def test_organized_double_elim_matches(test_data_importer) -> None:
    matches = test_data_importer.parse_match_list(
        __file__, "data/2017wiwi_matches.json"
    )

    _, organized_matches = MatchHelper.organized_matches(matches)
    double_elim_matches = MatchHelper.organized_double_elim_matches(organized_matches)

    assert DoubleElimBracket.WINNER in double_elim_matches
    assert DoubleElimBracket.LOSER in double_elim_matches

    assert all(
        level in double_elim_matches[DoubleElimBracket.WINNER]
        for level in [CompLevel.EF, CompLevel.QF, CompLevel.SF, CompLevel.F]
    )
    assert all(
        level in double_elim_matches[DoubleElimBracket.LOSER]
        for level in [CompLevel.EF, CompLevel.QF, CompLevel.SF, CompLevel.F]
    )


def test_play_order_sort(test_data_importer) -> None:
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    sorted_matches = MatchHelper.play_order_sorted_matches(matches)
    assert len(sorted_matches) == 94
    assert all(
        sorted_matches[i].play_order <= sorted_matches[i + 1].play_order
        for i in range(len(sorted_matches) - 1)
    )


def test_recent_matches(test_data_importer) -> None:
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    quals = [m for m in matches if m.comp_level == CompLevel.QM]
    for m in quals:
        if m.match_number > 70:
            m.alliances[AllianceColor.RED]["score"] = -1
            m.alliances[AllianceColor.BLUE]["score"] = -1
            m.alliances_json = json.dumps(m.alliances)
            m._alliances = None

    recent_matches = MatchHelper.recent_matches(quals, num=3)
    assert [m.key_name for m in recent_matches] == [
        "2019nyny_qm68",
        "2019nyny_qm69",
        "2019nyny_qm70",
    ]


def test_recent_matches_none_played(test_data_importer) -> None:
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    quals = [m for m in matches if m.comp_level == CompLevel.QM]
    for m in quals:
        m.alliances[AllianceColor.RED]["score"] = -1
        m.alliances[AllianceColor.BLUE]["score"] = -1
        m.alliances_json = json.dumps(m.alliances)
        m._alliances = None

    recent_matches = MatchHelper.recent_matches(quals, num=3)
    assert recent_matches == []


def test_upcoming_matches(test_data_importer) -> None:
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    quals = [m for m in matches if m.comp_level == CompLevel.QM]
    for m in quals:
        if m.match_number > 70:
            m.alliances[AllianceColor.RED]["score"] = -1
            m.alliances[AllianceColor.BLUE]["score"] = -1
            m.alliances_json = json.dumps(m.alliances)
            m._alliances = None

    upcoming_matches = MatchHelper.upcoming_matches(quals, num=3)
    assert [m.key_name for m in upcoming_matches] == [
        "2019nyny_qm71",
        "2019nyny_qm72",
        "2019nyny_qm73",
    ]


def test_upcoming_matches_all_played(test_data_importer) -> None:
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    quals = [m for m in matches if m.comp_level == CompLevel.QM]

    upcoming_matches = MatchHelper.upcoming_matches(quals, num=3)
    assert upcoming_matches == []


def test_cleanup_matches(ndb_stub, test_data_importer):
    event = Event(
        id="2013test",
        event_short="test",
        year=2013,
        event_type_enum=EventType.REGIONAL,
    )
    event.put()

    played = [
        {"red": {"score": 5}, "blue": {"score": 0}},
        {"red": {"score": 5}, "blue": {"score": 20}},
        {"red": {"score": 5}, "blue": {"score": 0}},
    ]
    unplayed = {"red": {"score": -1}, "blue": {"score": -1}}

    matches = [
        Match(
            id=f"2013test_qf1m{i}",
            comp_level=CompLevel.QF,
            set_number=1,
            match_number=i,
            event=ndb.Key(Event, "2013test"),
            alliances_json=json.dumps(played[i - 1] if i < 4 else unplayed),
        )
        for i in range(1, 6)
    ]

    cleaned_matches, keys_to_delete = MatchHelper.delete_invalid_matches(matches, event)
    assert [m.key_name for m in cleaned_matches] == [
        "2013test_qf1m1",
        "2013test_qf1m2",
        "2013test_qf1m3",
    ]
    assert [k.id() for k in keys_to_delete] == ["2013test_qf1m4", "2013test_qf1m5"]
