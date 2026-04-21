from __future__ import annotations

from typing import Callable, Dict, List, Optional, Set, Tuple

from backend.common.consts.alliance_color import AllianceColor
from backend.common.models.event_insights import EventInsights
from backend.common.models.match import Match
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo

# (red_val, blue_val) tiebreaker pair; None means the required field was absent.
TCriteria = Optional[Tuple[int, int]]

# Computes a numeric value from a match + alliance for use in OPR calculations.
StatAccessor = Callable[[Match, AllianceColor], float]


class SeasonGameConfig:
    """
    Per-season game configuration.

    All methods have default (no-op) implementations so that pre-2016 seasons
    and unknown years can participate without overriding everything.  Season
    subclasses override only the methods that differ for their game.

    Register every concrete season in game_specific/registry.py.
    """

    # ── Tiebreakers ────────────────────────────────────────────────────────────

    def tiebreak_criteria(self, red: Dict, blue: Dict) -> List[TCriteria]:
        """
        Returns an ordered list of (red_val, blue_val) tiebreaker pairs for
        elimination matches.  None in the list means required data was absent
        in the score breakdown.  Higher value wins each criterion.
        """
        return []

    def finals_can_be_tiebroken(self) -> bool:
        """
        Returns True for years where overtime applies to finals matches (e.g. 2016).
        For most years, finals matches 1-3 cannot be tiebroken — only overtime.
        """
        return False

    # ── Event Insights ─────────────────────────────────────────────────────────

    def calculate_event_insights(self, matches: List[Match]) -> Optional[EventInsights]:
        """Returns computed insights for the event, or None if not supported."""
        return None

    # ── Component OPRs ─────────────────────────────────────────────────────────

    def get_manual_coprs(self) -> Dict[str, StatAccessor]:
        """
        Returns a mapping of component-OPR label → accessor for computed stats
        that cannot be directly read as a single field from the score breakdown
        (e.g. sums of multiple fields, or derived values).
        """
        return {}

    # ── Match Predictions ──────────────────────────────────────────────────────

    def get_prediction_relevant_stats(self) -> List[Tuple[str, int, int]]:
        """
        Returns a list of (stat_name, prior_mean, prior_variance) tuples that
        drive the Bayesian match prediction model for this game.
        """
        return []

    def prediction_brier_fields(self) -> List[Tuple[str, str, str]]:
        """
        Returns tuples of
        (score_breakdown_actual_key, prediction_prob_key, brier_stat_name)
        used to compute extra Brier components for the game.
        """
        return []

    def ranking_bonus_rp_breakdown_fields(self) -> List[str]:
        """
        Returns score-breakdown keys that indicate bonus ranking points
        earned by an alliance in a played quals match.
        """
        return []

    def ranking_bonus_rp_prediction_fields(self) -> List[str]:
        """
        Returns prediction keys (probabilities) used to sample bonus ranking
        points for unplayed quals matches.
        """
        return []

    def ranking_tiebreaker_breakdown_field(self) -> Optional[str]:
        """
        Returns score-breakdown key used as the ranking tiebreaker contribution
        for played quals matches, or None when not defined.
        """
        return None

    def ranking_tiebreaker_prediction_field(self) -> Optional[str]:
        """
        Returns prediction key used as the ranking tiebreaker contribution for
        unplayed quals matches, or None when not defined.
        """
        return None

    def ranking_win_points(self) -> int:
        """
        Returns ranking points awarded to a winning alliance in quals matches.
        """
        return 2

    # ── Score Breakdown Keys ───────────────────────────────────────────────────

    def valid_score_breakdown_keys(self) -> Set[str]:
        """Returns the set of valid score-breakdown field names for this season."""
        return set()

    # ── Rankings ───────────────────────────────────────────────────────────────

    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        """Returns display info for ranking sort columns, or None if unknown."""
        return None

    def record_in_rankings(self) -> bool:
        """
        Returns True if W/L/T record is shown in rankings (the default).
        Override to return False for years that use a different primary metric
        (e.g. 2010, 2015, 2021).
        """
        return True

    def qual_average_in_rankings(self) -> bool:
        """
        Returns True if qual_average replaces W/L/T record as the primary
        ranking metric.  Only True for 2015.
        """
        return False

    # ── Playoff Round Robin ─────────────────────────────────────────────────────

    def round_robin_tiebreak_keys(self) -> List[str]:
        """
        Returns score-breakdown keys used to break round-robin ties.
        Empty list for years/games with no defined tiebreaker fields.
        """
        return []

    def round_robin_tiebreaker_names(self) -> List[str]:
        """
        Returns human-readable names for the round-robin tiebreakers,
        corresponding one-to-one with round_robin_tiebreak_keys().
        """
        return []
