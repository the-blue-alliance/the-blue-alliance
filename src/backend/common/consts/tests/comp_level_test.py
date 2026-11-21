from backend.common.consts.comp_level import (
    COMP_LEVELS_PLAY_ORDER,
    CompLevel,
    ELIM_LEVELS,
)


def test_elim_levels() -> None:
    assert ELIM_LEVELS == [CompLevel.EF, CompLevel.QF, CompLevel.SF, CompLevel.F]


def test_practice_plays_first() -> None:
    assert min(COMP_LEVELS_PLAY_ORDER, key=COMP_LEVELS_PLAY_ORDER.__getitem__) == (
        CompLevel.PM
    )
