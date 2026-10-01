import datetime
import json
import math
from typing import Any, Dict, List, Optional

import numpy as np
import pytest
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import ALLIANCE_COLORS, AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.game_specific.registry import get_game
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.prediction_helper import (
    ContributionCalculator,
    PredictionHelper,
)
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_predictions import (
    EventPredictions,
    MatchPrediction,
    TMatchPredictions,
    TQualPlayoff,
    TRankingPrediction,
    TStatMeanVar,
)
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey, TeamKey
from backend.common.models.match import Match
from backend.common.models.team import Team


@pytest.mark.parametrize(
    "event_key",
    [
        "2020scmb",
        "2019nyny",
        "2018nyny",
        "2017nyny",
        "2016nyny",
    ],
)
def test_compute_match_predictions(event_key: EventKey, test_data_importer) -> None:
    test_data_importer.import_event(__file__, f"data/{event_key}.json")
    test_data_importer.import_match_list(__file__, f"data/{event_key}_matches.json")

    matches = Match.query(Match.event == ndb.Key(Event, event_key)).fetch()
    sorted_matches = MatchHelper.play_order_sorted_matches(matches)
    (
        match_predictions,
        match_prediction_stats,
        stat_mean_vars,
    ) = PredictionHelper.get_match_predictions(sorted_matches)

    assert match_predictions is not None
    assert match_prediction_stats is not None
    assert stat_mean_vars is not None


def test_past_event_seeds_match_predictions(test_data_importer) -> None:
    test_data_importer.import_event(__file__, "data/2019scmb.json")
    test_data_importer.import_event_predictions(
        __file__, "data/2019scmb_predictions.json", "2019scmb"
    )
    test_data_importer.import_event(__file__, "data/2019nyny.json")
    test_data_importer.import_match_list(__file__, "data/2019nyny_matches.json")

    matches = Match.query(Match.event == ndb.Key(Event, "2019nyny")).fetch()
    sorted_matches = MatchHelper.play_order_sorted_matches(matches)

    # 2019scmb (Feb 27) precedes 2019nyny (Apr 4) but shares no teams with it.
    # Enter every 2019nyny team at 2019scmb and give each the stats of one
    # real 2019scmb team, so the 2019nyny priors come from 2019scmb.
    details = none_throws(EventDetails.get_by_id("2019scmb"))
    predictions = none_throws(details.predictions)
    qual_stats = none_throws(predictions["stat_mean_vars"])["qual"]
    template = "frc1051"
    nyny_teams = {
        team
        for match in matches
        for color in ALLIANCE_COLORS
        for team in match.alliances[color]["teams"]
    }
    for team in nyny_teams:
        _put_event_team("2019scmb", team)
        for stat in qual_stats.values():
            stat["mean"][team] = stat["mean"][template]
            stat["var"][team] = stat["var"][template]
    details.predictions = predictions
    details.put()

    (
        match_predictions,
        match_prediction_stats,
        stat_mean_vars,
    ) = PredictionHelper.get_match_predictions(sorted_matches)

    assert match_predictions is not None
    assert match_prediction_stats is not None
    assert stat_mean_vars is not None

    # Before anything is played the estimate is exactly the seeded prior, so
    # the first match predicts three copies of the template team's score.
    first = none_throws(sorted_matches[0].key.string_id())
    first_prediction = match_predictions["qual"][first]
    for color in ALLIANCE_COLORS:
        assert math.isclose(
            first_prediction[color]["score"],  # pyre-ignore[6]
            3 * qual_stats["score"]["mean"][template],
        )


@pytest.mark.parametrize(
    "event_key",
    [
        "2020scmb",
        "2019nyny",
        "2018nyny",
        "2017nyny",
        "2016nyny",
    ],
)
def test_compute_match_predictions_with_none_score_breakdown(
    event_key: EventKey, test_data_importer
) -> None:
    """Regression test: played matches with None score_breakdown should not crash."""
    test_data_importer.import_event(__file__, f"data/{event_key}.json")
    test_data_importer.import_match_list(__file__, f"data/{event_key}_matches.json")

    matches = Match.query(Match.event == ndb.Key(Event, event_key)).fetch()

    # Null out score_breakdown on all played matches
    for match in matches:
        if match.has_been_played:
            match.score_breakdown_json = None
            match._score_breakdown = None

    sorted_matches = MatchHelper.play_order_sorted_matches(matches)
    (
        match_predictions,
        match_prediction_stats,
        stat_mean_vars,
    ) = PredictionHelper.get_match_predictions(sorted_matches)

    assert match_predictions is not None
    assert match_prediction_stats is not None
    assert stat_mean_vars is not None


