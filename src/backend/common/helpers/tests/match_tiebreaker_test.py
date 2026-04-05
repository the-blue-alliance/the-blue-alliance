import json

import pytest

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.helpers.match_tiebreakers import MatchTiebreakers
from backend.common.models.alliance import MatchAlliance
from backend.common.models.match import Match


@pytest.fixture(autouse=True)
def auto_add_ndb_context(ndb_context) -> None:
    pass


def test_not_elim_match() -> None:
    m = Match(
        comp_level=CompLevel.QM,
    )
    assert MatchTiebreakers.tiebreak_winner(m) == ""


def test_no_breakdowns() -> None:
    m = Match(comp_level=CompLevel.SF)
    assert MatchTiebreakers.tiebreak_winner(m) == ""


def test_match_not_played() -> None:
    m = Match(
        comp_level=CompLevel.SF,
        alliances_json=json.dumps(
            {
                AllianceColor.RED: MatchAlliance(
                    teams=["frc1", "frc2", "frc3"],
                    score=-1,
                ),
                AllianceColor.BLUE: MatchAlliance(
                    teams=["frc4", "frc5", "frc6"],
                    score=-1,
                ),
            }
        ),
    )
    assert MatchTiebreakers.tiebreak_winner(m) == ""
