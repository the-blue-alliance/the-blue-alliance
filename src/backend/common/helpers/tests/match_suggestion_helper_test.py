import datetime
import json
from typing import Dict, List, Optional

import pytest
from freezegun import freeze_time
from google.appengine.ext import ndb

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.helpers.match_suggestion_helper import (
    MatchSuggestionHelper,
    MAX_UPCOMING_PER_EVENT,
    NUM_SUGGESTIONS,
    W_FAVORITES,
    W_PERFORMANCE,
    W_SIGNIFICANCE,
    W_TIME_DECAY,
)
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.keys import TeamKey
from backend.common.models.match import Match

NOW = datetime.datetime(2026, 4, 30, 15, 0, 0)


@pytest.fixture(autouse=True)
def auto_add_ndb_context(ndb_context) -> None:
    pass


def make_event(
    event_key: str = "2026casj",
    event_type: EventType = EventType.REGIONAL,
    start_date: Optional[datetime.datetime] = None,
) -> Event:
    year = int(event_key[:4])
    return Event(
        id=event_key,
        event_short=event_key[4:],
        name=f"Event {event_key}",
        short_name=event_key[4:].upper(),
        year=year,
        event_type_enum=event_type,
        start_date=start_date or datetime.datetime(year, 4, 29),
        end_date=(start_date or datetime.datetime(year, 4, 29))
        + datetime.timedelta(days=2),
    )


def make_match(
    event: Event,
    comp_level: CompLevel = CompLevel.QM,
    match_number: int = 1,
    set_number: int = 1,
    red: Optional[List[TeamKey]] = None,
    blue: Optional[List[TeamKey]] = None,
    played: bool = False,
    predicted_time: Optional[datetime.datetime] = None,
    time: Optional[datetime.datetime] = None,
) -> Match:
    red = red or ["frc1", "frc2", "frc3"]
    blue = blue or ["frc4", "frc5", "frc6"]
    score = 100 if played else -1
    return Match(
        id=Match.render_key_name(event.key_name, comp_level, set_number, match_number),
        event=event.key,
        year=event.year,
        comp_level=comp_level,
        set_number=set_number,
        match_number=match_number,
        team_key_names=red + blue,
        alliances_json=json.dumps(
            {
                "red": {"teams": red, "score": score},
                "blue": {"teams": blue, "score": score},
            }
        ),
        predicted_time=predicted_time,
        time=time,
    )


def seed_matches(event: Event, matches: List[Match]) -> Event:
    event.put()
    for match in matches:
        match.put()
    return event


# --------------------------------------------------------------------------
# Pure scoring functions
# --------------------------------------------------------------------------


def test_min_max_normalize_empty() -> None:
    assert MatchSuggestionHelper._min_max_normalize([]) == []


def test_min_max_normalize_single_value_is_neutral() -> None:
    assert MatchSuggestionHelper._min_max_normalize([42.0]) == [0.5]


def test_min_max_normalize_all_equal_is_neutral() -> None:
    assert MatchSuggestionHelper._min_max_normalize([3.0, 3.0, 3.0]) == [0.5, 0.5, 0.5]


def test_min_max_normalize_spreads_to_endpoints() -> None:
    assert MatchSuggestionHelper._min_max_normalize([10.0, 20.0, 30.0]) == [
        0.0,
        0.5,
        1.0,
    ]


def test_time_decay_none_is_zero() -> None:
    assert MatchSuggestionHelper._time_decay(None, NOW) == 0.0


def test_time_decay_peaks_at_match_time() -> None:
    assert MatchSuggestionHelper._time_decay(NOW, NOW) == 1.0


@pytest.mark.parametrize("offset_s", [60, 300, 900, 1800, 7200])
def test_time_decay_falls_off_into_the_future(offset_s: int) -> None:
    nearer = MatchSuggestionHelper._time_decay(
        NOW + datetime.timedelta(seconds=offset_s - 60), NOW
    )
    further = MatchSuggestionHelper._time_decay(
        NOW + datetime.timedelta(seconds=offset_s), NOW
    )
    assert 0.0 < further < nearer <= 1.0


