from backend.common.helpers.insights_v2.match_alliance_points import (
    get_auto_points,
    get_endgame_points,
    get_game_piece_count,
    get_teleop_points,
    MatchAlliancePoints,
)


def _pts(breakdown, year=2024):
    return MatchAlliancePoints(score=0, breakdown=breakdown, year=year)


class TestGetAutoPoints:
    def test_none_breakdown(self):
        assert get_auto_points(_pts(None)) is None

    def test_auto_points_field(self):
        assert get_auto_points(_pts({"autoPoints": 42})) == 42

    def test_total_auto_points_field_2026(self):
        assert get_auto_points(_pts({"totalAutoPoints": 30}, year=2026)) == 30

    def test_auto_points_preferred_over_total(self):
        assert get_auto_points(_pts({"autoPoints": 10, "totalAutoPoints": 99})) == 10

    def test_no_matching_field(self):
        assert get_auto_points(_pts({"teleopPoints": 5})) is None

    def test_zero_score(self):
        assert get_auto_points(_pts({"autoPoints": 0})) == 0


class TestGetTeleopPoints:
    def test_none_breakdown(self):
        assert get_teleop_points(_pts(None)) is None

    def test_teleop_points_field(self):
        assert get_teleop_points(_pts({"teleopPoints": 55})) == 55

    def test_total_teleop_points_field_2026(self):
        assert get_teleop_points(_pts({"totalTeleopPoints": 40}, year=2026)) == 40

    def test_teleop_points_preferred_over_total(self):
        assert (
            get_teleop_points(_pts({"teleopPoints": 10, "totalTeleopPoints": 99})) == 10
        )

    def test_no_matching_field(self):
        assert get_teleop_points(_pts({"autoPoints": 5})) is None

    def test_zero_score(self):
        assert get_teleop_points(_pts({"teleopPoints": 0})) == 0


class TestGetEndgamePoints:
    def test_none_breakdown(self):
        assert get_endgame_points(_pts(None)) is None

    def test_year_without_endgame_field(self):
        # 2015 has no endgame points field
        assert get_endgame_points(_pts({"autoPoints": 10}, year=2015)) is None

    def test_endgame_2016_challenge_plus_scale(self):
        bd = {"teleopChallengePoints": 5, "teleopScalePoints": 15}
        assert get_endgame_points(_pts(bd, year=2016)) == 20

    def test_endgame_2017_takeoff(self):
        assert get_endgame_points(_pts({"teleopTakeoffPoints": 30}, year=2017)) == 30

    def test_endgame_points_2018(self):
        assert get_endgame_points(_pts({"endgamePoints": 30}, year=2018)) == 30

    def test_endgame_points_2022(self):
        assert get_endgame_points(_pts({"endgamePoints": 20}, year=2022)) == 20

    def test_endgame_multi_key_sum_2023(self):
        bd = {"endGameChargeStationPoints": 10, "endGameParkPoints": 2}
        assert get_endgame_points(_pts(bd, year=2023)) == 12

    def test_endgame_2024(self):
        assert (
            get_endgame_points(_pts({"endGameTotalStagePoints": 15}, year=2024)) == 15
        )

    def test_endgame_2019_hab_climb(self):
        assert get_endgame_points(_pts({"habClimbPoints": 12}, year=2019)) == 12

    def test_endgame_2025(self):
        assert get_endgame_points(_pts({"endGameBargePoints": 8}, year=2025)) == 8

    def test_endgame_2026(self):
        assert get_endgame_points(_pts({"endGameTowerPoints": 12}, year=2026)) == 12

    def test_missing_key_treated_as_zero(self):
        # 2023: one key present, one missing → counts the present one only
        bd = {"endGameChargeStationPoints": 10}
        assert get_endgame_points(_pts(bd, year=2023)) == 10

    def test_zero_score(self):
        assert get_endgame_points(_pts({"endGameTotalStagePoints": 0}, year=2024)) == 0


_2019_PRELOAD_BAYS = (1, 2, 3, 6, 7, 8)
_2019_ROCKET_KEYS = [
    f"{level}{lr_side}Rocket{nf_side}"
    for level in ("low", "mid", "top")
    for lr_side in ("Left", "Right")
    for nf_side in ("Near", "Far")
]


def _2019_breakdown(overrides=None):
    # A baseline breakdown that nets to 0 game pieces: preloadable bays keep
    # their preloaded Panel (not scored), non-preloadable bays/rockets are
    # empty. Pass overrides to change specific bay/rocket/preload values.
    bd = {}
    for i in range(1, 9):
        if i in _2019_PRELOAD_BAYS:
            bd[f"preMatchBay{i}"] = "Panel"
            bd[f"bay{i}"] = "Panel"
        else:
            bd[f"bay{i}"] = "None"
    for key in _2019_ROCKET_KEYS:
        bd[key] = "None"
    if overrides:
        bd.update(overrides)
    return bd