@pytest.mark.parametrize(
    "event_key",
    [
        "2020scmb",
        "2019nyny",
        "2018nyny",
        "2017nyny",
        "2016nyny",
    ],
)
def test_compute_rankings_predictions(event_key: EventKey, test_data_importer) -> None:
    test_data_importer.import_event(__file__, f"data/{event_key}.json")
    test_data_importer.import_match_list(__file__, f"data/{event_key}_matches.json")
    with open(
        test_data_importer._get_path(__file__, f"data/{event_key}_predictions.json"),
        "r",
    ) as f:
        expected_predictions = json.load(f)

    matches = Match.query(Match.event == ndb.Key(Event, event_key)).fetch()
    sorted_matches = MatchHelper.play_order_sorted_matches(matches)
    (
        ranking_predictions,
        ranking_prediction_stats,
    ) = PredictionHelper.get_ranking_predictions(
        sorted_matches, expected_predictions["match_predictions"], n=1
    )

    assert ranking_predictions is not None
    assert ranking_prediction_stats is not None


@pytest.mark.parametrize(
    "event_key",
    [
        "2020scmb",
        "2019nyny",
        "2018nyny",
        "2017nyny",
        "2016nyny",
    ],
)
def test_compute_rankings_predictions_unplayed(
    event_key: EventKey, test_data_importer
) -> None:
    test_data_importer.import_event(__file__, f"data/{event_key}.json")
    test_data_importer.import_match_list(__file__, f"data/{event_key}_matches.json")
    with open(
        test_data_importer._get_path(__file__, f"data/{event_key}_predictions.json"),
        "r",
    ) as f:
        expected_predictions = json.load(f)

    matches = Match.query(Match.event == ndb.Key(Event, event_key)).fetch()
    sorted_matches = MatchHelper.play_order_sorted_matches(matches)

    def mark_unplayed(match: Match):
        alliances = match.alliances
        alliances[AllianceColor.RED]["score"] = -1
        alliances[AllianceColor.BLUE]["score"] = -1
        match.alliances_json = json.dumps(alliances)
        match._alliances = None

    # Leave the final qual match unplayed so the sampled-qual path runs.
    quals = [m for m in sorted_matches if m.comp_level == CompLevel.QM]
    mark_unplayed(quals[-1])

    (
        ranking_predictions,
        ranking_prediction_stats,
    ) = PredictionHelper.get_ranking_predictions(
        sorted_matches, expected_predictions["match_predictions"], n=1
    )

    assert ranking_predictions is not None
    assert ranking_prediction_stats is not None
    # The unplayed qual was sampled, not read as a result: the last played
    # match is the one before it.
    assert ranking_prediction_stats["last_played_match"] == quals[-2].key_name


# ---------------------------------------------------------------------------
# Synthetic-data helpers
# ---------------------------------------------------------------------------


def _make_event(
    event_key: EventKey,
    start_date: datetime.datetime,
    event_type: EventType = EventType.REGIONAL,
) -> Event:
    event = Event(
        id=event_key,
        year=int(event_key[:4]),
        event_short=event_key[4:],
        event_type_enum=event_type,
        start_date=start_date,
        end_date=start_date + datetime.timedelta(days=2),
    )
    event.put()
    return event


def _make_match(
    event_key: EventKey,
    match_number: int,
    red_teams: List[TeamKey],
    blue_teams: List[TeamKey],
    red_score: int,
    blue_score: int,
    score_breakdown: Optional[Dict[str, Dict[str, Any]]] = None,
    comp_level: CompLevel = CompLevel.QM,
) -> Match:
    alliances = {
        AllianceColor.RED: {"teams": red_teams, "score": red_score},
        AllianceColor.BLUE: {"teams": blue_teams, "score": blue_score},
    }
    return Match(
        id=Match.render_key_name(event_key, comp_level, 1, match_number),
        event=ndb.Key(Event, event_key),
        year=int(event_key[:4]),
        comp_level=comp_level,
        set_number=1,
        match_number=match_number,
        team_key_names=red_teams + blue_teams,
        alliances_json=json.dumps(alliances),
        score_breakdown_json=(
            json.dumps(score_breakdown) if score_breakdown is not None else None
        ),
    )