@pytest.mark.parametrize("offset_s", [60, 300, 900, 1800])
def test_time_decay_falls_off_into_the_past(offset_s: int) -> None:
    nearer = MatchSuggestionHelper._time_decay(
        NOW - datetime.timedelta(seconds=offset_s - 60), NOW
    )
    further = MatchSuggestionHelper._time_decay(
        NOW - datetime.timedelta(seconds=offset_s), NOW
    )
    assert 0.0 < further < nearer <= 1.0


def test_time_decay_forgets_late_matches_faster_than_future_ones() -> None:
    ten_min = datetime.timedelta(minutes=10)
    late = MatchSuggestionHelper._time_decay(NOW - ten_min, NOW)
    upcoming = MatchSuggestionHelper._time_decay(NOW + ten_min, NOW)
    assert late < upcoming


@pytest.mark.parametrize(
    "comp_level,expected",
    [
        (CompLevel.QM, 0.0),
        (CompLevel.EF, 0.1),
        (CompLevel.QF, 0.2),
        (CompLevel.SF, 0.4),
        (CompLevel.F, 1.0),
    ],
)
def test_significance_pre_2023(comp_level: CompLevel, expected: float) -> None:
    event = make_event("2019casj")
    match = make_match(event, comp_level=comp_level, set_number=1)
    assert MatchSuggestionHelper._significance(event, match) == expected


@pytest.mark.parametrize(
    "set_number,expected",
    [
        (1, 0.30),  # Round 1
        (4, 0.30),
        (5, 0.40),  # Round 2
        (8, 0.40),
        (9, 0.54),  # Round 3
        (10, 0.54),
        (11, 0.66),  # Round 4
        (12, 0.66),
        (13, 0.80),  # Round 5 -- decides the last finals slot
    ],
)
def test_significance_ramps_across_double_elim_rounds(
    set_number: int, expected: float
) -> None:
    event = make_event("2026cmptx", EventType.CMP_DIVISION)
    event.playoff_type = PlayoffType.DOUBLE_ELIM_8_TEAM
    match = make_match(event, comp_level=CompLevel.SF, set_number=set_number)

    actual = MatchSuggestionHelper._significance(event, match)
    assert actual == pytest.approx(expected)  # pyre-ignore[16]


def test_significance_double_elim_rounds_are_monotonic() -> None:
    event = make_event("2026cmptx", EventType.CMP_DIVISION)
    event.playoff_type = PlayoffType.DOUBLE_ELIM_8_TEAM

    scores = [
        MatchSuggestionHelper._significance(
            event, make_match(event, comp_level=CompLevel.SF, set_number=n)
        )
        for n in range(1, 14)
    ]
    assert scores == sorted(scores)
    # Every sf stays below a final and above a qual
    assert max(scores) < 1.0
    assert min(scores) > 0.0


@pytest.mark.parametrize(
    "set_number,expected",
    [
        (1, 0.30),  # Round 1
        (2, 0.30),
        (3, 0.40),  # Round 2
        (4, 0.40),
        (5, 0.54),  # Round 3
    ],
)
def test_significance_handles_the_four_team_bracket(
    set_number: int, expected: float
) -> None:
    event = make_event("2026necmp", EventType.DISTRICT_CMP)
    event.playoff_type = PlayoffType.DOUBLE_ELIM_4_TEAM
    match = make_match(event, comp_level=CompLevel.SF, set_number=set_number)

    actual = MatchSuggestionHelper._significance(event, match)
    assert actual == pytest.approx(expected)  # pyre-ignore[16]


def test_significance_ignores_double_elim_before_2023() -> None:
    event = make_event("2022cmptx", EventType.CMP_DIVISION)
    event.playoff_type = PlayoffType.DOUBLE_ELIM_8_TEAM
    match = make_match(event, comp_level=CompLevel.SF, set_number=13)

    # Pre-2023 `sf` means one specific round, so the flat weight still applies
    assert MatchSuggestionHelper._significance(event, match) == 0.4


