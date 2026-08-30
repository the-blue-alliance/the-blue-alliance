import datetime
import json
from typing import Dict, List, Set
from unittest import mock

import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.award_type import AwardType
from backend.common.consts.cmp_qualification import (
    CMP_QUALIFICATION_RULES,
    CmpQualificationMethod,
    HALL_OF_FAME_TEAMS_BY_YEAR,
)
from backend.common.consts.event_type import EventType
from backend.common.helpers.district_advancement_helper import (
    Cutoffs,
    DistrictAdvancementHelper,
    NO_POINTS_CUTOFF,
)
from backend.common.models.award import Award
from backend.common.models.district import District
from backend.common.models.district_advancement import DistrictAdvancementCutoffs
from backend.common.models.district_ranking import DistrictRanking
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_district_points import TeamAtEventDistrictPoints
from backend.common.models.event_team import EventTeam
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


def _dcmp_cutoffs(
    rankings: List[DistrictRanking],
    slots: int,
    auto_qualified: Set[TeamKey],
    attendance: Set[TeamKey],
) -> Cutoffs:
    return DistrictAdvancementHelper.calculate_cutoffs(
        rankings,
        slots,
        auto_qualified,
        set(),
        attendance,
        cap_to_slots=False,
    )


def _cmp_cutoffs(
    rankings: List[DistrictRanking],
    slots: int,
    consuming: Set[TeamKey],
    non_consuming: Set[TeamKey],
    attendance: Set[TeamKey],
) -> Cutoffs:
    return DistrictAdvancementHelper.calculate_cutoffs(
        rankings,
        slots,
        consuming,
        non_consuming,
        attendance,
        cap_to_slots=True,
    )


def test_no_declines_effective_matches_original() -> None:
    rankings = _descending_rankings(10)

    cutoffs = _dcmp_cutoffs(
        rankings, slots=5, auto_qualified=set(), attendance=_team_keys(1, 2, 3, 4, 5)
    )

    assert cutoffs.original == 96
    assert cutoffs.effective == 96
    assert cutoffs.declined == []


def test_decline_passes_slot_down() -> None:
    rankings = _descending_rankings(10)

    cutoffs = _dcmp_cutoffs(
        rankings, slots=5, auto_qualified=set(), attendance=_team_keys(1, 3, 4, 5, 6)
    )

    assert cutoffs.original == 96
    assert cutoffs.effective == 95
    assert cutoffs.declined == ["frc2"]


