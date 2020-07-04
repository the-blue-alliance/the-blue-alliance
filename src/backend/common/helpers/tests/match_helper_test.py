import json

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.helpers.match_helper import MatchHelper


def test_organize_matches_counts(test_data_importer) -> None:
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )

    count, organized_matches = MatchHelper.organizeMatches(matches)
    assert count == 94
    assert len(organized_matches[CompLevel.QM]) == 77
    assert len(organized_matches[CompLevel.QF]) == 11
    assert len(organized_matches[CompLevel.EF]) == 0
    assert len(organized_matches[CompLevel.SF]) == 4
    assert len(organized_matches[CompLevel.F]) == 2


def test_organize_matches_sorted(test_data_importer) -> None:
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )

    _, organized_matches = MatchHelper.organizeMatches(matches)
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


def test_play_order_sort(test_data_importer) -> None:
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    sorted_matches = MatchHelper.play_order_sort_matches(matches)
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

    recent_matches = MatchHelper.recentMatches(quals, num=3)
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

    recent_matches = MatchHelper.recentMatches(quals, num=3)
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

    upcoming_matches = MatchHelper.upcomingMatches(quals, num=3)
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

    upcoming_matches = MatchHelper.upcomingMatches(quals, num=3)
    assert upcoming_matches == []
