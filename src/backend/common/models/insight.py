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
    TYPED_LEADERBOARD_HIGHEST_MATCH_CLEAN_SCORE = 26
    TYPED_LEADERBOARD_HIGHEST_MATCH_CLEAN_COMBINED_SCORE = 27
    TYPED_LEADERBOARD_MOST_AWARDS = 28
    TYPED_LEADERBOARD_MOST_NON_CHAMPS_EVENT_WINS = 29
    TYPED_LEADERBOARD_MOST_UNIQUE_TEAMS_PLAYED_WITH_AGAINST = 30
    TYPED_LEADERBOARD_MOST_DIVISION_WINS = 31
    TYPED_LEADERBOARD_MOST_DIVISION_FINALS_APPEARANCES = 32
    TYPED_LEADERBOARD_MOST_WORLD_CHAMPIONSHIP_WINS = 33
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
        TYPED_LEADERBOARD_HIGHEST_MATCH_CLEAN_SCORE: "typed_leaderboard_highest_match_clean_score",
        TYPED_LEADERBOARD_HIGHEST_MATCH_CLEAN_COMBINED_SCORE: "typed_leaderboard_highest_match_clean_combined_score",
        TYPED_LEADERBOARD_MOST_AWARDS: "typed_leaderboard_most_awards",
        TYPED_LEADERBOARD_MOST_NON_CHAMPS_EVENT_WINS: "typed_leaderboard_most_non_champs_event_wins",
        TYPED_LEADERBOARD_MOST_UNIQUE_TEAMS_PLAYED_WITH_AGAINST: "typed_leaderboard_most_unique_teams_played_with_against",
        TYPED_LEADERBOARD_MOST_DIVISION_WINS: "typed_leaderboard_most_division_wins",
        TYPED_LEADERBOARD_MOST_DIVISION_FINALS_APPEARANCES: "typed_leaderboard_most_division_finals_appearances",
        TYPED_LEADERBOARD_MOST_WORLD_CHAMPIONSHIP_WINS: "typed_leaderboard_most_world_championship_wins",
        YEAR_SPECIFIC_BY_WEEK: "year_specific_by_week",
        YEAR_SPECIFIC: "year_specific",
    }

    TYPED_LEADERBOARD_MATCH_INSIGHTS = {
        TYPED_LEADERBOARD_MOST_MATCHES_PLAYED,
        TYPED_LEADERBOARD_HIGHEST_MEDIAN_SCORE_BY_EVENT,
        TYPED_LEADERBOARD_HIGHEST_MATCH_CLEAN_SCORE,
        TYPED_LEADERBOARD_HIGHEST_MATCH_CLEAN_COMBINED_SCORE,
        TYPED_LEADERBOARD_MOST_UNIQUE_TEAMS_PLAYED_WITH_AGAINST,
    }
    TYPED_LEADERBOARD_AWARD_INSIGHTS = {
        TYPED_LEADERBOARD_BLUE_BANNERS,
        TYPED_LEADERBOARD_MOST_AWARDS,
        TYPED_LEADERBOARD_MOST_NON_CHAMPS_EVENT_WINS,
        TYPED_LEADERBOARD_MOST_DIVISION_WINS,
        TYPED_LEADERBOARD_MOST_DIVISION_FINALS_APPEARANCES,
        TYPED_LEADERBOARD_MOST_WORLD_CHAMPIONSHIP_WINS,
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
        TYPED_LEADERBOARD_MOST_DIVISION_WINS: "team",
        TYPED_LEADERBOARD_MOST_DIVISION_FINALS_APPEARANCES: "team",
        TYPED_LEADERBOARD_MOST_WORLD_CHAMPIONSHIP_WINS: "team",
    }

    # These leaderboards are generated per-year, but are only exposed in the overall insights API endpoint.
    # Stored as insight names so that we can filter out insights on the API level, since insights are saved as names.
    TYPED_LEADERBOARD_OVERALL_ONLY_INSIGHTS = {
        INSIGHT_NAMES[TYPED_LEADERBOARD_MOST_DIVISION_WINS],
        INSIGHT_NAMES[TYPED_LEADERBOARD_MOST_DIVISION_FINALS_APPEARANCES],
        INSIGHT_NAMES[TYPED_LEADERBOARD_MOST_WORLD_CHAMPIONSHIP_WINS],
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
        return self.render_key_name(self.year, self.name)

    @classmethod
    def render_key_name(cls, year, name):
        if year == 0:
            return "insights" + "_" + str(name)
        else:
            return str(year) + "insights" + "_" + str(name)