def test_award_winner_below_cutoff_consumes_a_slot() -> None:
    rankings = _descending_rankings(10)

    cutoffs = _dcmp_cutoffs(
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

    cutoffs = _dcmp_cutoffs(
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

    cutoffs = _dcmp_cutoffs(
        rankings,
        slots=4,
        auto_qualified=_team_keys(9),
        attendance=_team_keys(1, 2, 3, 9),
    )

    assert cutoffs.original == 98
    assert cutoffs.effective == 98


def test_more_slots_than_teams() -> None:
    rankings = _descending_rankings(10)

    cutoffs = _dcmp_cutoffs(
        rankings, slots=20, auto_qualified=set(), attendance=_team_keys(*range(1, 11))
    )

    assert cutoffs.original == 91
    assert cutoffs.effective == 91


def test_no_attendance_yields_zero_effective() -> None:
    rankings = _descending_rankings(10)

    cutoffs = _dcmp_cutoffs(rankings, slots=5, auto_qualified=set(), attendance=set())

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


def _date(value: str) -> datetime.datetime:
    return datetime.datetime.strptime(value, "%Y-%m-%d")


def _expected_qualification(
    test_data_importer, district_key: str
) -> Dict[TeamKey, str]:
    grouped = _load(test_data_importer, "cmp_qualification.json")[district_key]
    return {
        team_key: method
        for method, team_keys in grouped.items()
        for team_key in team_keys
    }


def _group_by_method(
    qualification: Dict[TeamKey, CmpQualificationMethod],
) -> Dict[str, List[TeamKey]]:
    grouped: Dict[str, List[TeamKey]] = {}
    for team_key, method in qualification.items():
        grouped.setdefault(method.value, []).append(team_key)
    return {
        method: sorted(team_keys, key=lambda t: int(t[3:]))
        for method, team_keys in sorted(grouped.items())
    }


def _setup_cmp(test_data_importer, year: int) -> None:
    for event_key, team_keys in _load(
        test_data_importer, f"{year}_cmp_division_teams.json"
    ).items():
        event = Event(
            id=event_key,
            year=year,
            event_short=event_key[4:],
            event_type_enum=EventType.CMP_DIVISION,
            official=True,
        )
        event.put()
        for team_key in team_keys:
            EventTeam(
                id=f"{event_key}_{team_key}",
                event=event.key,
                team=ndb.Key(Team, team_key),
                year=year,
            ).put()

    regional_events: Dict[EventKey, Event] = {}
    for event_data in _load(test_data_importer, f"{year}_regional_events.json"):
        event = Event(
            id=event_data["key"],
            year=year,
            event_short=event_data["event_code"],
            event_type_enum=EventType.REGIONAL,
            official=True,
            start_date=_date(event_data["start_date"]),
            end_date=_date(event_data["end_date"]),
        )
        event.put()
        regional_events[event_data["key"]] = event

    for award in _load(test_data_importer, f"{year}_regional_awards.json"):
        _put_award(
            year, regional_events[award["event_key"]].key, EventType.REGIONAL, award
        )

    for award in _load(test_data_importer, "cmp_finals_awards.json"):
        _put_award(
            award["year"],
            ndb.Key(Event, award["event_key"]),
            EventType(award["event_type"]),
            award,
        )


def _put_award(
    year: int, event_key: ndb.Key, event_type: EventType, award: Dict
) -> None:
    Award(
        id=Award.render_key_name(
            none_throws(event_key.string_id()), award["award_type"]
        ),
        name_str=award["name"],
        award_type_enum=award["award_type"],
        year=year,
        event=event_key,
        event_type_enum=event_type,
        team_list=[ndb.Key(Team, team_key) for team_key in award["team_keys"]],
    ).put()


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
            official=True,
            start_date=_date(event_data["start_date"]),
            end_date=_date(event_data["end_date"]),
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
    [
        ("2022ne", 78),
        ("2025ne", 96),
        ("2025fim", 160),
        ("2025fit", 90),
        ("2026ne", 100),
        ("2026ont", 99),
        ("2026fim", 161),
        ("2026fit", 90),
    ],
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
    "2022fin": {
        "dcmp_original": 45,
        "dcmp_effective": 45,
        "dcmp_declines": [],
        "cmp_original": -1,
        "cmp_effective": 311,
        "cmp_declines": [],
    },
    "2022ne": {
        "dcmp_original": 51,
        "dcmp_effective": 39,
        "dcmp_declines": [
            "frc6328",
            "frc5813",
            "frc7407",
            "frc2168",
            "frc3467",
            "frc125",
            "frc236",
            "frc69",
            "frc138",
            "frc8709",
            "frc8013",
            "frc7127",
            "frc157",
            "frc151",
            "frc3451",
            "frc3958",
            "frc3464",
            "frc1058",
            "frc121",
            "frc2423",
            "frc4906",
            "frc6731",
            "frc1721",
            "frc999",
            "frc1512",
            "frc8604",
            "frc4311",
            "frc571",
            "frc7907",
        ],
        "cmp_original": 188,
        "cmp_effective": 88,
        "cmp_declines": [
            "frc238",
            "frc133",
            "frc6329",
            "frc95",
            "frc131",
            "frc5687",
            "frc319",
            "frc1768",
            "frc2370",
            "frc5846",
            "frc228",
            "frc4048",
            "frc78",
            "frc4564",
            "frc6153",
            "frc2067",
            "frc126",
            "frc2877",
            "frc172",
            "frc3146",
            "frc58",
            "frc237",
            "frc1757",
            "frc1071",
            "frc1027",
            "frc175",
            "frc6933",
            "frc1699",
            "frc8724",
            "frc2342",
            "frc558",
            "frc1100",
            "frc1740",
            "frc2648",
            "frc155",
            "frc8544",
            "frc2713",
            "frc509",
            "frc467",
            "frc5563",
            "frc2262",
            "frc5112",
            "frc716",
            "frc3205",
            "frc8889",
            "frc8046",
            "frc1922",
            "frc663",
        ],
    },
    "2018fim": {
        "dcmp_original": 66,
        "dcmp_effective": 65,
        "dcmp_declines": [
            "frc7218",
            "frc7154",
        ],
        "cmp_original": 142,
        "cmp_effective": 141,
        "cmp_declines": [],
    },
    "2019ne": {
        "dcmp_original": 69,
        "dcmp_effective": 64,
        "dcmp_declines": [
            "frc190",
            "frc126",
            "frc6161",
            "frc4929",
            "frc2876",
            "frc4564",
            "frc236",
            "frc131",
        ],
        "cmp_original": 136,
        "cmp_effective": 126,
        "cmp_declines": [
            "frc95",
            "frc69",
            "frc238",
            "frc4761",
            "frc4041",
            "frc7127",
            "frc7416",
        ],
    },
    "2024ne": {
        "dcmp_original": 50,
        "dcmp_effective": 49,
        "dcmp_declines": [
            "frc9732",
        ],
        "cmp_original": 195,
        "cmp_effective": 181,
        "cmp_declines": [
            "frc133",
            "frc1699",
        ],
    },
    "2025ne": {
        "dcmp_original": 48,
        "dcmp_effective": 46,
        "dcmp_declines": [
            "frc1512",
            "frc5902",
            "frc6933",
            "frc69",
            "frc429",
            "frc4546",
            "frc1277",
            "frc3323",
        ],
        "cmp_original": 175,
        "cmp_effective": 139,
        "cmp_declines": [
            "frc5687",
            "frc133",
            "frc1100",
            "frc138",
            "frc1699",
            "frc9443",
            "frc8013",
            "frc8085",
            "frc95",
            "frc9644",
            "frc131",
        ],
    },
    "2025fim": {
        "dcmp_original": 67,
        "dcmp_effective": 66,
        "dcmp_declines": [
            "frc5559",
            "frc7782",
            "frc4004",
            "frc9618",
        ],
        "cmp_original": 163,
        "cmp_effective": 152,
        "cmp_declines": [
            "frc1918",
            "frc5675",
            "frc5505",
            "frc5114",
            "frc7174",
            "frc3546",
            "frc1025",
            "frc1189",
            "frc1684",
        ],
    },
    "2025fit": {
        "dcmp_original": 54,
        "dcmp_effective": 53,
        "dcmp_declines": [
            "frc10118",
            "frc1164",
            "frc7540",
            "frc8515",
            "frc4251",
        ],
        "cmp_original": 202,
        "cmp_effective": 202,
        "cmp_declines": [],
    },
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
        "cmp_original": 191,
        "cmp_effective": 173,
        "cmp_declines": [
            "frc5687",
            "frc133",
            "frc4909",
            "frc1699",
            "frc236",
            "frc1153",
            "frc95",
        ],
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
        "cmp_original": 202,
        "cmp_effective": 183,
        "cmp_declines": [
            "frc610",
            "frc1360",
            "frc2702",
            "frc9098",
            "frc4039",
            "frc3161",
            "frc4069",
            "frc3683",
            "frc10554",
        ],
    },
    "2026fim": {
        "dcmp_original": 64,
        "dcmp_effective": 64,
        "dcmp_declines": [],
        "cmp_original": 155,
        "cmp_effective": 122,
        "cmp_declines": [
            "frc3668",
            "frc7197",
            "frc4237",
            "frc5114",
            "frc1918",
            "frc8517",
            "frc5660",
            "frc2611",
            "frc4398",
            "frc1188",
            "frc5675",
            "frc5843",
            "frc1481",
            "frc862",
            "frc123",
            "frc9215",
            "frc226",
            "frc9312",
            "frc5535",
            "frc3875",
            "frc85",
            "frc4779",
            "frc7056",
            "frc8352",
            "frc3767",
            "frc1502",
            "frc9210",
            "frc3357",
        ],
    },
    "2026fit": {
        "dcmp_original": 54,
        "dcmp_effective": 53,
        "dcmp_declines": ["frc8515", "frc436", "frc10118", "frc1164", "frc8573"],
        "cmp_original": 176,
        "cmp_effective": 176,
        "cmp_declines": [],
    },
}