def test_significance_ignores_non_double_elim_brackets() -> None:
    event = make_event("2026casj")
    event.playoff_type = PlayoffType.BRACKET_8_TEAM
    match = make_match(event, comp_level=CompLevel.SF, set_number=2)

    assert MatchSuggestionHelper._significance(event, match) == 0.4


def test_significance_falls_back_on_unknown_playoff_type() -> None:
    event = make_event("2026casj")
    match = make_match(event, comp_level=CompLevel.SF, set_number=1)

    # playoff_type is nullable on Event
    assert event.playoff_type is None
    assert MatchSuggestionHelper._significance(event, match) == 0.4


def test_significance_falls_back_on_out_of_bracket_set_number() -> None:
    event = make_event("2026cmptx", EventType.CMP_DIVISION)
    event.playoff_type = PlayoffType.DOUBLE_ELIM_8_TEAM
    match = make_match(event, comp_level=CompLevel.SF, set_number=99)

    assert MatchSuggestionHelper._significance(event, match) == 0.4


def test_performance_kernel_favors_close_matches() -> None:
    close = MatchSuggestionHelper._performance_kernel(150.0, 150.0)
    lopsided = MatchSuggestionHelper._performance_kernel(250.0, 50.0)
    assert close == 450.0
    assert lopsided == 350.0
    assert close > lopsided


def test_performance_kernel_is_symmetric() -> None:
    assert MatchSuggestionHelper._performance_kernel(
        200.0, 75.0
    ) == MatchSuggestionHelper._performance_kernel(75.0, 200.0)


def test_performance_kernel_zero() -> None:
    assert MatchSuggestionHelper._performance_kernel(0.0, 0.0) == 0.0


# --------------------------------------------------------------------------
# team_recent_oprs
# --------------------------------------------------------------------------


def seed_team_event(
    team_key: TeamKey,
    event_key: str,
    event_type: EventType,
    start_date: datetime.datetime,
    oprs: Optional[Dict[str, float]] = None,
    matchstats_is_none: bool = False,
) -> Event:
    from backend.common.models.event_team import EventTeam
    from backend.common.models.team import Team

    Team(
        id=team_key, team_number=int("".join(c for c in team_key[3:] if c.isdigit()))
    ).put()
    event = make_event(event_key, event_type, start_date)
    event.put()
    EventTeam(
        id=f"{event_key}_{team_key}",
        event=event.key,
        team=ndb.Key(Team, team_key),
        year=event.year,
    ).put()
    if not matchstats_is_none:
        EventDetails(
            id=event_key,
            matchstats={"oprs": oprs or {}, "dprs": {}, "ccwms": {}},
        ).put()
    else:
        EventDetails(id=event_key, matchstats=None).put()
    return event


def test_recent_oprs_prefers_most_recent_in_season_event(
    ndb_stub, memcache_stub
) -> None:
    seed_team_event(
        "frc254",
        "2026casj",
        EventType.REGIONAL,
        datetime.datetime(2026, 3, 1),
        oprs={"254": 30.0},
    )
    seed_team_event(
        "frc254",
        "2026cmptx",
        EventType.CMP_FINALS,
        datetime.datetime(2026, 4, 29),
        oprs={"254": 55.0},
    )

    oprs = MatchSuggestionHelper.team_recent_oprs({"frc254"}, 2026, NOW)
    assert oprs == {"frc254": 55.0}


def test_recent_oprs_ignores_later_offseason_event(ndb_stub, memcache_stub) -> None:
    seed_team_event(
        "frc254",
        "2026casj",
        EventType.REGIONAL,
        datetime.datetime(2026, 3, 1),
        oprs={"254": 30.0},
    )
    seed_team_event(
        "frc254",
        "2026cc",
        EventType.OFFSEASON,
        datetime.datetime(2026, 4, 29),
        oprs={"254": 99.0},
    )

    oprs = MatchSuggestionHelper.team_recent_oprs({"frc254"}, 2026, NOW)
    assert oprs == {"frc254": 30.0}