LEVELS: List[TQualPlayoff] = ["qual", "playoff"]
RED_TEAMS: List[TeamKey] = ["frc1", "frc2", "frc3"]
BLUE_TEAMS: List[TeamKey] = ["frc4", "frc5", "frc6"]


# ---------------------------------------------------------------------------
# get_match_predictions: modern seasons and edge cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "event_key",
    [
        "2026marea",
        "2023onlon",
        "2022on305",
    ],
)
def test_compute_match_predictions_modern_seasons(
    event_key: EventKey, test_data_importer
) -> None:
    test_data_importer.import_event(__file__, f"data/{event_key}.json")
    test_data_importer.import_match_list(__file__, f"data/{event_key}_matches.json")

    matches = Match.query(Match.event == ndb.Key(Event, event_key)).fetch()
    sorted_matches = MatchHelper.play_order_sorted_matches(matches)
    (
        match_predictions,
        match_prediction_stats,
        stat_mean_vars,
    ) = PredictionHelper.get_match_predictions(sorted_matches)

    assert match_predictions is not None
    assert match_prediction_stats is not None
    assert stat_mean_vars is not None

    game = get_game(int(event_key[:4]))
    expected_stats = {s for s, _, _ in game.get_prediction_relevant_stats()}
    assert set(stat_mean_vars["qual"].keys()) == expected_stats
    assert set(stat_mean_vars["playoff"].keys()) == expected_stats

    # Every match got a prediction carrying the game's bonus RP probabilities
    assert len(match_predictions["qual"]) + len(match_predictions["playoff"]) == len(
        sorted_matches
    )
    for level in LEVELS:
        for prediction in match_predictions[level].values():
            for color in ALLIANCE_COLORS:
                color_prediction = prediction[color]  # pyre-ignore[6]
                for prob_key in game.ranking_bonus_rp_prediction_fields():
                    assert 0.0 <= color_prediction[prob_key] <= 1.0
            assert 0.5 <= prediction["prob"] <= 1.0

    # Every played match contributed to the win/loss Brier score
    assert "win_loss" in match_prediction_stats["qual"]["brier_scores"]
    assert match_prediction_stats["qual"]["wl_accuracy"] is not None


@pytest.mark.parametrize(
    "event_key, secondary_stat, prob_key",
    [
        # 2024 MELODY: threshold drops with the Coopertition Bonus.
        ("2024nytr", "coopertition_criteria", "prob_melody_bonus"),
        # 2024 ENSEMBLE: needs at least 2 ONSTAGE ROBOTS.
        ("2024nytr", "robot_on_stage", "prob_ensemble_bonus"),
        # 2025 CORAL: threshold drops with the Coopertition Bonus.
        ("2025isde1", "coopertition_criteria", "prob_coral_bonus"),
    ],
)
def test_bonus_predictions_compute_their_secondary_stats(
    event_key: EventKey,
    secondary_stat: str,
    prob_key: str,
    test_data_importer,
) -> None:
    """Every stat a bonus RP prediction reads is computed (2024 Manual 6.5.6)."""
    game = get_game(int(event_key[:4]))
    assert secondary_stat in {s for s, _, _ in game.get_prediction_relevant_stats()}

    test_data_importer.import_event(__file__, f"data/{event_key}.json")
    test_data_importer.import_match_list(__file__, f"data/{event_key}_matches.json")
    matches = Match.query(Match.event == ndb.Key(Event, event_key)).fetch()
    sorted_matches = MatchHelper.play_order_sorted_matches(matches)

    (
        match_predictions,
        _match_prediction_stats,
        stat_mean_vars,
    ) = PredictionHelper.get_match_predictions(sorted_matches)

    assert match_predictions is not None
    assert stat_mean_vars is not None
    assert secondary_stat in stat_mean_vars["qual"]
    probs = [
        prediction[color][prob_key]  # pyre-ignore[6]
        for level in LEVELS
        for prediction in match_predictions[level].values()
        for color in ALLIANCE_COLORS
    ]
    assert probs
    assert all(0.0 <= p <= 1.0 for p in probs)
    assert any(p > 0.0 for p in probs)