@pytest.mark.parametrize("district_key", sorted(EXPECTED_CUTOFFS))
def test_district_cutoffs(district_key: str, ndb_stub, test_data_importer) -> None:
    district = _setup_district(test_data_importer, district_key)
    _setup_cmp(test_data_importer, district.year)
    events = Event.query(Event.district_key == district.key).fetch()

    cutoffs = DistrictAdvancementHelper.calculate_for_district(district, events)

    assert cutoffs == {
        **EXPECTED_CUTOFFS[district_key],
        "cmp_qualification": _expected_qualification(test_data_importer, district_key),
    }


CONFIRMED_2026NE_CMP_DECLINES = [
    "frc5687",
    "frc133",
    "frc4909",
    "frc1699",
    "frc236",
    "frc1153",
    "frc95",
]


def test_2026ne_cmp_declines_match_confirmed_list(ndb_stub, test_data_importer) -> None:
    district = _setup_district(test_data_importer, "2026ne")
    _setup_cmp(test_data_importer, district.year)
    events = Event.query(Event.district_key == district.key).fetch()

    cutoffs = none_throws(
        DistrictAdvancementHelper.calculate_for_district(district, events)
    )

    assert cutoffs["cmp_declines"] == CONFIRMED_2026NE_CMP_DECLINES


