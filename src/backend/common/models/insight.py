import json
from typing import Dict, List, Literal, Optional, Set, TypeAlias, TypedDict

from google.appengine.ext import ndb

from backend.common.models.cached_model import CachedModel
from backend.common.models.keys import (
    DistrictAbbreviation,
    EventKey,
    MatchKey,
    TeamKey,
    Year,
)
from backend.common.models.wlt import WLTRecord


LeaderboardKeyType = Literal["team"] | Literal["event"] | Literal["match"]
InsightEnumId: TypeAlias = int


class Insight(CachedModel):
    """
    Insights are the end result of analyzing a batch of data, such as the
    average score for all matches in a year.
    key_name is like '2012insights_matchavg'
    """

    MATCH_HIGHSCORE = 0
    MATCH_HIGHSCORE_BY_WEEK = 1
    MATCH_AVERAGES_BY_WEEK = 2
    ELIM_MATCH_AVERAGES_BY_WEEK = 3
    SCORE_DISTRIBUTION = 4
    ELIM_SCORE_DISTRIBUTION = 5
    NUM_MATCHES = 6
    BLUE_BANNERS = 7
    CA_WINNER = 8
    RCA_WINNERS = 9
    WORLD_CHAMPIONS = 10
    WORLD_FINALISTS = 11
    DIVISION_WINNERS = 12
    DIVISION_FINALISTS = 13
    REGIONAL_DISTRICT_WINNERS = 14
    SUCCESSFUL_ELIM_TEAMUPS = 15
    MATCH_PREDICTIONS = 16
    MATCH_AVERAGE_MARGINS_BY_WEEK = 17
    ELIM_MATCH_AVERAGE_MARGINS_BY_WEEK = 18
    WINNING_MARGIN_DISTRIBUTION = 19
    ELIM_WINNING_MARGIN_DISTRIBUTION = 20
    EINSTEIN_STREAK = 21
    MATCHES_PLAYED = 22
    TYPED_LEADERBOARD_BLUE_BANNERS = 23
    TYPED_LEADERBOARD_MOST_MATCHES_PLAYED = 24
    TYPED_LEADERBOARD_HIGHEST_MEDIAN_SCORE_BY_EVENT = 25
    TYPED_LEADERBOARD_HIGHEST_MATCH_CLEAN_SCORE = 26
    TYPED_LEADERBOARD_HIGHEST_MATCH_CLEAN_COMBINED_SCORE = 27
    TYPED_LEADERBOARD_MOST_AWARDS = 28
    TYPED_LEADERBOARD_MOST_NON_CHAMPS_EVENT_WINS = 29
    TYPED_LEADERBOARD_MOST_UNIQUE_TEAMS_PLAYED_WITH_AGAINST = 30
    TYPED_NOTABLES_DIVISION_WINNERS = 31
    TYPED_NOTABLES_DIVISION_FINALS_APPEARANCES = 32
    TYPED_NOTABLES_WORLD_CHAMPIONS = 33
    TYPED_NOTABLES_HALL_OF_FAME = 34
    TYPED_LEADERBOARD_MOST_EVENTS_PLAYED_AT = 35
    TYPED_LEADERBOARD_2025_MOST_CORAL_SCORED = 36
    TYPED_LEADERBOARD_LONGEST_EINSTEIN_STREAK = 37
    TYPED_NOTABLES_DCMP_WINNER = 38
    TYPED_NOTABLES_CMP_FINALS_APPEARANCES = 39
    TYPED_LEADERBOARD_MOST_NON_CHAMPS_IMPACT_WINS = 40
    TYPED_LEADERBOARD_MOST_WFFAS = 41
    SUCCESSFUL_EINSTEIN_TEAMUPS = 42
    TYPED_LEADERBOARD_LONGEST_QUALIFYING_EVENT_STREAK = 43
    DISTRICT_INSIGHTS_TEAM_DATA = 44
    DISTRICT_INSIGHT_DISTRICT_DATA = 45
    YEAR_SPECIFIC_BY_WEEK = 999
    YEAR_SPECIFIC = 1000

    # Used for datastore keys! Don't change unless you know what you're doing.
    INSIGHT_NAMES = {
        MATCH_HIGHSCORE: "match_highscore",
        MATCH_HIGHSCORE_BY_WEEK: "match_highscore_by_week",
        MATCH_AVERAGES_BY_WEEK: "match_averages_by_week",
        ELIM_MATCH_AVERAGES_BY_WEEK: "elim_match_averages_by_week",
        SCORE_DISTRIBUTION: "score_distribution",
        ELIM_SCORE_DISTRIBUTION: "elim_score_distribution",
        NUM_MATCHES: "num_matches",
        BLUE_BANNERS: "blue_banners",
        CA_WINNER: "ca_winner",
        RCA_WINNERS: "rca_winners",
        WORLD_CHAMPIONS: "world_champions",
        WORLD_FINALISTS: "world_finalists",
        DIVISION_WINNERS: "division_winners",
        DIVISION_FINALISTS: "division_finalists",
        REGIONAL_DISTRICT_WINNERS: "regional_district_winners",
        SUCCESSFUL_ELIM_TEAMUPS: "successful_elim_teamups",
        SUCCESSFUL_EINSTEIN_TEAMUPS: "successful_einstein_teamups",
        MATCH_PREDICTIONS: "match_predictions",
        MATCH_AVERAGE_MARGINS_BY_WEEK: "match_average_margins_by_week",
        ELIM_MATCH_AVERAGE_MARGINS_BY_WEEK: "elim_match_average_margins_by_week",
        WINNING_MARGIN_DISTRIBUTION: "winning_margin_distribution",
        ELIM_WINNING_MARGIN_DISTRIBUTION: "elim_winning_margin_distribution",
        EINSTEIN_STREAK: "einstein_streak",
        MATCHES_PLAYED: "matches_played",
        TYPED_LEADERBOARD_BLUE_BANNERS: "typed_leaderboard_blue_banners",
        TYPED_LEADERBOARD_MOST_MATCHES_PLAYED: "typed_leaderboard_most_matches_played",
        TYPED_LEADERBOARD_HIGHEST_MEDIAN_SCORE_BY_EVENT: "typed_leaderboard_highest_median_score_by_event",
        TYPED_LEADERBOARD_HIGHEST_MATCH_CLEAN_SCORE: "typed_leaderboard_highest_match_clean_score",
        TYPED_LEADERBOARD_HIGHEST_MATCH_CLEAN_COMBINED_SCORE: "typed_leaderboard_highest_match_clean_combined_score",
        TYPED_LEADERBOARD_MOST_AWARDS: "typed_leaderboard_most_awards",
        TYPED_LEADERBOARD_MOST_NON_CHAMPS_EVENT_WINS: "typed_leaderboard_most_non_champs_event_wins",
        TYPED_LEADERBOARD_MOST_UNIQUE_TEAMS_PLAYED_WITH_AGAINST: "typed_leaderboard_most_unique_teams_played_with_against",
        TYPED_LEADERBOARD_MOST_EVENTS_PLAYED_AT: "typed_leaderboard_most_events_played_at",
        TYPED_NOTABLES_DIVISION_WINNERS: "notables_division_winners",
        TYPED_NOTABLES_DIVISION_FINALS_APPEARANCES: "notables_division_finals_appearances",
        TYPED_NOTABLES_WORLD_CHAMPIONS: "notables_world_champions",
        TYPED_NOTABLES_HALL_OF_FAME: "notables_hall_of_fame",
        YEAR_SPECIFIC_BY_WEEK: "year_specific_by_week",
        YEAR_SPECIFIC: "year_specific",
        TYPED_LEADERBOARD_2025_MOST_CORAL_SCORED: "typed_leaderboard_2025_most_coral_scored",
        TYPED_LEADERBOARD_LONGEST_EINSTEIN_STREAK: "typed_leaderboard_longest_einstein_streak",
        TYPED_NOTABLES_DCMP_WINNER: "notables_dcmp_winner",
        TYPED_NOTABLES_CMP_FINALS_APPEARANCES: "notables_cmp_finals_appearances",
        TYPED_LEADERBOARD_MOST_NON_CHAMPS_IMPACT_WINS: "typed_leaderboard_most_non_champs_impact_wins",
        TYPED_LEADERBOARD_MOST_WFFAS: "typed_leaderboard_most_wffas",
        TYPED_LEADERBOARD_LONGEST_QUALIFYING_EVENT_STREAK: "typed_leaderboard_longest_qualifying_event_streak",
        DISTRICT_INSIGHTS_TEAM_DATA: "district_insights_team_data",
        DISTRICT_INSIGHT_DISTRICT_DATA: "district_insights_district_data",
    }

    TYPED_LEADERBOARD_KEY_TYPES: Dict[int, LeaderboardKeyType] = {
        TYPED_LEADERBOARD_BLUE_BANNERS: "team",
        TYPED_LEADERBOARD_MOST_MATCHES_PLAYED: "team",
        TYPED_LEADERBOARD_HIGHEST_MEDIAN_SCORE_BY_EVENT: "event",
        TYPED_LEADERBOARD_HIGHEST_MATCH_CLEAN_SCORE: "match",
        TYPED_LEADERBOARD_HIGHEST_MATCH_CLEAN_COMBINED_SCORE: "match",
        TYPED_LEADERBOARD_MOST_AWARDS: "team",
        TYPED_LEADERBOARD_MOST_NON_CHAMPS_EVENT_WINS: "team",
        TYPED_LEADERBOARD_MOST_UNIQUE_TEAMS_PLAYED_WITH_AGAINST: "team",
        TYPED_LEADERBOARD_MOST_EVENTS_PLAYED_AT: "team",
        TYPED_LEADERBOARD_2025_MOST_CORAL_SCORED: "match",
        TYPED_LEADERBOARD_LONGEST_EINSTEIN_STREAK: "team",
        TYPED_LEADERBOARD_MOST_NON_CHAMPS_IMPACT_WINS: "team",
        TYPED_LEADERBOARD_MOST_WFFAS: "team",
        TYPED_LEADERBOARD_LONGEST_QUALIFYING_EVENT_STREAK: "team",
    }

    NOTABLE_INSIGHTS = {
        TYPED_NOTABLES_DIVISION_WINNERS,
        TYPED_NOTABLES_DIVISION_FINALS_APPEARANCES,
        TYPED_NOTABLES_WORLD_CHAMPIONS,
        TYPED_NOTABLES_HALL_OF_FAME,
        TYPED_NOTABLES_DCMP_WINNER,
        TYPED_NOTABLES_CMP_FINALS_APPEARANCES,
    }

    name = ndb.StringProperty(required=True)  # general name used for sorting
    year = ndb.IntegerProperty(
        required=True
    )  # year this insight pertains to. year = 0 for overall insights
    data_json = ndb.TextProperty(
        required=True, indexed=False
    )  # JSON dictionary of the data of the insight

    district_abbreviation = ndb.StringProperty(required=False, indexed=True)

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    _json_attrs: Set[str] = {
        "data_json",
    }

    _mutable_attrs: Set[str] = {
        "district_abbreviation",
    }

    def __init__(self, *args, **kw):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            "year": set(),
        }
        self._data = None
        super(Insight, self).__init__(*args, **kw)

    @property
    def data(self):
        """
        Lazy load data_json as an OrderedDict
        """
        if self._data is None:
            self._data = json.loads(self.data_json)
        return self._data

    @property
    def key_name(self):
        """
        Returns the string of the key_name of the Insight object before writing it.
        """
        return self.render_key_name(self.year, self.name, self.district_abbreviation)

    @classmethod
    def render_key_name(
        cls,
        year: int,
        name: str,
        district_abbreviation: Optional[DistrictAbbreviation] = None,
    ) -> str:
        prefix = f"{year}insights" if year != 0 else "insights"
        suffix = f"_{district_abbreviation}" if district_abbreviation else ""
        return f"{prefix}_{name}{suffix}"