@pytest.mark.parametrize(
    "red_mean, blue_mean, low, high",
    [
        # Both ALLIANCES reliably meet their half: the bonus is likely.
        (1.0, 1.0, 0.9, 1.0),
        # One ALLIANCE never does: no bonus, however keen the other is.
        (1.0, 0.0, 0.0, 0.1),
        (0.0, 1.0, 0.0, 0.1),
    ],
)
def test_coopertition_bonus_needs_both_alliances(
    red_mean: float, blue_mean: float, low: float, high: float
) -> None:
    """Coopertition needs both alliances (2024 Manual 6.5.5, 2025 Manual 6.5.3)."""
    mean_vars = {
        "red": {"coopertition_criteria": {"mean": red_mean, "var": 0.01}},
        "blue": {"coopertition_criteria": {"mean": blue_mean, "var": 0.01}},
    }
    prob = PredictionHelper._prob_coopertition_bonus(mean_vars)
    assert low <= prob <= high


def test_get_match_predictions_no_matches() -> None:
    assert PredictionHelper.get_match_predictions([]) == (None, None, None)


@pytest.mark.filterwarnings("ignore:invalid value")
def test_predict_match_nan_probability_falls_back_to_coin_flip() -> None:
    """
    With identical zero-variance predictions for both alliances the win
    probability is 0/0 (nan); it is reported as 0.5 and red is chosen as
    the winner of a predicted tie.
    """
    event = _make_event("2019test", datetime.datetime(2019, 3, 1))
    match = _make_match("2019test", 1, RED_TEAMS, BLUE_TEAMS, -1, -1)
    stat_mean_vars: TStatMeanVar = {
        "score": {
            "mean": {t: 0.0 for t in RED_TEAMS + BLUE_TEAMS},
            "var": {t: 0.0 for t in RED_TEAMS + BLUE_TEAMS},
        }
    }

    prediction = PredictionHelper._predict_match(event, match, stat_mean_vars, False)

    assert prediction["prob"] == 0.5
    assert prediction["winning_alliance"] == AllianceColor.RED
    assert prediction["red"] == {"score": 0.0, "score_var": 0.0}
    assert prediction["blue"] == {"score": 0.0, "score_var": 0.0}


# ---------------------------------------------------------------------------
# ContributionCalculator: per-stat extraction from score breakdowns
# ---------------------------------------------------------------------------


def _rocket(**overrides: str) -> Dict[str, str]:
    breakdown = {
        f"{level}{side2}Rocket{side1}": "None"
        for side1 in ("Far", "Near")
        for side2 in ("Left", "Right")
        for level in ("low", "mid", "top")
    }
    breakdown.update(overrides)
    return breakdown


