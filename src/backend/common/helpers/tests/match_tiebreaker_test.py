import json
import os

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.helpers.match_tiebreakers import MatchTiebreakers
from backend.common.models.alliance import MatchAlliance
from backend.common.models.match import Match


def get_path(path: str) -> str:
    this_dir = os.path.dirname(__file__)
    return os.path.join(this_dir, f"data/{path}")


def test_not_elim_match() -> None:
    m = Match(comp_level=CompLevel.QM,)
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
                    teams=["frc1", "frc2", "frc3"], score=-1,
                ),
                AllianceColor.BLUE: MatchAlliance(
                    teams=["frc4", "frc5", "frc6"], score=-1,
                ),
            }
        ),
    )
    assert MatchTiebreakers.tiebreak_winner(m) == ""


def test_2016_tiebreakers(test_data_importer) -> None:
    test_data_importer.import_match(get_path("2016cmp_f1m3.json"))
    match = Match.get_by_id("2016cmp_f1m3")
    assert match.winning_alliance == AllianceColor.RED


def test_2017_tiebreakers(test_data_importer) -> None:
    test_data_importer.import_match(get_path("2017dal_qf3m2.json"))
    match = Match.get_by_id("2017dal_qf3m2")
    assert match.winning_alliance == AllianceColor.RED


def test_2019_tiebreakers(test_data_importer) -> None:
    test_data_importer.import_match(get_path("2019hiho_qf4m1.json"))
    match = Match.get_by_id("2019hiho_qf4m1")
    assert match.winning_alliance == AllianceColor.RED


def test_2020_tiebreakers(test_data_importer) -> None:
    test_data_importer.import_match(get_path("2020mndu2_sf2m2.json"))
    match = Match.get_by_id("2020mndu2_sf2m2")
    assert match.winning_alliance == AllianceColor.BLUE