def test_recent_oprs_falls_through_when_newest_event_has_no_matchstats(
    ndb_stub, memcache_stub
) -> None:
    seed_team_event(
        "frc254",
        "2026casj",
        EventType.REGIONAL,
        datetime.datetime(2026, 3, 1),
        oprs={"254": 30.0},
    )
    seed_team_event(
        "frc254",
        "2026cmptx",
        EventType.CMP_FINALS,
        datetime.datetime(2026, 4, 29),
        matchstats_is_none=True,
    )

    oprs = MatchSuggestionHelper.team_recent_oprs({"frc254"}, 2026, NOW)
    assert oprs == {"frc254": 30.0}


def test_recent_oprs_falls_through_when_team_missing_from_oprs(
    ndb_stub, memcache_stub
) -> None:
    seed_team_event(
        "frc254",
        "2026casj",
        EventType.REGIONAL,
        datetime.datetime(2026, 3, 1),
        oprs={"254": 30.0},
    )
    seed_team_event(
        "frc254",
        "2026cmptx",
        EventType.CMP_FINALS,
        datetime.datetime(2026, 4, 29),
        oprs={"1114": 40.0},
    )

    oprs = MatchSuggestionHelper.team_recent_oprs({"frc254"}, 2026, NOW)
    assert oprs == {"frc254": 30.0}


def test_recent_oprs_zero_when_no_in_season_opr(ndb_stub, memcache_stub) -> None:
    seed_team_event(
        "frc254",
        "2026cc",
        EventType.OFFSEASON,
        datetime.datetime(2026, 4, 29),
        oprs={"254": 99.0},
    )

    oprs = MatchSuggestionHelper.team_recent_oprs({"frc254"}, 2026, NOW)
    assert oprs == {"frc254": 0.0}


def test_recent_oprs_includes_event_starting_today(ndb_stub, memcache_stub) -> None:
    seed_team_event(
        "frc254",
        "2026cmptx",
        EventType.CMP_FINALS,
        NOW.replace(hour=0, minute=0),
        oprs={"254": 55.0},
    )

    oprs = MatchSuggestionHelper.team_recent_oprs({"frc254"}, 2026, NOW)
    assert oprs == {"frc254": 55.0}


def test_recent_oprs_ignores_future_events(ndb_stub, memcache_stub) -> None:
    seed_team_event(
        "frc254",
        "2026casj",
        EventType.REGIONAL,
        datetime.datetime(2026, 3, 1),
        oprs={"254": 30.0},
    )
    seed_team_event(
        "frc254",
        "2026week7",
        EventType.REGIONAL,
        datetime.datetime(2026, 5, 10),
        oprs={"254": 99.0},
    )

    oprs = MatchSuggestionHelper.team_recent_oprs({"frc254"}, 2026, NOW)
    assert oprs == {"frc254": 30.0}


def test_recent_oprs_does_not_cross_years(ndb_stub, memcache_stub) -> None:
    seed_team_event(
        "frc254",
        "2025casj",
        EventType.REGIONAL,
        datetime.datetime(2025, 3, 1),
        oprs={"254": 30.0},
    )

    oprs = MatchSuggestionHelper.team_recent_oprs({"frc254"}, 2026, NOW)
    assert oprs == {"frc254": 0.0}


def test_recent_oprs_clamps_negatives(ndb_stub, memcache_stub) -> None:
    seed_team_event(
        "frc254",
        "2026casj",
        EventType.REGIONAL,
        datetime.datetime(2026, 3, 1),
        oprs={"254": -12.5},
    )

    oprs = MatchSuggestionHelper.team_recent_oprs({"frc254"}, 2026, NOW)
    assert oprs == {"frc254": 0.0}


# --------------------------------------------------------------------------
# compute_match_suggestions
# --------------------------------------------------------------------------


def test_no_events_yields_empty_feed(ndb_stub, memcache_stub) -> None:
    result = MatchSuggestionHelper.compute_match_suggestions(events=[], now=NOW)
    assert result.suggestions == {}
    assert result.updated_at == int(NOW.timestamp())