@pytest.mark.parametrize("district_key", sorted(EXPECTED_CUTOFFS))
def test_cmp_qualification_methods(
    district_key: str, ndb_stub, test_data_importer
) -> None:
    district = _setup_district(test_data_importer, district_key)
    _setup_cmp(test_data_importer, district.year)
    events = Event.query(Event.district_key == district.key).fetch()

    qualification = DistrictAdvancementHelper.cmp_qualification_methods(
        district, events
    )

    assert (
        _group_by_method(qualification)
        == _load(test_data_importer, "cmp_qualification.json")[district_key]
    )


def test_2024ne_waitlist(ndb_stub, test_data_importer) -> None:
    district = _setup_district(test_data_importer, "2024ne")
    _setup_cmp(test_data_importer, district.year)
    events = Event.query(Event.district_key == district.key).fetch()

    qualification = DistrictAdvancementHelper.cmp_qualification_methods(
        district, events
    )

    assert qualification["frc2713"] == CmpQualificationMethod.WAITLIST


def test_no_dcmp_attendance_returns_none(ndb_stub) -> None:
    district = District(id="2026ne", year=2026, abbreviation="ne")
    district.rankings = _descending_rankings(10)
    district.put()

    assert DistrictAdvancementHelper.calculate_for_district(district, []) is None


def test_no_rankings_returns_none(ndb_stub) -> None:
    district = District(id="2026ne", year=2026, abbreviation="ne")
    district.put()

    assert DistrictAdvancementHelper.calculate_for_district(district, []) is None


def test_non_consuming_qualifier_extends_the_points_line() -> None:
    rankings = _descending_rankings(10)

    cutoffs = _cmp_cutoffs(
        rankings,
        slots=5,
        consuming=set(),
        non_consuming=_team_keys(2),
        attendance=_team_keys(1, 2, 3, 4, 5, 6),
    )

    assert cutoffs.original == 95
    assert cutoffs.effective == 95
    assert cutoffs.declined == []


def test_consuming_qualifier_above_the_line_changes_nothing() -> None:
    rankings = _descending_rankings(10)

    cutoffs = _cmp_cutoffs(
        rankings,
        slots=5,
        consuming=_team_keys(2),
        non_consuming=set(),
        attendance=_team_keys(1, 2, 3, 4, 5),
    )

    assert cutoffs.original == 96
    assert cutoffs.effective == 96
    assert cutoffs.declined == []


def test_consuming_qualifier_below_the_line_raises_original() -> None:
    rankings = _descending_rankings(10)

    cutoffs = _cmp_cutoffs(
        rankings,
        slots=5,
        consuming=_team_keys(9),
        non_consuming=set(),
        attendance=_team_keys(1, 2, 3, 4, 9),
    )

    assert cutoffs.original == 97
    assert cutoffs.effective == 97
    assert cutoffs.declined == []


