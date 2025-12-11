from collections.abc import Sequence
from typing import NotRequired, TypedDict

from pyre_extensions import safe_json

from backend.common.datafeed_parsers.exceptions import ParserInputException
from backend.common.helpers.rankings_helper import RankingsHelper
from backend.common.models.event_ranking import EventRanking
from backend.common.models.keys import TeamKey, Year
from backend.common.models.team import Team


class RankingRowInput(TypedDict):
    rank: int
    team_key: TeamKey
    played: int
    dqs: int
    wins: NotRequired[int]
    losses: NotRequired[int]
    ties: NotRequired[int]
    qual_average: NotRequired[float]
    breakdowns: NotRequired[dict[str, float]]


class RankingInput(TypedDict, total=False):
    breakdowns: list[str]
    rankings: list[RankingRowInput]


class JSONRankingsParser:
    @staticmethod
    def parse[T: (str, bytes)](year: Year, rankings_json: T) -> Sequence[EventRanking]:
        """
        Parse JSON that contains a dict of:
        breakdowns: List of ranking breakdowns, such as "Wins", "Qual Avg", "QS", "Auton", "Teleop", etc. Breakdowns will be shown in the order given.
        rankings: List of ranking dicts

        Ranking dict format:
        team_key: String corresponding to a particular team in the format "frcXXX"
        rank: Integer rank of the particular team
        played: Integer of the number of non-surrogate matches played
        dqs: Integer of the number of non-surrogate DQed matches
        breakdown: Dict where the key is a breakdown and the value is its value
        """
        data = safe_json.loads(rankings_json, RankingInput, validate=False)

        if not isinstance(data, dict):
            raise ParserInputException("Data must be a dict.")
        if not isinstance(breakdowns := data.get("breakdowns"), list):
            raise ParserInputException("Data must have a list 'breakdowns'")
        if not isinstance(rankings_data := data.get("rankings"), list):
            raise ParserInputException("Data must have a list 'rankings'")

        # remove wlt from breakdown list so they're not added twice
        for key in ("wins", "losses", "ties"):
            if key in breakdowns:
                breakdowns.remove(key)

        rankings: Sequence[EventRanking] = []
        for ranking in rankings_data:
            if not isinstance(ranking, dict):
                raise ParserInputException("Ranking must be a dict.")
            if "team_key" not in ranking or not Team.validate_key_name(
                ranking["team_key"]
            ):
                raise ParserInputException(
                    "Ranking must have a 'team_key' that follows the format 'frcXXX'"
                )
            for attr in ["rank", "played", "dqs"]:
                if not isinstance(ranking.get(attr), int):
                    raise ParserInputException(f"Ranking must have an integer '{attr}'")

            rankings.append(
                RankingsHelper.build_ranking(
                    year,
                    ranking["rank"],
                    ranking["team_key"],
                    ranking.get("wins", 0),
                    ranking.get("losses", 0),
                    ranking.get("ties", 0),
                    ranking.get("qual_average"),
                    ranking["played"],
                    ranking["dqs"],
                    [ranking[b] for b in breakdowns],
                )
            )

        return rankings