@pytest.mark.parametrize(
    "stat, red_breakdown, blue_breakdown, expected_red, expected_blue",
    [
        # Generic score: 2016/2017 playoff bonus points are removed
        (
            "score",
            {"breachPoints": 20, "capturePoints": 25},
            {"kPaBonusPoints": 20, "rotorBonusPoints": 100},
            100 - 20 - 25,
            60 - 20 - 100,
        ),
        ("score", {}, {}, 100, 60),
        ("auto_points", {"autoPoints": 12}, {"autoPoints": 7}, 12, 7),
        # 2016
        (
            "boulders",
            {
                "autoBouldersLow": 1,
                "autoBouldersHigh": 2,
                "teleopBouldersLow": 3,
                "teleopBouldersHigh": 4,
            },
            {"teleopBouldersHigh": 5},
            10,
            5,
        ),
        (
            "crossings",
            {
                "position1crossings": 1,
                "position2crossings": 2,
                "position3crossings": 3,
                "position4crossings": 4,
                "position5crossings": 5,
            },
            {"position2crossings": 2},
            15,
            2,
        ),
        # 2017
        (
            "pressure",
            {
                "autoFuelHigh": 9,
                "autoFuelLow": 9,
                "teleopFuelHigh": 9,
                "teleopFuelLow": 9,
            },
            {},
            9 + 3 + 3 + 1,
            0,
        ),
        ("gears", {"rotor4Engaged": True}, {"rotor3Engaged": True}, 12, 6),
        ("gears", {"rotor2Auto": True}, {"rotor2Engaged": True}, 3, 2),
        ("gears", {"rotor1Auto": True}, {"rotor1Engaged": True}, 1, 0),
        ("gears", {}, {"rotor4Engaged": False}, -1, -1),
        # 2018
        ("endgame_points", {"endgamePoints": 30}, {"endgamePoints": 0}, 30, 0),
        # 2019
        (
            "rocket_pieces_scored",
            _rocket(lowLeftRocketFar="Cargo", midRightRocketNear="Panel"),
            _rocket(topLeftRocketNear="PanelAndCargo"),
            3,
            2,
        ),
        ("hab_climb_points", {"habClimbPoints": 15}, {"habClimbPoints": 3}, 15, 3),
        # 2020
        (
            "power_cells_scored",
            {
                "autoCellsBottom": 1,
                "autoCellsOuter": 2,
                "autoCellsInner": 3,
                "teleopCellsBottom": 4,
                "teleopCellsOuter": 5,
                "teleopCellsInner": 6,
            },
            {
                "autoCellsBottom": 0,
                "autoCellsOuter": 0,
                "autoCellsInner": 0,
                "teleopCellsBottom": 0,
                "teleopCellsOuter": 0,
                "teleopCellsInner": 0,
            },
            21,
            0,
        ),
        # 2022: five or more auto cargo approximates the quintet (+2)
        (
            "cargo_scored",
            {
                **{
                    f"autoCargo{goal}{exit}": 1
                    for goal in ("Lower", "Upper")
                    for exit in ("Near", "Far", "Red", "Blue")
                },
                **{
                    f"teleopCargo{goal}{exit}": 2
                    for goal in ("Lower", "Upper")
                    for exit in ("Near", "Far", "Red", "Blue")
                },
            },
            {
                **{
                    f"autoCargo{goal}{exit}": 0
                    for goal in ("Lower", "Upper")
                    for exit in ("Near", "Far", "Red", "Blue")
                },
                "autoCargoLowerNear": 4,
                **{
                    f"teleopCargo{goal}{exit}": 1
                    for goal in ("Lower", "Upper")
                    for exit in ("Near", "Far", "Red", "Blue")
                },
            },
            8 + 2 + 16,
            4 + 8,
        ),
        # 2023
        (
            "game_piece_scored",
            {"autoGamePieceCount": 3, "teleopGamePieceCount": 12},
            {"autoGamePieceCount": 0, "teleopGamePieceCount": 4},
            15,
            4,
        ),
        ("links", {"linkPoints": 17}, {"linkPoints": 0}, 3, 0),
        (
            "charge_station_points",
            {"totalChargeStationPoints": 26},
            {"totalChargeStationPoints": 12},
            26,
            12,
        ),
        # 2024
        (
            "note_scored",
            {
                "autoAmpNoteCount": 1,
                "autoSpeakerNoteCount": 2,
                "teleopAmpNoteCount": 3,
                "teleopSpeakerNoteCount": 4,
                "teleopSpeakerNoteAmplifiedCount": 5,
            },
            {
                "autoAmpNoteCount": 0,
                "autoSpeakerNoteCount": 0,
                "teleopAmpNoteCount": 0,
                "teleopSpeakerNoteCount": 0,
                "teleopSpeakerNoteAmplifiedCount": 0,
            },
            15,
            0,
        ),
        (
            "stage_points",
            {"endGameTotalStagePoints": 10},
            {"endGameTotalStagePoints": 2},
            10,
            2,
        ),
        (
            "coopertition_criteria",
            {"coopertitionCriteriaMet": True},
            {"coopertitionCriteriaMet": False},
            1,
            0,
        ),
        # 2025: Coopertition is 2+ ALGAE in the ALLIANCE's PROCESSOR (6.5.3),
        # whatever FMS reports in coopertitionCriteriaMet.
        (
            "coopertition_criteria",
            {"wallAlgaeCount": 2, "coopertitionCriteriaMet": False},
            {"wallAlgaeCount": 1, "coopertitionCriteriaMet": True},
            1,
            0,
        ),
        ("auto_coral_scored", {"autoCoralCount": 4}, {"autoCoralCount": 1}, 4, 1),
        ("coral_scored", {"teleopCoralCount": 22}, {"teleopCoralCount": 9}, 22, 9),
        ("barge_points", {"endGameBargePoints": 14}, {"endGameBargePoints": 2}, 14, 2),
        # 2026
        ("totalAutoPoints", {"totalAutoPoints": 18}, {"totalAutoPoints": 5}, 18, 5),
        (
            "totalTeleopPoints",
            {"totalTeleopPoints": 40},
            {"totalTeleopPoints": 25},
            40,
            25,
        ),
        (
            "endGameTowerPoints",
            {"endGameTowerPoints": 15},
            {"endGameTowerPoints": 0},
            15,
            0,
        ),
    ],
)
def test_contribution_calculator_extracts_stat(
    stat: str,
    red_breakdown: Dict[str, Any],
    blue_breakdown: Dict[str, Any],
    expected_red: float,
    expected_blue: float,
) -> None:
    # The extractor only looks at the breakdown keys for the requested stat, so
    # a single generic event serves every season's stat.
    event = _make_event("2019test", datetime.datetime(2019, 3, 1))
    match = _make_match(
        "2019test",
        1,
        RED_TEAMS,
        BLUE_TEAMS,
        100,
        60,
        {"red": red_breakdown, "blue": blue_breakdown},
    )
    calculator = ContributionCalculator(event, [match], stat, 10, 5**2)

    result = calculator.calculate_before_match(0)

    assert calculator._mean_sums == [expected_red, expected_blue]
    assert set(result["mean"].keys()) == set(RED_TEAMS + BLUE_TEAMS)
    assert set(result["var"].keys()) == set(RED_TEAMS + BLUE_TEAMS)
    # No past stats and nothing accumulated yet: the prior is the default
    for team in RED_TEAMS + BLUE_TEAMS:
        assert math.isclose(result["mean"][team], 10)
        assert math.isclose(result["var"][team], 5**2)


