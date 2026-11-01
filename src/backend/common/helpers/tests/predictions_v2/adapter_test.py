import calendar
import datetime
import json
from typing import Dict, List, Optional

import pytest
from google.appengine.ext import ndb

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.helpers.predictions_v2.adapter import (
    bonus_rps,
    build_stream,
    entry_kind,
    EntryKind,
    is_stream_match,
    match_slot,
    outcome_fingerprint,
    to_match_context,
    to_match_outcome,
)
from backend.common.helpers.predictions_v2.ordering import event_block_order
from backend.common.helpers.tests.predictions_v2.api_fixture import load_api_fixture
from backend.common.helpers.tests.predictions_v2.model.golden import load_golden
from backend.common.models.event import Event
from backend.common.models.match import Match


def _event(event_type: EventType, key: str = "2024casj") -> Event:
    return Event(
        id=key,
        year=int(key[:4]),
        event_short=key[4:],
        event_type_enum=event_type,
        start_date=datetime.datetime(2024, 3, 8),
        end_date=datetime.datetime(2024, 3, 10),
    )


def _match(
    red_score: int = 50,
    blue_score: int = 40,
    comp_level: str = "qm",
    breakdown: Optional[Dict] = None,
    red_dqs: Optional[List[str]] = None,
    key: str = "2024casj_qm1",
) -> Match:
    return Match(
        id=key,
        event=ndb.Key(Event, "2024casj"),
        year=2024,
        comp_level=comp_level,
        set_number=1,
        match_number=1,
        team_key_names=["frc254", "frc604B", "frc1678", "frc971", "frc5940", "frc8"],
        alliances_json=json.dumps(
            {
                "red": {
                    "teams": ["frc254", "frc604B", "frc1678"],
                    "score": red_score,
                    "surrogates": [],
                    "dqs": red_dqs or [],
                },
                "blue": {
                    "teams": ["frc971", "frc5940", "frc8"],
                    "score": blue_score,
                    "surrogates": ["frc8"],
                    "dqs": [],
                },
            }
        ),
        score_breakdown_json=json.dumps(breakdown) if breakdown else None,
        actual_time=datetime.datetime(2024, 3, 9, 17, 0),
        time=datetime.datetime(2024, 3, 9, 16, 50),
    )


def test_golden_inputs_from_tba_models() -> None:
    events, matches = load_api_fixture()
    by_key = {m.key_name: m for m in matches}
    golden = load_golden()
    assert len(golden) == len(matches)
    for g in golden:
        m = by_key[g.context.match_key]
        event = events[m.event_key_name]
        assert entry_kind(event) == EntryKind.TRAIN
        assert is_stream_match(m)
        assert to_match_context(m, event) == g.context
        assert to_match_outcome(m) == g.outcome, g.context.match_key


def test_golden_stream_order_from_tba_models() -> None:
    events, matches = load_api_fixture()
    slots = [match_slot(m, events[m.event_key_name]) for m in matches]
    ordered = [slots[i].match_key for i in event_block_order(slots)]
    assert ordered == [g.context.match_key for g in load_golden()]


def test_build_stream_skips_events_outside_the_stream() -> None:
    events = {
        "2024casj": _event(EventType.REGIONAL, "2024casj"),
        "2024cc": _event(EventType.OFFSEASON, "2024cc"),
        "2024rem": _event(EventType.REMOTE, "2024rem"),
    }
    matches = [
        _match(key="2024casj_qm1"),
        _match(key="2024casj_qm2", comp_level="pm"),
        _match(key="2024casj_qm3", red_score=-1, blue_score=-1),
    ]
    for key in ("2024cc_qm1", "2024rem_qm1"):
        m = _match(key=key)
        m.event = ndb.Key(Event, key.split("_")[0])
        matches.append(m)
    stream = build_stream(events, matches)
    assert [(it.context.match_key, it.kind) for it in stream] == [
        ("2024casj_qm1", EntryKind.TRAIN),
        ("2024cc_qm1", EntryKind.FORECAST),
    ]