def test_skips_played_matches(ndb_stub, memcache_stub) -> None:
    event = make_event()
    seed_matches(
        event,
        [
            make_match(
                event,
                match_number=1,
                played=True,
                predicted_time=NOW + datetime.timedelta(minutes=1),
            ),
            make_match(
                event,
                match_number=2,
                predicted_time=NOW + datetime.timedelta(minutes=10),
            ),
        ],
    )

    result = MatchSuggestionHelper.compute_match_suggestions(events=[event], now=NOW)
    assert list(result.suggestions) == ["2026casj_qm2"]


def test_skips_matches_with_no_time(ndb_stub, memcache_stub) -> None:
    event = make_event()
    seed_matches(event, [make_match(event, match_number=1)])

    result = MatchSuggestionHelper.compute_match_suggestions(events=[event], now=NOW)
    assert result.suggestions == {}


def test_skips_matches_beyond_the_future_horizon(ndb_stub, memcache_stub) -> None:
    event = make_event()
    seed_matches(
        event,
        [
            make_match(
                event,
                match_number=1,
                predicted_time=NOW + datetime.timedelta(hours=4),
            )
        ],
    )

    result = MatchSuggestionHelper.compute_match_suggestions(events=[event], now=NOW)
    assert result.suggestions == {}


def test_skips_stale_late_matches(ndb_stub, memcache_stub) -> None:
    event = make_event()
    seed_matches(
        event,
        [
            make_match(
                event,
                match_number=1,
                predicted_time=NOW - datetime.timedelta(minutes=45),
            )
        ],
    )

    result = MatchSuggestionHelper.compute_match_suggestions(events=[event], now=NOW)
    assert result.suggestions == {}


def test_falls_back_to_scheduled_time(ndb_stub, memcache_stub) -> None:
    event = make_event()
    seed_matches(
        event,
        [make_match(event, match_number=1, time=NOW + datetime.timedelta(minutes=5))],
    )

    result = MatchSuggestionHelper.compute_match_suggestions(events=[event], now=NOW)
    assert list(result.suggestions) == ["2026casj_qm1"]


def test_respects_max_upcoming_per_event(ndb_stub, memcache_stub) -> None:
    event = make_event()
    seed_matches(
        event,
        [
            make_match(
                event,
                match_number=i,
                predicted_time=NOW + datetime.timedelta(minutes=i),
            )
            for i in range(1, 8)
        ],
    )

    result = MatchSuggestionHelper.compute_match_suggestions(events=[event], now=NOW)
    assert len(result.suggestions) == MAX_UPCOMING_PER_EVENT


def test_truncates_to_num_suggestions(ndb_stub, memcache_stub) -> None:
    events = []
    for i in range(15):
        event = make_event(event_key=f"2026ev{i:02d}")
        seed_matches(
            event,
            [
                make_match(
                    event,
                    match_number=j,
                    predicted_time=NOW + datetime.timedelta(minutes=j),
                )
                for j in range(1, 4)
            ],
        )
        events.append(event)

    result = MatchSuggestionHelper.compute_match_suggestions(events=events, now=NOW)
    assert len(result.suggestions) == NUM_SUGGESTIONS
    ranks = sorted(s.rank for s in result.suggestions.values())
    assert ranks == list(range(NUM_SUGGESTIONS))


def test_imminent_final_outranks_distant_qual(ndb_stub, memcache_stub) -> None:
    einstein = make_event("2026cmptx", EventType.CMP_FINALS)
    seed_matches(
        einstein,
        [
            make_match(
                einstein,
                comp_level=CompLevel.F,
                match_number=1,
                predicted_time=NOW + datetime.timedelta(minutes=2),
            )
        ],
    )
    regional = make_event("2026casj")
    seed_matches(
        regional,
        [
            make_match(
                regional,
                match_number=1,
                predicted_time=NOW + datetime.timedelta(minutes=90),
            )
        ],
    )

    result = MatchSuggestionHelper.compute_match_suggestions(
        events=[regional, einstein], now=NOW
    )
    by_rank = sorted(result.suggestions.values(), key=lambda s: s.rank)
    assert [s.match_key for s in by_rank] == ["2026cmptx_f1m1", "2026casj_qm1"]
    assert [s.rank for s in by_rank] == [0, 1]