class LeaderboardRanking(TypedDict):
    keys: List[TeamKey | EventKey | MatchKey]
    value: int | float


class LeaderboardData(TypedDict):
    rankings: List[LeaderboardRanking]
    key_type: LeaderboardKeyType


class LeaderboardInsight(TypedDict):
    """This is the type that should be returned over the API!"""

    data: LeaderboardData
    name: str
    year: int


class NotableEntry(TypedDict):
    team_key: TeamKey

    # this needs to be a list to support overall
    # in an individual year, this should probably always be len 1
    context: List[EventKey]


class NotablesData(TypedDict):
    """In case we need more data in the future, we can add it here."""

    entries: List[NotableEntry]


class NotablesInsight(TypedDict):
    """This is the type that should be returned over the API!"""

    data: NotablesData
    name: str
    year: int


class DistrictInsightTeamData(TypedDict):
    district_seasons: int
    total_district_points: int
    total_pre_dcmp_district_points: int
    district_event_wins: int
    dcmp_wins: int
    team_awards: int
    individual_awards: int
    quals_record: WLTRecord
    elims_record: WLTRecord
    blue_banners: int
    in_district_extra_play_count: int
    total_matches_played: int
    dcmp_appearances: int
    cmp_appearances: int


class DistrictInsightDistrictRegionData(TypedDict):
    yearly_active_team_count: Dict[Year, int]
    yearly_gained_teams: Dict[Year, List[TeamKey]]
    yearly_lost_teams: Dict[Year, List[TeamKey]]
    yearly_event_count: Dict[Year, int]


class DistrictInsightDistrictData(TypedDict):
    # Grouped by region (state or country)
    region_data: Dict[str, DistrictInsightDistrictRegionData]
    # Full district-wide data
    district_wide_data: DistrictInsightDistrictRegionData