def test_contribution_calculator_unknown_stat() -> None:
    event = _make_event("2019test", datetime.datetime(2019, 3, 1))
    match = _make_match(
        "2019test", 1, RED_TEAMS, BLUE_TEAMS, 100, 60, {"red": {}, "blue": {}}
    )
    calculator = ContributionCalculator(event, [match], "bogus_stat", 10, 5**2)

    with pytest.raises(Exception, match="Unknown stat: bogus_stat"):
        calculator.calculate_before_match(0)


def test_contribution_calculator_skips_unplayed_and_breakdownless_matches() -> None:
    event = _make_event("2019test", datetime.datetime(2019, 3, 1))
    unplayed = _make_match("2019test", 1, RED_TEAMS, BLUE_TEAMS, -1, -1)
    no_breakdown = _make_match("2019test", 2, RED_TEAMS, BLUE_TEAMS, 100, 60)
    calculator = ContributionCalculator(
        event, [unplayed, no_breakdown], "score", 10, 5**2
    )

    calculator.calculate_before_match(0)
    calculator.calculate_before_match(1)

    assert calculator._mean_sums == []
    assert calculator._var_sums == []


# ---------------------------------------------------------------------------
# ContributionCalculator: priors seeded from earlier events in the season
# ---------------------------------------------------------------------------


def _put_event_predictions(event_key: EventKey, qual_stats: TStatMeanVar) -> None:
    EventDetails(
        id=event_key,
        predictions=EventPredictions(
            match_predictions=None,
            match_prediction_stats=None,
            stat_mean_vars={"qual": qual_stats, "playoff": {}},
            ranking_predictions=None,
            ranking_prediction_stats=None,
        ),
    ).put()


def _put_event_team(event_key: EventKey, team_key: TeamKey) -> None:
    EventTeam(
        id=f"{event_key}_{team_key}",
        event=ndb.Key(Event, event_key),
        team=ndb.Key(Team, team_key),
        year=int(event_key[:4]),
    ).put()