def test_cap_drops_surplus_attendee_as_waitlist() -> None:
    rankings = _descending_rankings(10)

    cutoffs = _cmp_cutoffs(
        rankings,
        slots=5,
        consuming=set(),
        non_consuming=set(),
        attendance=_team_keys(1, 2, 3, 4, 5, 9),
    )

    assert cutoffs.original == 96
    assert cutoffs.effective == 96
    assert cutoffs.declined == []


def test_uncapped_surplus_attendee_sets_effective() -> None:
    rankings = _descending_rankings(10)

    cutoffs = _dcmp_cutoffs(
        rankings, slots=5, auto_qualified=set(), attendance=_team_keys(1, 2, 3, 4, 5, 9)
    )

    assert cutoffs.original == 96
    assert cutoffs.effective == 92
    assert cutoffs.declined == ["frc6", "frc7", "frc8"]


@pytest.mark.parametrize(
    "method,year,expected",
    [
        (CmpQualificationMethod.WAITLIST, 1992, True),
        (CmpQualificationMethod.WAITLIST, 2026, True),
        (CmpQualificationMethod.HALL_OF_FAME, 1992, True),
        (CmpQualificationMethod.HALL_OF_FAME, 2026, True),
        (CmpQualificationMethod.DCMP_IMPACT, 2008, False),
        (CmpQualificationMethod.DCMP_IMPACT, 2009, True),
        (CmpQualificationMethod.DCMP_WINNER, 2026, True),
    ],
)
def test_rule_year_ranges(
    method: CmpQualificationMethod, year: int, expected: bool
) -> None:
    assert CMP_QUALIFICATION_RULES[method].applies_to(year) == expected


def test_hall_of_fame_derives_every_prior_induction(
    ndb_stub, test_data_importer
) -> None:
    _setup_cmp(test_data_importer, 2026)

    everyone = DistrictAdvancementHelper.hall_of_fame_teams(2026)

    assert {"frc2834", "frc2614", "frc5985"} <= everyone
    assert "frc5985" not in DistrictAdvancementHelper.hall_of_fame_teams(2025)


def test_hall_of_fame_year_lists_are_used_verbatim(
    ndb_stub, test_data_importer
) -> None:
    _setup_cmp(test_data_importer, 2026)
    district = District(id="2026ne", year=2026, abbreviation="ne")
    district.put()

    with mock.patch.dict(
        HALL_OF_FAME_TEAMS_BY_YEAR, {2026: {"frc2834", "frc503"}}, clear=False
    ):
        derived = DistrictAdvancementHelper.cmp_qualifiers_by_method(district, [])

    assert derived[CmpQualificationMethod.HALL_OF_FAME] == {"frc2834", "frc503"}
    assert "frc2614" in DistrictAdvancementHelper.hall_of_fame_teams(2026)


def test_hall_of_fame_pre_manual_era_uses_derived_list(
    ndb_stub, test_data_importer
) -> None:
    _setup_cmp(test_data_importer, 2019)
    district = District(id="2019ne", year=2019, abbreviation="ne")
    district.put()

    derived = DistrictAdvancementHelper.cmp_qualifiers_by_method(district, [])

    assert derived[
        CmpQualificationMethod.HALL_OF_FAME
    ] == DistrictAdvancementHelper.hall_of_fame_teams(2019)


def test_hall_of_fame_unlisted_manual_year_is_empty(
    ndb_stub, test_data_importer
) -> None:
    _setup_cmp(test_data_importer, 2026)
    district = District(id="2027ne", year=2027, abbreviation="ne")
    district.put()

    derived = DistrictAdvancementHelper.cmp_qualifiers_by_method(district, [])

    assert derived[CmpQualificationMethod.HALL_OF_FAME] == set()


def test_prior_year_cmp_qualifiers(ndb_stub, test_data_importer) -> None:
    _setup_cmp(test_data_importer, 2026)

    assert DistrictAdvancementHelper.prior_year_cmp_teams(
        2026, EventType.CMP_FINALS, AwardType.WINNER
    ) == {"frc1323", "frc2910", "frc4272", "frc5026"}
    assert (
        len(
            DistrictAdvancementHelper.prior_year_cmp_teams(
                2026, EventType.CMP_DIVISION, AwardType.ENGINEERING_INSPIRATION
            )
        )
        == 8
    )