class TestGetGamePieceCount:
    def test_none_breakdown(self):
        assert get_game_piece_count(_pts(None)) is None

    def test_unsupported_year(self):
        assert get_game_piece_count(_pts({"totalPoints": 10}, year=2018)) is None

    def test_2016_boulders(self):
        bd = {
            "autoBouldersLow": 1,
            "autoBouldersHigh": 2,
            "teleopBouldersLow": 3,
            "teleopBouldersHigh": 4,
        }
        assert get_game_piece_count(_pts(bd, year=2016)) == 10

    def test_2016_missing_field(self):
        assert get_game_piece_count(_pts({"autoBouldersLow": 1}, year=2016)) is None

    def test_2017_fuel(self):
        bd = {
            "autoFuelLow": 1,
            "autoFuelHigh": 2,
            "teleopFuelLow": 3,
            "teleopFuelHigh": 4,
        }
        assert get_game_piece_count(_pts(bd, year=2017)) == 10

    def test_2019_preload_panel_stays_panel_scores_zero(self):
        # Preloaded with a Panel, still just a Panel at the end -> nothing scored.
        bd = _2019_breakdown(overrides={"preMatchBay1": "Panel", "bay1": "Panel"})
        assert get_game_piece_count(_pts(bd, year=2019)) == 0

    def test_2019_preload_panel_plus_cargo_scores_one(self):
        # Preloaded with a Panel, Cargo added during the match -> 1 piece scored.
        bd = _2019_breakdown(
            overrides={"preMatchBay1": "Panel", "bay1": "PanelAndCargo"}
        )
        assert get_game_piece_count(_pts(bd, year=2019)) == 1

    def test_2019_preload_cargo_ends_panel_scores_one(self):
        # Preloaded with Cargo, ends as just a Panel -> 1 piece scored (the
        # preload isn't a Panel, so nothing is subtracted from the final count).
        bd = _2019_breakdown(overrides={"preMatchBay1": "Cargo", "bay1": "Panel"})
        assert get_game_piece_count(_pts(bd, year=2019)) == 1

    def test_2019_preload_cargo_ends_panel_and_cargo_scores_two(self):
        # Preloaded with Cargo, ends with both Panel and Cargo -> 2 pieces scored.
        bd = _2019_breakdown(
            overrides={"preMatchBay1": "Cargo", "bay1": "PanelAndCargo"}
        )
        assert get_game_piece_count(_pts(bd, year=2019)) == 2

    def test_2019_rocket_pieces_counted_directly(self):
        # Rocket slots have no preload, so every piece present is scored.
        bd = _2019_breakdown(
            overrides={"lowLeftRocketNear": "Panel", "topRightRocketFar": "Cargo"}
        )
        assert get_game_piece_count(_pts(bd, year=2019)) == 2

    def test_2019_bay_4_and_5_always_preloaded_with_cargo(self):
        # bay4/bay5 are always preloaded with Cargo (no choice, no preMatchBay
        # field), so the same "Cargo preload isn't subtracted" rule applies as
        # for the chosen-preload bays: a Panel added alongside it scores 2.
        bd = _2019_breakdown(overrides={"bay4": "PanelAndCargo"})
        assert get_game_piece_count(_pts(bd, year=2019)) == 2

    def test_2019_bay_4_and_5_unchanged_cargo_still_counts(self):
        # Consistent with the Cargo-preload rule elsewhere: an untouched
        # preloaded Cargo in bay4/bay5 is still counted (only Panel preloads
        # are excluded from the count).
        bd = _2019_breakdown(overrides={"bay4": "Cargo"})
        assert get_game_piece_count(_pts(bd, year=2019)) == 1

    def test_2019_missing_bay_field(self):
        bd = _2019_breakdown()
        del bd["bay8"]
        assert get_game_piece_count(_pts(bd, year=2019)) is None

    def test_2019_missing_preload_field(self):
        bd = _2019_breakdown()
        del bd["preMatchBay1"]
        assert get_game_piece_count(_pts(bd, year=2019)) is None

    def test_2020_power_cells(self):
        bd = {
            "autoCellsBottom": 1,
            "autoCellsOuter": 2,
            "autoCellsInner": 3,
            "teleopCellsBottom": 4,
            "teleopCellsOuter": 5,
            "teleopCellsInner": 6,
        }
        assert get_game_piece_count(_pts(bd, year=2020)) == 21

    def test_2022_cargo(self):
        assert get_game_piece_count(_pts({"matchCargoTotal": 15}, year=2022)) == 15

    def test_2023_game_pieces(self):
        bd = {"autoGamePieceCount": 4, "teleopGamePieceCount": 10}
        assert get_game_piece_count(_pts(bd, year=2023)) == 14

    def test_2024_notes(self):
        bd = {
            "autoAmpNoteCount": 1,
            "autoSpeakerNoteCount": 2,
            "teleopAmpNoteCount": 3,
            "teleopSpeakerNoteCount": 4,
            "teleopSpeakerNoteAmplifiedCount": 5,
        }
        assert get_game_piece_count(_pts(bd, year=2024)) == 15

    def test_2025_coral(self):
        bd = {"autoCoralCount": 8, "teleopCoralCount": 30}
        assert get_game_piece_count(_pts(bd, year=2025)) == 38

    def test_2026_fuel(self):
        bd = {"hubScore": {"totalCount": 42}}
        assert get_game_piece_count(_pts(bd, year=2026)) == 42

    def test_2026_missing_hub_score(self):
        assert get_game_piece_count(_pts({"totalPoints": 10}, year=2026)) is None