def test_score_is_the_weighted_sum_of_components(ndb_stub, memcache_stub) -> None:
    event = make_event()
    seed_matches(
        event,
        [
            make_match(
                event,
                match_number=1,
                predicted_time=NOW + datetime.timedelta(minutes=3),
            )
        ],
    )

    result = MatchSuggestionHelper.compute_match_suggestions(events=[event], now=NOW)
    suggestion = result.suggestions["2026casj_qm1"]
    c = suggestion.components
    expected = (
        W_FAVORITES * c.favorites
        + W_SIGNIFICANCE * c.significance
        + W_TIME_DECAY * c.time_decay
        + W_PERFORMANCE * c.performance
    )
    assert suggestion.score == pytest.approx(expected, abs=1e-4)  # pyre-ignore[16]


def test_populates_render_fields(ndb_stub, memcache_stub) -> None:
    event = make_event()
    predicted = NOW + datetime.timedelta(minutes=3)
    scheduled = NOW + datetime.timedelta(minutes=5)
    seed_matches(
        event,
        [
            make_match(
                event,
                comp_level=CompLevel.SF,
                set_number=3,
                match_number=1,
                red=["frc254", "frc1114", "frc2056"],
                blue=["frc118", "frc148", "frc971"],
                predicted_time=predicted,
                time=scheduled,
            )
        ],
    )

    result = MatchSuggestionHelper.compute_match_suggestions(events=[event], now=NOW)
    suggestion = result.suggestions["2026casj_sf3m1"]
    assert suggestion.event_key == "2026casj"
    assert suggestion.event_name == "Event 2026casj"
    assert suggestion.event_short_name == "CASJ"
    assert suggestion.comp_level == CompLevel.SF
    assert suggestion.set_number == 3
    assert suggestion.match_number == 1
    assert suggestion.red_team_numbers == [254, 1114, 2056]
    assert suggestion.blue_team_numbers == [118, 148, 971]
    assert suggestion.predicted_time == int(predicted.timestamp())
    assert suggestion.scheduled_time == int(scheduled.timestamp())


def test_stronger_teams_score_higher(ndb_stub, memcache_stub) -> None:
    seed_team_event(
        "frc254",
        "2026casj",
        EventType.REGIONAL,
        datetime.datetime(2026, 3, 1),
        oprs={"254": 90.0},
    )

    event = make_event("2026cmptx", EventType.CMP_FINALS)
    seed_matches(
        event,
        [
            make_match(
                event,
                match_number=1,
                red=["frc254", "frc2", "frc3"],
                blue=["frc4", "frc5", "frc6"],
                predicted_time=NOW + datetime.timedelta(minutes=5),
            ),
            make_match(
                event,
                match_number=2,
                red=["frc7", "frc8", "frc9"],
                blue=["frc10", "frc11", "frc12"],
                predicted_time=NOW + datetime.timedelta(minutes=5),
            ),
        ],
    )

    result = MatchSuggestionHelper.compute_match_suggestions(events=[event], now=NOW)
    strong = result.suggestions["2026cmptx_qm1"]
    weak = result.suggestions["2026cmptx_qm2"]
    assert strong.components.performance > weak.components.performance
    assert strong.rank < weak.rank


def test_uses_live_events_by_default(ndb_stub, memcache_stub) -> None:
    event = make_event("2026casj", EventType.REGIONAL, datetime.datetime(2026, 4, 30))
    seed_matches(
        event,
        [
            make_match(
                event,
                match_number=1,
                predicted_time=NOW + datetime.timedelta(minutes=5),
            )
        ],
    )

    with freeze_time(NOW):
        result = MatchSuggestionHelper.compute_match_suggestions()

    assert list(result.suggestions) == ["2026casj_qm1"]


# --------------------------------------------------------------------------
# score_all_matches (any-event validation mode)
# --------------------------------------------------------------------------


