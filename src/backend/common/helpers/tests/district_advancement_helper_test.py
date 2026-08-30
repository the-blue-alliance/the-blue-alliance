import json
from typing import Dict, List, Set

import pytest
from google.appengine.ext import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.district_advancement_helper import (
    DistrictAdvancementHelper,
)
from backend.common.models.award import Award
from backend.common.models.district import District
from backend.common.models.district_ranking import DistrictRanking
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_district_points import TeamAtEventDistrictPoints
from backend.common.models.keys import EventKey, TeamKey
from backend.common.models.team import Team


def _points(
    event_key: EventKey,
    *,
    district_cmp: bool = False,
    qual: int = 0,
    elim: int = 0,
    alliance: int = 0,
    award: int = 0,
) -> TeamAtEventDistrictPoints:
    return TeamAtEventDistrictPoints(
        event_key=event_key,
        district_cmp=district_cmp,
        qual_points=qual,
        elim_points=elim,
        alliance_points=alliance,
        award_points=award,
        total=qual + elim + alliance + award,
    )


def _ranking(
    rank: int,
    team_key: TeamKey,
    *event_points: TeamAtEventDistrictPoints,
    rookie_bonus: int = 0,
    adjustments: int = 0,
) -> DistrictRanking:
    ranking = DistrictRanking(
        rank=rank,
        team_key=team_key,
        point_total=sum(ep["total"] for ep in event_points)
        + rookie_bonus
        + adjustments,
        rookie_bonus=rookie_bonus,
        event_points=list(event_points),
    )
    if adjustments:
        ranking["adjustments"] = adjustments
    return ranking


def _descending_rankings(count: int, top_points: int = 100) -> List[DistrictRanking]:
    return [
        _ranking(i + 1, f"frc{i + 1}", _points("2026qual", qual=top_points - i))
        for i in range(count)
    ]


def _team_keys(*numbers: int) -> Set[TeamKey]:
    return {f"frc{n}" for n in numbers}


def test_no_declines_effective_matches_original() -> None:
    rankings = _descending_rankings(10)

    cutoffs = DistrictAdvancementHelper.calculate_dcmp_cutoffs(
        rankings, slots=5, auto_qualified=set(), attendance=_team_keys(1, 2, 3, 4, 5)
    )

    assert cutoffs.original == 96
    assert cutoffs.effective == 96
    assert cutoffs.declined == []


def test_decline_passes_slot_down() -> None:
    rankings = _descending_rankings(10)

    cutoffs = DistrictAdvancementHelper.calculate_dcmp_cutoffs(
        rankings, slots=5, auto_qualified=set(), attendance=_team_keys(1, 3, 4, 5, 6)
    )

    assert cutoffs.original == 96
    assert cutoffs.effective == 95
    assert cutoffs.declined == ["frc2"]


def test_award_winner_below_cutoff_consumes_a_slot() -> None:
    rankings = _descending_rankings(10)

    cutoffs = DistrictAdvancementHelper.calculate_dcmp_cutoffs(
        rankings,
        slots=5,
        auto_qualified=_team_keys(8),
        attendance=_team_keys(1, 2, 3, 4, 8),
    )

    assert cutoffs.original == 97
    assert cutoffs.effective == 97
    assert cutoffs.declined == []


def test_award_winner_above_cutoff_changes_nothing() -> None:
    rankings = _descending_rankings(10)

    cutoffs = DistrictAdvancementHelper.calculate_dcmp_cutoffs(
        rankings,
        slots=5,
        auto_qualified=_team_keys(2),
        attendance=_team_keys(1, 2, 3, 4, 5),
    )

    assert cutoffs.original == 96
    assert cutoffs.effective == 96
    assert cutoffs.declined == []


def test_award_winner_below_cutoff_does_not_lower_effective() -> None:
    rankings = _descending_rankings(10)

    cutoffs = DistrictAdvancementHelper.calculate_dcmp_cutoffs(
        rankings,
        slots=4,
        auto_qualified=_team_keys(9),
        attendance=_team_keys(1, 2, 3, 9),
    )

    assert cutoffs.original == 98
    assert cutoffs.effective == 98


