from backend.common.consts.comp_level import CompLevel
from backend.common.consts.playoff_type import PlayoffType
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