def test_score_all_includes_played_and_unscheduled(ndb_stub, memcache_stub) -> None:
    event = make_event()
    seed_matches(
        event,
        [
            make_match(event, match_number=1, played=True),
            make_match(event, match_number=2),
        ],
    )

    result = MatchSuggestionHelper.score_all_matches([event], now=NOW)
    assert set(result.suggestions) == {"2026casj_qm1", "2026casj_qm2"}


def test_score_all_ignores_the_time_horizon(ndb_stub, memcache_stub) -> None:
    event = make_event()
    seed_matches(
        event,
        [
            make_match(
                event,
                match_number=1,
                played=True,
                predicted_time=NOW - datetime.timedelta(days=400),
            )
        ],
    )

    result = MatchSuggestionHelper.score_all_matches([event], now=NOW)
    assert list(result.suggestions) == ["2026casj_qm1"]


def test_score_all_zeroes_time_decay(ndb_stub, memcache_stub) -> None:
    event = make_event()
    seed_matches(
        event,
        [
            make_match(
                event,
                match_number=1,
                predicted_time=NOW + datetime.timedelta(minutes=1),
            )
        ],
    )

    result = MatchSuggestionHelper.score_all_matches([event], now=NOW)
    suggestion = result.suggestions["2026casj_qm1"]
    assert suggestion.components.time_decay == 0.0
    expected = (
        W_FAVORITES * suggestion.components.favorites
        + W_SIGNIFICANCE * suggestion.components.significance
        + W_PERFORMANCE * suggestion.components.performance
    )
    assert suggestion.score == pytest.approx(expected, abs=1e-4)  # pyre-ignore[16]


def test_score_all_is_not_truncated(ndb_stub, memcache_stub) -> None:
    event = make_event()
    seed_matches(
        event,
        [
            make_match(event, match_number=i, played=True)
            for i in range(1, NUM_SUGGESTIONS + 12)
        ],
    )

    result = MatchSuggestionHelper.score_all_matches([event], now=NOW)
    assert len(result.suggestions) == NUM_SUGGESTIONS + 11


def test_score_all_ranks_by_significance_and_performance(
    ndb_stub, memcache_stub
) -> None:
    seed_team_event(
        "frc254",
        "2026casj",
        EventType.REGIONAL,
        datetime.datetime(2026, 3, 1),
        oprs={"254": 90.0},
    )
    event = make_event("2026cmptx", EventType.CMP_FINALS)
    seed_matches(
        event,
        [
            make_match(event, comp_level=CompLevel.QM, match_number=1, played=True),
            make_match(
                event,
                comp_level=CompLevel.F,
                match_number=1,
                red=["frc254", "frc2", "frc3"],
                played=True,
            ),
        ],
    )

    result = MatchSuggestionHelper.score_all_matches([event], now=NOW)
    finals = result.suggestions["2026cmptx_f1m1"]
    quals = result.suggestions["2026cmptx_qm1"]
    assert finals.components.significance == 1.0
    assert quals.components.significance == 0.0
    assert finals.components.performance > quals.components.performance
    assert finals.rank < quals.rank


def test_score_all_normalizes_across_the_events_passed(ndb_stub, memcache_stub) -> None:
    seed_team_event(
        "frc254",
        "2026casj",
        EventType.REGIONAL,
        datetime.datetime(2026, 3, 1),
        oprs={"254": 90.0},
    )
    strong = make_event("2026cmptx", EventType.CMP_FINALS)
    seed_matches(
        strong,
        [
            make_match(
                strong, match_number=1, red=["frc254", "frc2", "frc3"], played=True
            )
        ],
    )
    weak = make_event("2026ev01")
    seed_matches(weak, [make_match(weak, match_number=1, played=True)])

    together = MatchSuggestionHelper.score_all_matches([strong, weak], now=NOW)
    assert together.suggestions["2026cmptx_qm1"].components.performance == 1.0
    assert together.suggestions["2026ev01_qm1"].components.performance == 0.0

    # Scored alone there is nothing to normalize against, so it lands neutral
    alone = MatchSuggestionHelper.score_all_matches([strong], now=NOW)
    assert alone.suggestions["2026cmptx_qm1"].components.performance == 0.5