def test_contribution_calculator_seeds_priors_from_past_events() -> None:
    """
    Teams that already played an event this season start from the means and
    variances computed there; teams without history start from the average
    of the other teams' past means (and the default variance).
    """
    current = _make_event("2019cur", datetime.datetime(2019, 4, 1))

    # An earlier regional with predictions for frc1 and frc2 (not frc3)
    _make_event("2019past", datetime.datetime(2019, 3, 1))
    _put_event_predictions(
        "2019past",
        {
            "score": {
                "mean": {"frc1": 30.0, "frc2": 40.0},
                "var": {"frc1": 9.0, "frc2": 16.0},
            }
        },
    )
    for team in ("frc1", "frc2", "frc3"):
        _put_event_team("2019past", team)

    # An even earlier regional with no details at all
    _make_event("2019empty", datetime.datetime(2019, 2, 20))
    _put_event_team("2019empty", "frc1")

    # A later event and a championship finals event must not contribute
    _make_event("2019later", datetime.datetime(2019, 4, 20))
    _put_event_predictions(
        "2019later", {"score": {"mean": {"frc1": 999.0}, "var": {"frc1": 999.0}}}
    )
    _put_event_team("2019later", "frc1")
    _make_event("2019cmp", datetime.datetime(2019, 3, 15), EventType.CMP_FINALS)
    _put_event_predictions(
        "2019cmp", {"score": {"mean": {"frc1": 999.0}, "var": {"frc1": 999.0}}}
    )
    _put_event_team("2019cmp", "frc1")

    match = _make_match("2019cur", 1, RED_TEAMS, BLUE_TEAMS, -1, -1)
    calculator = ContributionCalculator(current, [match], "score", 10, 20**2)

    assert dict(calculator._past_stats_mean) == {"frc1": [30.0], "frc2": [40.0]}
    assert dict(calculator._past_stats_var) == {"frc1": [9.0], "frc2": [16.0]}

    # Before any match is played the MMSE estimate is exactly the prior
    result = calculator.calculate_before_match(0)
    assert math.isclose(result["mean"]["frc1"], 30.0)
    assert math.isclose(result["mean"]["frc2"], 40.0)
    assert math.isclose(result["var"]["frc1"], 9.0)
    assert math.isclose(result["var"]["frc2"], 16.0)
    for team in ("frc3", "frc4", "frc5", "frc6"):
        assert math.isclose(result["mean"][team], (30.0 + 40.0) / 2)
        assert math.isclose(result["var"][team], 20**2)


# ---------------------------------------------------------------------------
# get_ranking_predictions
# ---------------------------------------------------------------------------


def _dummy_match_predictions(match_key: str) -> TMatchPredictions:
    return {
        "qual": {
            match_key: MatchPrediction(
                winning_alliance=AllianceColor.RED, prob=0.6, red={}, blue={}
            )
        },
        "playoff": {},
    }


def test_get_ranking_predictions_without_qual_matches() -> None:
    playoff = _make_match(
        "2019test", 1, RED_TEAMS, BLUE_TEAMS, 100, 60, comp_level=CompLevel.QF
    )
    predictions = _dummy_match_predictions("2019test_qm1")

    assert PredictionHelper.get_ranking_predictions([], predictions) == (None, None)
    assert PredictionHelper.get_ranking_predictions([playoff], predictions) == (
        None,
        None,
    )


def test_get_ranking_predictions_without_match_predictions() -> None:
    match = _make_match("2019test", 1, RED_TEAMS, BLUE_TEAMS, 100, 60)

    assert PredictionHelper.get_ranking_predictions([match], None) == (None, None)
    assert PredictionHelper.get_ranking_predictions(
        [match], {"qual": {}, "playoff": {}}
    ) == (None, None)


def test_get_ranking_predictions_played_match_without_breakdown() -> None:
    match = _make_match("2019test", 1, RED_TEAMS, BLUE_TEAMS, 100, 60)
    predictions = _dummy_match_predictions("2019test_qm1")

    assert PredictionHelper.get_ranking_predictions([match], predictions) == (
        None,
        None,
    )