@pytest.mark.parametrize(
    "regional_week,consumes",
    [(4, True), (6, False), (7, False)],
)
def test_regional_qualifier_only_consumes_before_the_dcmp(
    regional_week: int, consumes: bool, ndb_stub
) -> None:
    year = CMP_QUALIFICATION_RULES[CmpQualificationMethod.REGIONAL_WINNER].year_end
    district = District(id=f"{year}ne", year=year, abbreviation="ne")
    district.put()

    season_start = datetime.datetime(year, 2, 23)
    anchor = Event(
        id=f"{year}anchor",
        year=year,
        event_short="anchor",
        event_type_enum=EventType.REGIONAL,
        official=True,
        start_date=season_start,
        end_date=season_start,
    )
    anchor.put()

    regional_start = season_start + datetime.timedelta(weeks=regional_week)
    regional = Event(
        id=f"{year}reg",
        year=year,
        event_short="reg",
        event_type_enum=EventType.REGIONAL,
        official=True,
        start_date=regional_start,
        end_date=regional_start,
    )
    regional.put()
    Award(
        id=Award.render_key_name(f"{year}reg", AwardType.WINNER),
        name_str="Regional Winner",
        award_type_enum=AwardType.WINNER,
        year=year,
        event=regional.key,
        event_type_enum=EventType.REGIONAL,
        team_list=[ndb.Key(Team, "frc1")],
    ).put()

    dcmp_start = season_start + datetime.timedelta(weeks=6)
    dcmp = Event(
        id=f"{year}necmp",
        year=year,
        event_short="necmp",
        event_type_enum=EventType.DISTRICT_CMP,
        district_key=district.key,
        official=True,
        start_date=dcmp_start,
        end_date=dcmp_start,
    )
    dcmp.put()

    consuming, non_consuming = DistrictAdvancementHelper.cmp_qualifiers(
        district, [dcmp]
    )
    derived = DistrictAdvancementHelper.cmp_qualifiers_by_method(district, [dcmp])

    assert ("frc1" in consuming) == consumes
    assert ("frc1" in non_consuming) != consumes
    assert derived[CmpQualificationMethod.REGIONAL_WINNER] == (
        _team_keys(1) if consumes else set()
    )
    assert derived[CmpQualificationMethod.LATE_REGIONAL_WINNER] == (
        set() if consumes else _team_keys(1)
    )


