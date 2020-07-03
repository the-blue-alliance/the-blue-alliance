from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from pyre_extensions import none_throws

from backend.common.consts.alliance_color import (
    AllianceColor,
    TMatchWinner,
)
from backend.common.consts.comp_level import ELIM_LEVELS
from backend.common.models.match import Match


# Tuples of (red_tiebreaker, blue_tiebreaker) or None. Higher value wins.
TCriteria = Optional[Tuple[int, int]]


class MatchTiebreakers(object):
    @classmethod
    def tiebreak_winner(cls, match: Match) -> TMatchWinner:
        """
        Compute elim winner using tiebreakers
        """
        if match.comp_level not in ELIM_LEVELS or match.score_breakdown is None:
            return ""

        if AllianceColor.RED not in none_throws(
            match.score_breakdown
        ) or AllianceColor.BLUE not in none_throws(match.score_breakdown):
            return ""

        red_breakdown = none_throws(match.score_breakdown)[AllianceColor.RED]
        blue_breakdown = none_throws(match.score_breakdown)[AllianceColor.BLUE]
        tiebreakers: List[TCriteria]

        if match.year == 2016:
            tiebreakers = cls._tiebreak_2016(red_breakdown, blue_breakdown)

        elif match.year == 2017 and not (
            match.comp_level == "f" and match.match_number <= 3
        ):  # Finals can't be tiebroken. Only overtime
            tiebreakers = cls._tiebreak_2017(red_breakdown, blue_breakdown)

        elif match.year == 2019 and not (
            match.comp_level == "f" and match.match_number <= 3
        ):  # Finals can't be tiebroken. Only overtime
            tiebreakers = cls._tiebreak_2019(red_breakdown, blue_breakdown)

        elif match.year == 2020 and not (
            match.comp_level == "f" and match.match_number <= 3
        ):  # Finals can't be tiebroken. Only overtime
            tiebreakers = cls._tiebreak_2020(red_breakdown, blue_breakdown)

        else:
            tiebreakers = []

        for tiebreaker in tiebreakers:
            if tiebreaker is None:
                return ""
            elif tiebreaker[0] > tiebreaker[1]:
                return AllianceColor.RED
            elif tiebreaker[1] > tiebreaker[0]:
                return AllianceColor.BLUE
        return ""

    @classmethod
    def _tiebreak_2020(
        cls, red_breakdown: Dict, blue_breakdown: Dict
    ) -> List[TCriteria]:
        tiebreakers: List[TCriteria] = []

        # Cumulative FOUL and TECH FOUL points due to opponent rule violations
        if "foulPoints" in red_breakdown and "foulPoints" in blue_breakdown:
            tiebreakers.append(
                (red_breakdown["foulPoints"], blue_breakdown["foulPoints"])
            )
        else:
            tiebreakers.append(None)

        # Cumulative AUTO points
        if "autoPoints" in red_breakdown and "autoPoints" in blue_breakdown:
            tiebreakers.append(
                (red_breakdown["autoPoints"], blue_breakdown["autoPoints"])
            )
        else:
            tiebreakers.append(None)

        # Cumulative ENDGAME points
        if "endgamePoints" in red_breakdown and "endgamePoints" in blue_breakdown:
            tiebreakers.append(
                (red_breakdown["endgamePoints"], blue_breakdown["endgamePoints"])
            )
        else:
            tiebreakers.append(None)

        # Cumulative TELEOP POWER CELL and CONTROL PANEL points
        if (
            "teleopCellPoints" in red_breakdown
            and "teleopCellPoints" in blue_breakdown
            and "controlPanelPoints" in red_breakdown
            and "controlPanelPoints" in blue_breakdown
        ):
            tiebreakers.append(
                (
                    red_breakdown["teleopCellPoints"]
                    + red_breakdown["controlPanelPoints"],
                    blue_breakdown["teleopCellPoints"]
                    + blue_breakdown["controlPanelPoints"],
                )
            )
        else:
            tiebreakers.append(None)
        return tiebreakers

    @classmethod
    def _tiebreak_2019(
        cls, red_breakdown: Dict, blue_breakdown: Dict
    ) -> List[TCriteria]:
        tiebreakers: List[TCriteria] = []

        # Greater number of FOUL points awarded (i.e. the ALLIANCE that played the cleaner MATCH)
        if "foulPoints" in red_breakdown and "foulPoints" in blue_breakdown:
            tiebreakers.append(
                (red_breakdown["foulPoints"], blue_breakdown["foulPoints"])
            )
        else:
            tiebreakers.append(None)

        # Cumulative sum of scored CARGO points
        if "cargoPoints" in red_breakdown and "cargoPoints" in blue_breakdown:
            tiebreakers.append(
                (red_breakdown["cargoPoints"], blue_breakdown["cargoPoints"])
            )
        else:
            tiebreakers.append(None)

        # Cumulative sum of scored HATCH PANEL points
        if "hatchPanelPoints" in red_breakdown and "hatchPanelPoints" in blue_breakdown:
            tiebreakers.append(
                (red_breakdown["hatchPanelPoints"], blue_breakdown["hatchPanelPoints"])
            )
        else:
            tiebreakers.append(None)

        # Cumulative sum of scored HAB CLIMB points
        if "habClimbPoints" in red_breakdown and "habClimbPoints" in blue_breakdown:
            tiebreakers.append(
                (red_breakdown["habClimbPoints"], blue_breakdown["habClimbPoints"])
            )
        else:
            tiebreakers.append(None)

        # Cumulative sum of scored SANDSTORM BONUS points
        if (
            "sandStormBonusPoints" in red_breakdown
            and "sandStormBonusPoints" in blue_breakdown
        ):
            tiebreakers.append(
                (
                    red_breakdown["sandStormBonusPoints"],
                    blue_breakdown["sandStormBonusPoints"],
                )
            )
        else:
            tiebreakers.append(None)
        return tiebreakers

    @classmethod
    def _tiebreak_2017(
        cls, red_breakdown: Dict, blue_breakdown: Dict
    ) -> List[TCriteria]:
        tiebreakers: List[TCriteria] = []

        # Greater number of FOUL points awarded (i.e. the ALLIANCE that played the cleaner MATCH)
        if "foulPoints" in red_breakdown and "foulPoints" in blue_breakdown:
            tiebreakers.append(
                (red_breakdown["foulPoints"], blue_breakdown["foulPoints"])
            )
        else:
            tiebreakers.append(None)

        # Cumulative sum of scored AUTO points
        if "autoPoints" in red_breakdown and "autoPoints" in blue_breakdown:
            tiebreakers.append(
                (red_breakdown["autoPoints"], blue_breakdown["autoPoints"])
            )
        else:
            tiebreakers.append(None)

        # Cumulative ROTOR engagement score (AUTO and TELEOP)
        if (
            "autoRotorPoints" in red_breakdown
            and "autoRotorPoints" in blue_breakdown
            and "teleopRotorPoints" in red_breakdown
            and "teleopRotorPoints" in blue_breakdown
        ):
            red_rotor = (
                red_breakdown["autoRotorPoints"] + red_breakdown["teleopRotorPoints"]
            )
            blue_rotor = (
                blue_breakdown["autoRotorPoints"] + blue_breakdown["teleopRotorPoints"]
            )
            tiebreakers.append((red_rotor, blue_rotor))
        else:
            tiebreakers.append(None)

        # Cumulative TOUCHPAD score
        if (
            "teleopTakeoffPoints" in red_breakdown
            and "teleopTakeoffPoints" in blue_breakdown
        ):
            tiebreakers.append(
                (
                    red_breakdown["teleopTakeoffPoints"],
                    blue_breakdown["teleopTakeoffPoints"],
                )
            )
        else:
            tiebreakers.append(None)

        # Total accumulated pressure
        if (
            "autoFuelPoints" in red_breakdown
            and "autoFuelPoints" in blue_breakdown
            and "teleopFuelPoints" in red_breakdown
            and "teleopFuelPoints" in blue_breakdown
        ):
            red_pressure = (
                red_breakdown["autoFuelPoints"] + red_breakdown["teleopFuelPoints"]
            )
            blue_pressure = (
                blue_breakdown["autoFuelPoints"] + blue_breakdown["teleopFuelPoints"]
            )
            tiebreakers.append((red_pressure, blue_pressure))
        else:
            tiebreakers.append(None)
        return tiebreakers

    @classmethod
    def _tiebreak_2016(
        cls, red_breakdown: Dict, blue_breakdown: Dict
    ) -> List[TCriteria]:
        tiebreakers: List[TCriteria] = []

        # Greater number of FOUL points awarded (i.e. the ALLIANCE that played the cleaner MATCH)
        if "foulPoints" in red_breakdown and "foulPoints" in blue_breakdown:
            tiebreakers.append(
                (red_breakdown["foulPoints"], blue_breakdown["foulPoints"])
            )
        else:
            tiebreakers.append(None)

        # Cumulative sum of BREACH and CAPTURE points
        if (
            "breachPoints" in red_breakdown
            and "breachPoints" in blue_breakdown
            and "capturePoints" in red_breakdown
            and "capturePoints" in blue_breakdown
        ):
            red_breach_capture = (
                red_breakdown["breachPoints"] + red_breakdown["capturePoints"]
            )
            blue_breach_capture = (
                blue_breakdown["breachPoints"] + blue_breakdown["capturePoints"]
            )
            tiebreakers.append((red_breach_capture, blue_breach_capture))
        else:
            tiebreakers.append(None)

        # Cumulative sum of scored AUTO points
        if "autoPoints" in red_breakdown and "autoPoints" in blue_breakdown:
            tiebreakers.append(
                (red_breakdown["autoPoints"], blue_breakdown["autoPoints"])
            )
        else:
            tiebreakers.append(None)

        # Cumulative sum of scored SCALE and CHALLENGE points
        if (
            "teleopScalePoints" in red_breakdown
            and "teleopScalePoints" in blue_breakdown
            and "teleopChallengePoints" in red_breakdown
            and "teleopChallengePoints" in blue_breakdown
        ):
            red_scale_challenge = (
                red_breakdown["teleopScalePoints"]
                + red_breakdown["teleopChallengePoints"]
            )
            blue_scale_challenge = (
                blue_breakdown["teleopScalePoints"]
                + blue_breakdown["teleopChallengePoints"]
            )
            tiebreakers.append((red_scale_challenge, blue_scale_challenge))
        else:
            tiebreakers.append(None)

        # Cumulative sum of scored TOWER GOAL points (High and Low goals from AUTO and TELEOP)
        if (
            "autoBoulderPoints" in red_breakdown
            and "autoBoulderPoints" in blue_breakdown
            and "teleopBoulderPoints" in red_breakdown
            and "teleopBoulderPoints" in blue_breakdown
        ):
            red_boulder = (
                red_breakdown["autoBoulderPoints"]
                + red_breakdown["teleopBoulderPoints"]
            )
            blue_boulder = (
                blue_breakdown["autoBoulderPoints"]
                + blue_breakdown["teleopBoulderPoints"]
            )
            tiebreakers.append((red_boulder, blue_boulder))
        else:
            tiebreakers.append(None)

        # Cumulative sum of CROSSED UNDAMAGED DEFENSE points (AUTO and TELEOP)
        if (
            "autoCrossingPoints" in red_breakdown
            and "autoCrossingPoints" in blue_breakdown
            and "teleopCrossingPoints" in red_breakdown
            and "teleopCrossingPoints" in blue_breakdown
        ):
            red_crossing = (
                red_breakdown["autoCrossingPoints"]
                + red_breakdown["teleopCrossingPoints"]
            )
            blue_crossing = (
                blue_breakdown["autoCrossingPoints"]
                + blue_breakdown["teleopCrossingPoints"]
            )
            tiebreakers.append((red_crossing, blue_crossing))
        else:
            tiebreakers.append(None)

        return tiebreakers