@pytest.mark.parametrize(
    "event_type, kind",
    [
        (EventType.REGIONAL, EntryKind.TRAIN),
        (EventType.DISTRICT, EntryKind.TRAIN),
        (EventType.DISTRICT_CMP, EntryKind.TRAIN),
        (EventType.DISTRICT_CMP_DIVISION, EntryKind.TRAIN),
        (EventType.CMP_DIVISION, EntryKind.TRAIN),
        (EventType.CMP_FINALS, EntryKind.TRAIN),
        (EventType.FOC, EntryKind.TRAIN),
        (EventType.OFFSEASON, EntryKind.FORECAST),
        (EventType.PRESEASON, EntryKind.FORECAST),
        (EventType.REMOTE, None),
        (EventType.UNLABLED, None),
    ],
)
def test_entry_kind(event_type: EventType, kind: Optional[EntryKind]) -> None:
    assert entry_kind(_event(event_type)) == kind


def test_practice_and_unplayed_matches_are_not_entries() -> None:
    assert is_stream_match(_match())
    assert not is_stream_match(_match(comp_level="pm"))
    assert not is_stream_match(_match(red_score=-1, blue_score=-1))


def test_context_keeps_team_keys_and_event_metadata() -> None:
    ctx = to_match_context(_match(), _event(EventType.DISTRICT))
    assert ctx.red_teams == ("frc254", "frc604B", "frc1678")
    assert ctx.blue_teams == ("frc971", "frc5940", "frc8")
    assert ctx.event_type == EventType.DISTRICT
    assert ctx.comp_level == CompLevel.QM


def test_outcome_win_labels() -> None:
    assert to_match_outcome(_match(50, 40)).red_win == 1.0
    assert to_match_outcome(_match(40, 50)).red_win == 0.0
    assert to_match_outcome(_match(40, 40)).red_win == 0.5


def test_outcome_dqs_cover_the_alliance_in_playoffs() -> None:
    qm = to_match_outcome(_match(red_dqs=["frc254"]))
    assert qm.red_dqs == ("frc254",)
    sf = to_match_outcome(
        _match(comp_level="sf", red_dqs=["frc254"], key="2024casj_sf1m1")
    )
    assert sf.red_dqs == ("frc254", "frc604B", "frc1678")


def test_bonus_rps() -> None:
    assert bonus_rps(
        2024, {"melodyBonusAchieved": True, "ensembleBonusAchieved": False}
    ) == {
        "rp_1": 1,
        "rp_2": 0,
    }
    # A missing flag is left out.
    assert bonus_rps(2024, {"melodyBonusAchieved": True}) == {"rp_1": 1}
    # 2020 keys follow the model's rules: operational, then energized.
    assert bonus_rps(
        2020,
        {"shieldOperationalRankingPoint": True, "shieldEnergizedRankingPoint": False},
    ) == {"rp_1": 1, "rp_2": 0}
    assert bonus_rps(2015, {"foo": True}) == {}
    assert bonus_rps(2024, None) == {}


def test_outcome_fingerprint_changes_with_the_result() -> None:
    bd = {"red": {"totalPoints": 50}, "blue": {"totalPoints": 40}}
    base = outcome_fingerprint(_match(breakdown=bd))
    assert base == outcome_fingerprint(_match(breakdown=bd))
    assert base != outcome_fingerprint(_match(51, 40, breakdown=bd))
    assert base != outcome_fingerprint(
        _match(breakdown={"red": {"totalPoints": 51}, "blue": {"totalPoints": 40}})
    )
    assert base != outcome_fingerprint(_match(red_dqs=["frc254"], breakdown=bd))


def test_match_slot() -> None:
    slot = match_slot(_match(), _event(EventType.REGIONAL))
    assert slot.match_key == "2024casj_qm1"
    assert slot.year == 2024
    assert slot.time == int(datetime.datetime(2024, 3, 9, 17, 0).timestamp())
    assert slot.event_start == calendar.timegm(datetime.date(2024, 3, 8).timetuple())
    untimed = _match()
    untimed.actual_time = None
    assert match_slot(untimed, _event(EventType.REGIONAL)).time == int(
        datetime.datetime(2024, 3, 9, 16, 50).timestamp()
    )


def test_match_slot_with_a_placeholder_time() -> None:
    m = _match()
    m.actual_time = None
    m.time = datetime.datetime(1900, 1, 1, 0, 0)
    slot = match_slot(m, _event(EventType.REGIONAL))
    assert slot.time is not None and slot.time < 0