def test_dcmp_award_qualifiers_ignore_plain_district_events(ndb_stub) -> None:
    district = District(id="2026ne", year=2026, abbreviation="ne")
    district.put()

    events = []
    for team_number, (event_key, event_type, award_type) in enumerate(
        [
            ("2026necmp", EventType.DISTRICT_CMP, AwardType.CHAIRMANS),
            (
                "2026necmp1",
                EventType.DISTRICT_CMP_DIVISION,
                AwardType.ENGINEERING_INSPIRATION,
            ),
            ("2026necmp2", EventType.DISTRICT_CMP_DIVISION, AwardType.ROOKIE_ALL_STAR),
            ("2026qual", EventType.DISTRICT, AwardType.CHAIRMANS),
            ("2026reg", EventType.REGIONAL, AwardType.CHAIRMANS),
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
            id=Award.render_key_name(event_key, award_type),
            name_str="Award",
            award_type_enum=award_type,
            year=2026,
            event=event.key,
            event_type_enum=event_type,
            team_list=[ndb.Key(Team, f"frc{team_number}")],
        ).put()

    derived = DistrictAdvancementHelper.cmp_qualifiers_by_method(district, events)

    assert derived[CmpQualificationMethod.DCMP_IMPACT] == _team_keys(1)
    assert derived[CmpQualificationMethod.DCMP_ENGINEERING_INSPIRATION] == _team_keys(2)
    assert derived[CmpQualificationMethod.DCMP_ROOKIE_ALL_STAR] == _team_keys(3)


def test_dcmp_winner_counts_only_on_the_finals_field(ndb_stub) -> None:
    district = District(id="2026ne", year=2026, abbreviation="ne")
    district.put()

    events = []
    for team_number, (event_key, event_type) in enumerate(
        [
            ("2026necmp", EventType.DISTRICT_CMP),
            ("2026necmp2", EventType.DISTRICT_CMP_DIVISION),
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
            id=Award.render_key_name(event_key, AwardType.WINNER),
            name_str="District Championship Winner",
            award_type_enum=AwardType.WINNER,
            year=2026,
            event=event.key,
            event_type_enum=event_type,
            team_list=[ndb.Key(Team, f"frc{team_number}")],
        ).put()

    derived = DistrictAdvancementHelper.cmp_qualifiers_by_method(district, events)

    assert derived[CmpQualificationMethod.DCMP_WINNER] == _team_keys(1)


def test_declines_include_a_qualifier_who_did_not_attend() -> None:
    rankings = _descending_rankings(10)

    cutoffs = _cmp_cutoffs(
        rankings,
        slots=5,
        consuming=_team_keys(2),
        non_consuming=set(),
        attendance=_team_keys(1, 3, 4, 5),
    )

    assert cutoffs.effective == 96
    assert cutoffs.declined == ["frc2"]


def test_declined_consuming_slot_returns_to_the_points_pool() -> None:
    rankings = _descending_rankings(10)

    cutoffs = _cmp_cutoffs(
        rankings,
        slots=5,
        consuming=_team_keys(9),
        non_consuming=set(),
        attendance=_team_keys(1, 2, 3, 4, 5),
    )

    assert cutoffs.original == 97
    assert cutoffs.effective == 96
    assert cutoffs.declined == []


def test_no_points_slots_yields_sentinel_original() -> None:
    rankings = _descending_rankings(10)

    cutoffs = _cmp_cutoffs(
        rankings,
        slots=3,
        consuming=_team_keys(8, 9, 10),
        non_consuming=set(),
        attendance=_team_keys(1, 8, 9),
    )

    assert cutoffs.original == NO_POINTS_CUTOFF
    assert cutoffs.effective == 100


def test_every_ranked_team_qualified_yields_sentinel_original() -> None:
    rankings = _descending_rankings(3)

    cutoffs = _cmp_cutoffs(
        rankings,
        slots=5,
        consuming=set(),
        non_consuming=_team_keys(1, 2, 3),
        attendance=_team_keys(1, 2, 3),
    )

    assert cutoffs.original == NO_POINTS_CUTOFF
    assert cutoffs.effective == 0


def test_declines_exclude_non_consuming_qualifiers() -> None:
    rankings = _descending_rankings(10)

    cutoffs = _cmp_cutoffs(
        rankings,
        slots=5,
        consuming=set(),
        non_consuming=_team_keys(2),
        attendance=_team_keys(1, 3, 4, 5, 6),
    )

    assert cutoffs.effective == 95
    assert cutoffs.declined == []


def test_cmp_attendance_reads_division_rosters(ndb_stub, test_data_importer) -> None:
    _setup_cmp(test_data_importer, 2026)

    assert len(DistrictAdvancementHelper.cmp_attendance(2026)) == 597


def test_cmp_values_carry_forward_when_cmp_has_not_happened(
    ndb_stub, test_data_importer
) -> None:
    district = _setup_district(test_data_importer, "2026ne")
    district.advancement_cutoffs = DistrictAdvancementCutoffs(
        dcmp_original=0,
        dcmp_effective=0,
        dcmp_declines=[],
        cmp_original=190,
        cmp_effective=173,
        cmp_declines=["frc95"],
        cmp_qualification={"frc95": CmpQualificationMethod.DISTRICT_POINTS},
    )
    district.put()
    events = Event.query(Event.district_key == district.key).fetch()

    cutoffs = none_throws(
        DistrictAdvancementHelper.calculate_for_district(district, events)
    )

    assert cutoffs["cmp_original"] == 190
    assert cutoffs["cmp_effective"] == 173
    assert cutoffs["cmp_declines"] == ["frc95"]
    assert cutoffs["cmp_qualification"] == {
        "frc95": CmpQualificationMethod.DISTRICT_POINTS
    }
