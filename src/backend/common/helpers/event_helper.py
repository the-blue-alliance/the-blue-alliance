from typing import cast, List, NamedTuple, Optional

from backend.common.consts import comp_level
from backend.common.consts.alliance_color import AllianceColor
from backend.common.models.event_team_status import WLTRecord
from backend.common.models.keys import EventKey, TeamKey
from backend.common.models.match import Match


class TeamAvgScore(NamedTuple):
    qual_avg: Optional[float]
    elim_avg: Optional[float]
    all_qual_scores: List[int]
    all_elim_scores: List[int]


class EventHelper(object):
    @staticmethod
    def is_2015_playoff(event_key: EventKey) -> bool:
        year = event_key[:4]
        event_short = event_key[4:]
        return year == "2015" and event_short not in {"cc", "cacc", "mttd"}

    @staticmethod
    def calculateTeamAvgScoreFromMatches(
        team_key: TeamKey, matches: List[Match]
    ) -> TeamAvgScore:
        """
        Given a team_key and some matches, find the team's average qual and elim score
        """
        all_qual_scores: List[int] = []
        all_elim_scores: List[int] = []
        for match in matches:
            if match.has_been_played:
                for alliance in match.alliances.values():
                    if team_key in alliance["teams"]:
                        if match.comp_level in comp_level.ELIM_LEVELS:
                            all_elim_scores.append(alliance["score"])
                        else:
                            all_qual_scores.append(alliance["score"])
                        break
        qual_avg = (
            float(sum(all_qual_scores)) / len(all_qual_scores)
            if all_qual_scores != []
            else None
        )
        elim_avg = (
            float(sum(all_elim_scores)) / len(all_elim_scores)
            if all_elim_scores != []
            else None
        )
        return TeamAvgScore(
            qual_avg=qual_avg,
            elim_avg=elim_avg,
            all_qual_scores=all_qual_scores,
            all_elim_scores=all_elim_scores,
        )

    @staticmethod
    def calculateTeamWLTFromMatches(
        team_key: TeamKey, matches: List[Match]
    ) -> WLTRecord:
        """
        Given a team_key and some matches, find the Win Loss Tie.
        """
        wlt: WLTRecord = {"wins": 0, "losses": 0, "ties": 0}

        for match in matches:
            if match.has_been_played and match.winning_alliance is not None:
                if match.winning_alliance == "":
                    wlt["ties"] += 1
                elif (
                    team_key
                    in match.alliances[cast(AllianceColor, match.winning_alliance)][
                        "teams"
                    ]
                ):
                    wlt["wins"] += 1
                else:
                    wlt["losses"] += 1
        return wlt
