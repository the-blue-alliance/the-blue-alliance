import json
from typing import Dict, Literal, Set

from google.appengine.ext import ndb

from backend.common.models.cached_model import CachedModel


LeaderboardKeyType = Literal["team"] | Literal["event"] | Literal["match"]


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
        YEAR_SPECIFIC_BY_WEEK: "year_specific_by_week",
        YEAR_SPECIFIC: "year_specific",
    }

    TYPED_LEADERBOARD_MATCH_INSIGHTS = {
        TYPED_LEADERBOARD_MOST_MATCHES_PLAYED,
        TYPED_LEADERBOARD_HIGHEST_MEDIAN_SCORE_BY_EVENT,
    }
    TYPED_LEADERBOARD_AWARD_INSIGHTS = {
        TYPED_LEADERBOARD_BLUE_BANNERS,
    }

    TYPED_LEADERBOARD_KEY_TYPES: Dict[int, LeaderboardKeyType] = {
        TYPED_LEADERBOARD_BLUE_BANNERS: "team",
        TYPED_LEADERBOARD_MOST_MATCHES_PLAYED: "team",
        TYPED_LEADERBOARD_HIGHEST_MEDIAN_SCORE_BY_EVENT: "event",
    }

    name = ndb.StringProperty(required=True)  # general name used for sorting
    year = ndb.IntegerProperty(
        required=True
    )  # year this insight pertains to. year = 0 for overall insights
    data_json = ndb.TextProperty(
        required=True, indexed=False
    )  # JSON dictionary of the data of the insight

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    _json_attrs: Set[str] = {
        "data_json",
    }

    def __init__(self, *args, **kw):
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
        return self.render_key_name(self.year, self.name)

    @classmethod
    def render_key_name(cls, year, name):
        if year == 0:
            return "insights" + "_" + str(name)
        else:
            return str(year) + "insights" + "_" + str(name)