def test_more_slots_than_teams() -> None:
    rankings = _descending_rankings(10)

    cutoffs = DistrictAdvancementHelper.calculate_dcmp_cutoffs(
        rankings, slots=20, auto_qualified=set(), attendance=_team_keys(*range(1, 11))
    )

    assert cutoffs.original == 91
    assert cutoffs.effective == 91


def test_no_attendance_yields_zero_effective() -> None:
    rankings = _descending_rankings(10)

    cutoffs = DistrictAdvancementHelper.calculate_dcmp_cutoffs(
        rankings, slots=5, auto_qualified=set(), attendance=set()
    )

    assert cutoffs.original == 96
    assert cutoffs.effective == 0
    assert cutoffs.declined == []


def test_attendance_ignores_award_only_dcmp_entry() -> None:
    competed = _ranking(
        1,
        "frc1",
        _points("2026qual", qual=50),
        _points("2026necmp1", district_cmp=True, qual=24),
    )
    award_only = _ranking(
        2,
        "frc2",
        _points("2026qual", qual=40),
        _points("2026necmp", district_cmp=True, award=24),
    )
    no_dcmp = _ranking(3, "frc3", _points("2026qual", qual=30))

    attendance = DistrictAdvancementHelper.dcmp_attendance(
        [competed, award_only, no_dcmp]
    )

    assert attendance == {"frc1"}


def test_attendance_counts_elim_only_finals_entry() -> None:
    finals_only = _ranking(
        1,
        "frc1",
        _points("2026qual", qual=50),
        _points("2026necmp", district_cmp=True, elim=30),
    )

    assert DistrictAdvancementHelper.dcmp_attendance([finals_only]) == {"frc1"}


def test_pre_dcmp_rankings_reorders_after_removing_dcmp_points() -> None:
    boosted_by_dcmp = _ranking(
        1,
        "frc1",
        _points("2026qual", qual=50),
        _points("2026necmp1", district_cmp=True, qual=30),
    )
    stronger_in_quals = _ranking(
        2,
        "frc2",
        _points("2026qual", qual=60),
        _points("2026necmp1", district_cmp=True, qual=5),
    )

    pre_dcmp = DistrictAdvancementHelper.pre_dcmp_rankings(
        [boosted_by_dcmp, stronger_in_quals]
    )

    assert [(r["rank"], r["team_key"], r["point_total"]) for r in pre_dcmp] == [
        (1, "frc2", 60),
        (2, "frc1", 50),
    ]
    assert all(not ep.get("district_cmp") for r in pre_dcmp for ep in r["event_points"])


def test_pre_dcmp_rankings_preserves_bonuses() -> None:
    ranking = _ranking(
        1,
        "frc1",
        _points("2026qual", qual=50),
        _points("2026necmp1", district_cmp=True, qual=30),
        rookie_bonus=10,
        adjustments=5,
    )

    pre_dcmp = DistrictAdvancementHelper.pre_dcmp_rankings([ranking])[0]

    assert pre_dcmp["point_total"] == 65
    assert pre_dcmp["rookie_bonus"] == 10
    assert pre_dcmp["adjustments"] == 5


def test_pre_dcmp_rankings_breaks_ties_on_playoff_points() -> None:
    fewer_playoff_points = _ranking(
        1, "frc1", _points("2026qual", qual=50, elim=0), _points("2026b", qual=10)
    )
    more_playoff_points = _ranking(
        2, "frc2", _points("2026qual", qual=30, elim=20), _points("2026b", qual=10)
    )

    pre_dcmp = DistrictAdvancementHelper.pre_dcmp_rankings(
        [fewer_playoff_points, more_playoff_points]
    )

    assert [r["team_key"] for r in pre_dcmp] == ["frc2", "frc1"]


def test_pre_dcmp_rankings_breaks_ties_on_highest_match_score() -> None:
    pre_dcmp = DistrictAdvancementHelper.pre_dcmp_rankings(
        [
            _ranking(1, "frc1", _points("2026qual", qual=20)),
            _ranking(2, "frc2", _points("2026qual", qual=20)),
        ],
        {"2026qual": {"frc1": [300, 200, 100], "frc2": [400, 100, 50]}},
    )

    assert [r["team_key"] for r in pre_dcmp] == ["frc2", "frc1"]


