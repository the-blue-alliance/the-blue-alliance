import json
from collections import defaultdict
from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import Any

from backend.common.consts.event_type import SEASON_EVENT_TYPES
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.award import Award
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


CounterDictType = defaultdict[Any, int] | defaultdict[Any, float] | dict[Any, int]


@dataclass
class LeaderboardInsightArguments:
    events: list[Event]
    year: int

    def matches(self) -> Generator[Match, None, None]:
        """
        It's not feasible to store every match in memory, so create a reusable generator
        that yields one match at a time given a list of events.
        """
        for event in self.events:
            for match in event.matches:
                yield match

    def awards(self) -> Generator[Award, None, None]:
        """
        It's not feasible to store every award in memory, so create a reusable generator
        that yields one award at a time given a list of events.
        """
        for event in self.events:
            for award in event.awards:
                yield award


def make_leaderboard_args(year: Year) -> LeaderboardInsightArguments:
    all_events: list[Event] = []

    if year == 0:
        for yr in SeasonHelper.get_valid_years():
            all_events.extend(EventListQuery(year=yr).fetch())
    else:
        all_events.extend(EventListQuery(year=year).fetch())

    all_events = [e for e in all_events if e.event_type_enum in SEASON_EVENT_TYPES]
    return LeaderboardInsightArguments(
        events=all_events,
        year=year,
    )


def make_insights_from_functions(
    year: Year, fns: list[Callable[[LeaderboardInsightArguments], Insight | None]]
) -> list[Insight]:
    args = make_leaderboard_args(year=year)

    insights: list[Insight] = []
    for fn in fns:
        if maybe_insight := fn(args):
            insights.append(maybe_insight)

    return insights


def sort_counter_dict(
    count: CounterDictType, key_type: LeaderboardKeyType = "team"
) -> list[tuple[int | float, list[str]]]:
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


def create_insight(
    data: Any, name: str, year: int, district_abbreviation: str | None = None
) -> Insight:
    """
    Create Insight object given data, name, and year
    """
    return Insight(
        id=Insight.render_key_name(year, name, district_abbreviation),
        name=name,
        year=year,
        data_json=json.dumps(data),
        district_abbreviation=district_abbreviation,
    )


def make_leaderboard_from_dict_counts(
    counter: CounterDictType,
    insight_type: int,
    year: int,
) -> Insight:
    sorted_leaderboard_tuples = sort_counter_dict(
        counter, key_type=Insight.TYPED_LEADERBOARD_KEY_TYPES[insight_type]
    )
    leaderboard_rankings: list[LeaderboardRanking] = [
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
