from typing import AnyStr, Dict, List, Sequence, TypedDict

from pyre_extensions import safe_json

from backend.common.datafeed_parsers.exceptions import ParserInputException
from backend.common.helpers.rankings_helper import RankingsHelper
from backend.common.models.event_ranking import EventRanking
from backend.common.models.keys import TeamKey, Year
from backend.common.models.team import Team


class RankingRowInput(TypedDict, total=False):
    team_key: TeamKey
    rank: int
    played: int
    dqs: int
    breakdowns: Dict[str, float]


class RankingInput(TypedDict, total=False):
    breakdowns: List[str]
    rankings: List[RankingRowInput]


class JSONRankingsParser:
    @staticmethod
    def parse(year: Year, rankings_json: AnyStr) -> Sequence[EventRanking]:
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
        try:
            data = safe_json.loads(rankings_json, RankingInput, validate=False)
        except Exception:
            raise ParserInputException("Invalid JSON. Please check input.")

        if type(data) is not dict:
            raise ParserInputException("Data must be a dict.")
        if "breakdowns" not in data or type(data["breakdowns"]) is not list:
            raise ParserInputException("Data must have a list 'breakdowns'")
        if "rankings" not in data or type(data["rankings"]) is not list:
            raise ParserInputException("Data must have a list 'rankings'")

        if (
            "wins" in data["breakdowns"]
            and "losses" in data["breakdowns"]
            and "ties" in data["breakdowns"]
        ):
            # remove wlt from breakdown list so they're not added twice
            data["breakdowns"].remove("wins")
            data["breakdowns"].remove("losses")
            data["breakdowns"].remove("ties")

        rankings: Sequence[EventRanking] = []
        for ranking in data["rankings"]:
            if type(ranking) is not dict:
                raise ParserInputException("Ranking must be a dict.")
            if "team_key" not in ranking or not Team.validate_key_name(
                ranking["team_key"]
            ):
                raise ParserInputException(
                    "Ranking must have a 'team_key' that follows the format 'frcXXX'"
                )
            for attr in ["rank", "played", "dqs"]:
                if attr not in ranking or type(ranking[attr]) is not int:
                    raise ParserInputException(
                        "Ranking must have a integer '{}'".format(attr)
                    )

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
                    [ranking[b] for b in data["breakdowns"]],
                )
            )

        return rankings