def test_pre_dcmp_rankings_breaks_ties_on_second_highest_match_score() -> None:
    pre_dcmp = DistrictAdvancementHelper.pre_dcmp_rankings(
        [
            _ranking(1, "frc1", _points("2026qual", qual=20)),
            _ranking(2, "frc2", _points("2026qual", qual=20)),
        ],
        {"2026qual": {"frc1": [400, 200, 100], "frc2": [400, 300, 50]}},
    )

    assert [r["team_key"] for r in pre_dcmp] == ["frc2", "frc1"]


def test_pre_dcmp_rankings_ignores_dcmp_match_scores() -> None:
    pre_dcmp = DistrictAdvancementHelper.pre_dcmp_rankings(
        [
            _ranking(
                1,
                "frc1",
                _points("2026qual", qual=20),
                _points("2026necmp", district_cmp=True, qual=50),
            ),
            _ranking(
                2,
                "frc2",
                _points("2026qual", qual=20),
                _points("2026necmp", district_cmp=True, qual=50),
            ),
        ],
        {
            "2026qual": {"frc1": [100], "frc2": [200]},
            "2026necmp": {"frc1": [999], "frc2": [0]},
        },
    )

    assert [r["team_key"] for r in pre_dcmp] == ["frc2", "frc1"]


def _load(test_data_importer, filename: str):
    with open(test_data_importer._get_path(__file__, f"data/{filename}")) as f:
        return json.load(f)


def _setup_district(test_data_importer, district_key: str) -> District:
    year = int(district_key[:4])
    rankings = _load(test_data_importer, f"{district_key}_rankings.json")
    awards = _load(test_data_importer, f"{district_key}_awards.json")

    district = District(id=district_key, year=year, abbreviation=district_key[4:])
    district.rankings = rankings
    district.put()

    district_points = _load(test_data_importer, f"{district_key}_district_points.json")

    events: Dict[EventKey, Event] = {}
    for event_data in _load(test_data_importer, f"{district_key}_events.json"):
        event_key = event_data["key"]
        event = Event(
            id=event_key,
            year=year,
            event_short=event_data["event_code"],
            event_type_enum=EventType(event_data["event_type"]),
            district_key=district.key,
        )
        event.put()
        EventDetails(id=event_key, district_points=district_points[event_key]).put()
        events[event_key] = event

    for award in awards:
        event = events[award["event_key"]]
        Award(
            id=Award.render_key_name(award["event_key"], award["award_type"]),
            name_str=award["name"],
            award_type_enum=award["award_type"],
            year=year,
            event=event.key,
            event_type_enum=event.event_type_enum,
            team_list=[
                ndb.Key(Team, recipient["team_key"])
                for recipient in award["recipient_list"]
                if recipient["team_key"]
            ],
        ).put()

    return district


def test_2026ne_impact_winners(ndb_stub, test_data_importer) -> None:
    district = _setup_district(test_data_importer, "2026ne")
    events = Event.query(Event.district_key == district.key).fetch()

    winners = DistrictAdvancementHelper.impact_award_winners(events)

    assert winners == {
        "frc131",
        "frc1350",
        "frc173",
        "frc190",
        "frc195",
        "frc2079",
        "frc2170",
        "frc2370",
        "frc2877",
        "frc4905",
        "frc6328",
        "frc8046",
    }


