from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import DOUBLE_ELIM_MAPPING, PlayoffType
from backend.common.helpers.playoff_type_helper import PlayoffTypeHelper


def test_BRACKET_8_TEAM() -> None:
    playoff_type = PlayoffType.BRACKET_8_TEAM

    # Qual
    for i in range(50):
        assert (
            PlayoffTypeHelper.get_comp_level(playoff_type, "Qualification", i + 1)
            == "qm"
        )
        assert PlayoffTypeHelper.get_set_match_number(
            playoff_type, CompLevel.QM, i + 1
        ) == (1, i + 1)

    # Playoff
    expected = [
        CompLevel.QF,
        CompLevel.QF,
        CompLevel.QF,
        CompLevel.QF,
        CompLevel.QF,
        CompLevel.QF,
        CompLevel.QF,
        CompLevel.QF,
        CompLevel.QF,
        CompLevel.QF,
        CompLevel.QF,
        CompLevel.QF,
        CompLevel.SF,
        CompLevel.SF,
        CompLevel.SF,
        CompLevel.SF,
        CompLevel.SF,
        CompLevel.SF,
        CompLevel.F,
        CompLevel.F,
        CompLevel.F,
    ]
    for i in range(21):
        assert (
            PlayoffTypeHelper.get_comp_level(playoff_type, "Playoff", i + 1)
            == expected[i]
        )

    assert PlayoffTypeHelper.get_set_match_number(playoff_type, CompLevel.QF, 1) == (
        1,
        1,
    )
    assert PlayoffTypeHelper.get_set_match_number(playoff_type, CompLevel.QF, 12) == (
        4,
        3,
    )
    assert PlayoffTypeHelper.get_set_match_number(playoff_type, CompLevel.SF, 13) == (
        1,
        1,
    )
    assert PlayoffTypeHelper.get_set_match_number(playoff_type, CompLevel.SF, 18) == (
        2,
        3,
    )
    assert PlayoffTypeHelper.get_set_match_number(playoff_type, CompLevel.F, 19) == (
        1,
        1,
    )
    assert PlayoffTypeHelper.get_set_match_number(playoff_type, CompLevel.F, 21) == (
        1,
        3,
    )


def test_ROUND_ROBIN_6_TEAM() -> None:
    playoff_type = PlayoffType.ROUND_ROBIN_6_TEAM

    # Qual
    for i in range(50):
        assert (
            PlayoffTypeHelper.get_comp_level(playoff_type, "Qualification", i + 1)
            == "qm"
        )
        assert PlayoffTypeHelper.get_set_match_number(
            playoff_type, CompLevel.QM, i + 1
        ) == (1, i + 1)

    # Playoff
    expected = [
        CompLevel.SF,
        CompLevel.SF,
        CompLevel.SF,
        CompLevel.SF,
        CompLevel.SF,
        CompLevel.SF,
        CompLevel.SF,
        CompLevel.SF,
        CompLevel.SF,
        CompLevel.SF,
        CompLevel.SF,
        CompLevel.SF,
        CompLevel.SF,
        CompLevel.SF,
        CompLevel.SF,
        CompLevel.F,
        CompLevel.F,
        CompLevel.F,
    ]
    for i in range(18):
        assert (
            PlayoffTypeHelper.get_comp_level(playoff_type, "Playoff", i + 1)
            == expected[i]
        )

    assert PlayoffTypeHelper.get_set_match_number(playoff_type, CompLevel.SF, 1) == (
        1,
        1,
    )
    assert PlayoffTypeHelper.get_set_match_number(playoff_type, CompLevel.SF, 15) == (
        1,
        15,
    )
    assert PlayoffTypeHelper.get_set_match_number(playoff_type, CompLevel.F, 16) == (
        1,
        1,
    )
    assert PlayoffTypeHelper.get_set_match_number(playoff_type, CompLevel.F, 18) == (
        1,
        3,
    )


def test_einstein_qualification_tagged_matches_route_to_playoff() -> None:
    # Championship (Einstein) events have no qualification phase, but the FMS
    # feed sometimes tags their playoff matches as "Qualification". At a
    # CMP_FINALS event those must map to the playoff bracket, not qm (#10102).
    # 2026 Einstein is an 8-alliance double-elimination bracket.
    playoff_type = PlayoffType.DOUBLE_ELIM_8_TEAM
    for i in range(1, 17):
        einstein = PlayoffTypeHelper.get_comp_level(
            playoff_type, "Qualification", i, EventType.CMP_FINALS
        )
        # Identical to the same match arriving tagged "Playoff".
        assert einstein == PlayoffTypeHelper.get_comp_level(playoff_type, "Playoff", i)
        assert einstein in (CompLevel.SF, CompLevel.F)
        assert einstein != CompLevel.QM
        # And the set/match numbering is the double-elim mapping, not the qm
        # (1, i) numbering it would have gotten while mislabeled.
        expected_level, expected_set, expected_match = DOUBLE_ELIM_MAPPING[i]
        assert einstein == expected_level
        assert PlayoffTypeHelper.get_set_match_number(playoff_type, einstein, i) == (
            expected_set,
            expected_match,
        )


def test_qualification_still_qm_for_non_cmp_finals_events() -> None:
    # Regression: real qualification matches at ordinary events are unaffected,
    # including championship DIVISIONS (which do run qualification matches) and
    # the default (no event_type) call path used everywhere else.
    playoff_type = PlayoffType.DOUBLE_ELIM_8_TEAM
    for i in range(1, 50):
        assert (
            PlayoffTypeHelper.get_comp_level(playoff_type, "Qualification", i)
            == CompLevel.QM
        )
        for event_type in (
            EventType.REGIONAL,
            EventType.DISTRICT,
            EventType.CMP_DIVISION,
        ):
            assert (
                PlayoffTypeHelper.get_comp_level(
                    playoff_type, "Qualification", i, event_type
                )
                == CompLevel.QM
            )
