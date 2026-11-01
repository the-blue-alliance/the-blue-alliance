from typing import Optional

from backend.common.consts.comp_level import CompLevel
from backend.common.helpers.predictions_v2.ordering import (
    bracket_key,
    event_block_keys,
    event_block_order,
    MatchSlot,
)

DAY = 86400


def _slot(
    key: str,
    comp_level: CompLevel = CompLevel.QM,
    set_number: int = 1,
    match_number: int = 1,
    time: Optional[int] = None,
    year: int = 2024,
    start: Optional[int] = 1_700_000_000,
    end: Optional[int] = 1_700_000_000 + 2 * DAY,
) -> MatchSlot:
    return MatchSlot(
        match_key=key,
        event_key=key.split("_")[0],
        year=year,
        comp_level=comp_level,
        set_number=set_number,
        match_number=match_number,
        time=time,
        event_start=start,
        event_end=end,
    )


def _order(*slots: MatchSlot) -> list:
    return [slots[i].match_key for i in event_block_order(slots)]


def test_bracket_keys() -> None:
    # Best-of-3 playoffs play round by round, double elimination set by set.
    assert bracket_key(2019, CompLevel.QF, 2, 1) < bracket_key(2019, CompLevel.QF, 1, 2)
    assert bracket_key(2024, CompLevel.SF, 1, 2) < bracket_key(2024, CompLevel.SF, 2, 1)
    assert bracket_key(2024, CompLevel.QM, 1, 80) < bracket_key(
        2024, CompLevel.SF, 1, 1
    )
    assert bracket_key(2024, CompLevel.SF, 13, 1) < bracket_key(2024, CompLevel.F, 1, 1)


def test_bracket_order_inside_an_event_ignores_times() -> None:
    assert _order(
        _slot("2024a_qm2", match_number=2, time=100),
        _slot("2024a_qm1", match_number=1, time=200),
    ) == ["2024a_qm1", "2024a_qm2"]


def test_concurrent_events_interleave_by_running_max_time() -> None:
    order = _order(
        _slot("2024a_qm1", match_number=1, time=100),
        _slot("2024a_qm2", match_number=2, time=300),
        _slot("2024b_qm1", match_number=1, time=200),
        _slot("2024b_qm2", match_number=2, time=None),  # inherits 200
        _slot("2024b_qm3", match_number=3, time=400),
    )
    assert order == ["2024a_qm1", "2024b_qm1", "2024b_qm2", "2024a_qm2", "2024b_qm3"]


def test_untimed_event_spreads_over_its_dates() -> None:
    start = 1_700_000_000
    keys = event_block_keys(
        [
            _slot(f"2024u_qm{i}", match_number=i, start=start, end=start + DAY)
            for i in (1, 2)
        ]
    )
    assert keys[0][1] == start
    assert keys[1][1] == start + DAY  # half of the two-day span


def test_season_is_the_primary_key() -> None:
    assert _order(
        _slot("2025a_qm1", year=2025, time=1),
        _slot("2024a_qm1", year=2024, time=999),
    ) == ["2024a_qm1", "2025a_qm1"]


def test_replayed_match_follows_the_original() -> None:
    assert _order(
        _slot("2024a_sf1m2", CompLevel.SF, 1, 2, time=50),
        _slot("2024a_sf1m1", CompLevel.SF, 1, 1, time=100),
    ) == ["2024a_sf1m1", "2024a_sf1m2"]