def test_impact_winners_only_count_district_qualifying_events(ndb_stub) -> None:
    district = District(id="2026ne", year=2026, abbreviation="ne")
    district.put()

    events = []
    for team_number, (event_key, event_type) in enumerate(
        [
            ("2026qual", EventType.DISTRICT),
            ("2026necmp1", EventType.DISTRICT_CMP_DIVISION),
            ("2026necmp", EventType.DISTRICT_CMP),
            ("2026reg", EventType.REGIONAL),
            ("2026off", EventType.OFFSEASON),
            ("2026pre", EventType.PRESEASON),
        ],
        start=1,
    ):
        event = Event(
            id=event_key,
            year=2026,
            event_short=event_key[4:],
            event_type_enum=event_type,
            district_key=district.key,
        )
        event.put()
        events.append(event)
        Award(
            id=Award.render_key_name(event_key, AwardType.CHAIRMANS),
            name_str="FIRST Impact Award",
            award_type_enum=AwardType.CHAIRMANS,
            year=2026,
            event=event.key,
            event_type_enum=event_type,
            team_list=[ndb.Key(Team, f"frc{team_number}")],
        ).put()

    assert DistrictAdvancementHelper.impact_award_winners(events) == {"frc1"}


@pytest.mark.parametrize(
    "district_key,expected_attendance",
    [("2026ne", 100), ("2026ont", 99), ("2026fim", 161), ("2026fit", 90)],
)
def test_attendance_matches_division_rosters(
    district_key: str, expected_attendance: int, ndb_stub, test_data_importer
) -> None:
    district = _setup_district(test_data_importer, district_key)

    attendance = DistrictAdvancementHelper.dcmp_attendance(district.rankings)

    assert len(attendance) == expected_attendance


def test_2026ne_attendance_excludes_award_only_teams(
    ndb_stub, test_data_importer
) -> None:
    district = _setup_district(test_data_importer, "2026ne")

    attendance = DistrictAdvancementHelper.dcmp_attendance(district.rankings)

    assert "frc11269" not in attendance
    assert "frc999" not in attendance


EXPECTED_CUTOFFS = {
    "2026ne": {
        "dcmp_original": 53,
        "dcmp_effective": 46,
        "dcmp_declines": [
            "frc6153",
            "frc4572",
            "frc9055",
            "frc429",
            "frc4473",
            "frc1307",
            "frc11157",
            "frc4564",
            "frc69",
            "frc1277",
            "frc237",
        ],
        "cmp_original": 0,
        "cmp_effective": 0,
        "cmp_declines": [],
    },
    "2026ont": {
        "dcmp_original": 31,
        "dcmp_effective": 15,
        "dcmp_declines": [
            "frc6135",
            "frc11362",
            "frc6397",
            "frc6110",
            "frc11215",
            "frc5912",
            "frc4617",
            "frc6864",
            "frc8081",
            "frc6854",
            "frc8850",
            "frc6725",
            "frc6859",
            "frc7603",
            "frc4940",
            "frc4015",
            "frc7058",
            "frc8764",
        ],
        "cmp_original": 0,
        "cmp_effective": 0,
        "cmp_declines": [],
    },
    "2026fim": {
        "dcmp_original": 64,
        "dcmp_effective": 64,
        "dcmp_declines": [],
        "cmp_original": 0,
        "cmp_effective": 0,
        "cmp_declines": [],
    },
    "2026fit": {
        "dcmp_original": 54,
        "dcmp_effective": 53,
        "dcmp_declines": ["frc8515", "frc436", "frc10118", "frc8573"],
        "cmp_original": 0,
        "cmp_effective": 0,
        "cmp_declines": [],
    },
}


@pytest.mark.parametrize("district_key", sorted(EXPECTED_CUTOFFS))
def test_district_cutoffs(district_key: str, ndb_stub, test_data_importer) -> None:
    district = _setup_district(test_data_importer, district_key)
    events = Event.query(Event.district_key == district.key).fetch()

    cutoffs = DistrictAdvancementHelper.calculate_for_district(district, events)

    assert cutoffs == EXPECTED_CUTOFFS[district_key]


def test_no_dcmp_attendance_returns_none(ndb_stub) -> None:
    district = District(id="2026ne", year=2026, abbreviation="ne")
    district.rankings = _descending_rankings(10)
    district.put()

    assert DistrictAdvancementHelper.calculate_for_district(district, []) is None


def test_no_rankings_returns_none(ndb_stub) -> None:
    district = District(id="2026ne", year=2026, abbreviation="ne")
    district.put()

    assert DistrictAdvancementHelper.calculate_for_district(district, []) is None