def test_get_ranking_predictions_ties_and_surrogates() -> None:
    """
    A win gives the game's win RPs, a tie gives 1 RP, and each achieved bonus
    gives 1 RP. Surrogate teams (those playing more matches than the minimum)
    earn nothing from their third match.
    """
    _make_event("2026test", datetime.datetime(2026, 3, 1))
    empty: Dict[str, Dict[str, Any]] = {"red": {}, "blue": {}}
    all_bonuses = {
        "red": {
            "energizedAchieved": True,
            "superchargedAchieved": True,
            "traversalAchieved": True,
        },
        "blue": {},
    }
    matches = [
        _make_match(
            "2026test",
            1,
            ["frc1", "frc2", "frc3"],
            ["frc4", "frc5", "frc6"],
            10,
            5,
            all_bonuses,
        ),
        _make_match(
            "2026test",
            2,
            ["frc1", "frc4", "frc7"],
            ["frc2", "frc5", "frc6"],
            10,
            5,
            empty,
        ),
        # Tie, and the third match for surrogates frc2, frc4 and frc5
        _make_match(
            "2026test",
            3,
            ["frc1", "frc2", "frc3"],
            ["frc4", "frc5", "frc7"],
            7,
            7,
            empty,
        ),
        _make_match(
            "2026test",
            4,
            ["frc2", "frc3", "frc7"],
            ["frc4", "frc5", "frc6"],
            5,
            10,
            empty,
        ),
    ]
    predictions = _dummy_match_predictions("2026test_qm1")

    ranking_predictions, ranking_stats = PredictionHelper.get_ranking_predictions(
        matches, predictions, n=1
    )

    assert ranking_stats == {"last_played_match": "2026test_qm4"}
    assert ranking_predictions is not None
    rps = {team: prediction.max_rp for team, prediction in ranking_predictions}
    win = get_game(2026).ranking_win_points()
    assert rps == {
        "frc1": (win + 3) + win + 1,
        "frc2": (win + 3),
        "frc3": (win + 3) + 1,
        "frc4": win + win,
        "frc5": win,
        "frc6": win,
        "frc7": win + 1,
    }
    assert [team for team, _ in ranking_predictions[:2]] == ["frc1", "frc3"]
    top_rp = 2 * win + 4
    assert ranking_predictions[0][1] == TRankingPrediction(
        1, 1, 1, 1, float(top_rp), top_rp, top_rp
    )


def test_compute_rankings_predictions_from_computed_predictions_unplayed(
    test_data_importer,
) -> None:
    """
    Feed get_match_predictions output into get_ranking_predictions with the
    last qual match unplayed, so its outcome and three bonus RPs are sampled.
    """
    event_key = "2026marea"
    test_data_importer.import_event(__file__, f"data/{event_key}.json")
    test_data_importer.import_match_list(__file__, f"data/{event_key}_matches.json")

    matches = Match.query(Match.event == ndb.Key(Event, event_key)).fetch()
    sorted_matches = MatchHelper.play_order_sorted_matches(matches)
    qual_matches = [m for m in sorted_matches if m.comp_level == CompLevel.QM]
    last_qual = qual_matches[-1]

    alliances = last_qual.alliances
    alliances[AllianceColor.RED]["score"] = -1
    alliances[AllianceColor.BLUE]["score"] = -1
    last_qual.alliances_json = json.dumps(alliances)
    last_qual._alliances = None
    assert not last_qual.has_been_played

    match_predictions, _, _ = PredictionHelper.get_match_predictions(sorted_matches)
    assert match_predictions is not None
    # Make the unplayed match a coin flip so both outcomes get sampled
    match_predictions["qual"][last_qual.key_name]["prob"] = 0.5

    np.random.seed(0)
    ranking_predictions, ranking_stats = PredictionHelper.get_ranking_predictions(
        sorted_matches, match_predictions, n=20
    )

    assert ranking_stats == {"last_played_match": qual_matches[-2].key_name}
    assert ranking_predictions is not None
    teams = {
        t
        for m in qual_matches
        for c in ALLIANCE_COLORS
        for t in m.alliances[c]["teams"]
    }
    assert {team for team, _ in ranking_predictions} == teams
    ranks = [prediction.avg_rank for _, prediction in ranking_predictions]
    assert ranks == sorted(ranks)
    assert all(
        1 <= p.min_rank <= p.max_rank <= len(teams) for _, p in ranking_predictions
    )
