from backend.common.helpers.insights_v2.match_alliance_points import (
    get_auto_points,
    get_endgame_points,
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
