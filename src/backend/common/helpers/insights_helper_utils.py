import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, DefaultDict, Dict, List, Optional, Tuple

from backend.common.consts.event_type import SEASON_EVENT_TYPES
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.event import Event
from backend.common.models.insight import (
    Insight,
    LeaderboardData,
    LeaderboardKeyType,
    LeaderboardRanking,
)
from backend.common.models.keys import Year
from backend.common.models.match import Match
from backend.common.queries.event_query import EventListQuery


CounterDictType = DefaultDict[Any, int] | DefaultDict[Any, float] | Dict[Any, int]


@dataclass
class LeaderboardInsightArguments:
    matches: List[Match]
    year: int


def make_leaderboard_args() -> List[LeaderboardInsightArguments]:
    all_events: List[Event] = []

    event_futures = []
    for year in SeasonHelper.get_valid_years():
        event_futures.append(EventListQuery(year=year).fetch_async())

    for future in event_futures:
        all_events.extend(future.get_result())

    all_events = [e for e in all_events if e.event_type_enum in SEASON_EVENT_TYPES]

    args_list: List[LeaderboardInsightArguments] = []
    all_matches: List[Match] = []

    # Build per-year args
    for year in SeasonHelper.get_valid_years():
        year_events = [e for e in all_events if e.year == year]
        year_matches = [m for e in year_events for m in e.matches]
        all_matches.extend(year_matches)
        args_list.append(LeaderboardInsightArguments(matches=year_matches, year=year))

    # Build overall args
    args_list.append(LeaderboardInsightArguments(matches=all_matches, year=0))

    # todo(tervay): add more args groups, e.g. by district

    return args_list


def make_insights_from_functions(
    year: Year, fns: List[Callable[[LeaderboardInsightArguments], Optional[Insight]]]
) -> List[Insight]:
    args_list = make_leaderboard_args()

    insights: List[Insight] = []
    for args in args_list:
        # Only compute overall and the given year
        if args.year not in [0, year]:
            continue

        for fn in fns:
            if maybe_insight := fn(args):
                insights.append(maybe_insight)

    return insights


def sort_counter_dict(
    count: CounterDictType, key_type: LeaderboardKeyType = "team"
) -> List[Tuple[int | float, List[str]]]:
    """
    Takes an object that looks like: {"frc1": 5, "frc2": 5, "frc3": 3}
    (may be match, event, or team keys) and returns a list of tuples that
    are (magnitude, list of keys) grouped by magnitude, and then sorted by
    magnitude, e.g. [(5, ["frc1", "frc2"]), (2, ["frc3"])].
    """

    # sort by:
    #   team: team number
    #   event & match: alphabetically by key
    tuples = []
    if key_type == "team":
        tuples = sorted(count.items(), key=lambda pair: int(pair[0][3:]))
    else:
        tuples = sorted(count.items(), key=lambda pair: pair[4:])

    # group by magnitude
    temp = defaultdict(list)
    for team, num in tuples:
        temp[num].append(team)

    # sort by magnitude
    return sorted(temp.items(), key=lambda pair: float(pair[0]), reverse=True)


def create_insight(data: Any, name: str, year: int) -> Insight:
    """
    Create Insight object given data, name, and year
    """
    return Insight(
        id=Insight.render_key_name(year, name),
        name=name,
        year=year,
        data_json=json.dumps(data),
    )


def make_leaderboard_from_dict_counts(
    counter: CounterDictType,
    insight_type: int,
    year: int,
) -> Insight:
    sorted_leaderboard_tuples = sort_counter_dict(
        counter, key_type=Insight.TYPED_LEADERBOARD_KEY_TYPES[insight_type]
    )
    leaderboard_rankings: List[LeaderboardRanking] = [
        LeaderboardRanking(keys=keys, value=value)
        # Only take top 25 sorted results
        for (value, keys) in sorted_leaderboard_tuples[:25]
    ]
    leaderboard_data = LeaderboardData(
        rankings=leaderboard_rankings,
        key_type=Insight.TYPED_LEADERBOARD_KEY_TYPES[insight_type],
    )

    return create_insight(
        data=leaderboard_data,
        name=Insight.INSIGHT_NAMES[insight_type],
        year=year,
    )
