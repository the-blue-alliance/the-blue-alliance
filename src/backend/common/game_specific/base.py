from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Set, Tuple

from backend.common.consts.alliance_color import AllianceColor
from backend.common.models.event_insights import EventInsights
from backend.common.models.match import Match
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo

# (red_val, blue_val) tiebreaker pair; None means the required field was absent.
TCriteria = Optional[Tuple[int, int]]

# Computes a numeric value from a match + alliance for use in OPR calculations.
StatAccessor = Callable[[Match, AllianceColor], float]


class SeasonGameConfig(ABC):
    """
    Per-season game configuration.

    This abstract root declares all per-season extension points.
    Concrete season classes should inherit from one or more intermediate
    base classes/mixins in this module (historical vs breakdown games,
    with/without bonus RPs, ranking record/qual-average variants, etc.)
    and override only behavior specific to their game/year.

    Register every concrete season in game_specific/registry.py.
    """

    # ── Tiebreakers ────────────────────────────────────────────────────────────

    @abstractmethod
    def tiebreak_criteria(self, red: Dict, blue: Dict) -> List[TCriteria]:
        """
        Returns an ordered list of (red_val, blue_val) tiebreaker pairs for
        elimination matches.  None in the list means required data was absent
        in the score breakdown.  Higher value wins each criterion.
        """
        raise NotImplementedError()

    @abstractmethod
    def finals_can_be_tiebroken(self) -> bool:
        """
        Returns True for years where overtime applies to finals matches (e.g. 2016).
        For most years, finals matches 1-3 cannot be tiebroken — only overtime.
        """
        raise NotImplementedError()

    # ── Event Insights ─────────────────────────────────────────────────────────

    @abstractmethod
    def calculate_event_insights(self, matches: List[Match]) -> Optional[EventInsights]:
        """Returns computed insights for the event, or None if not supported."""
        raise NotImplementedError()

    # ── Component OPRs ─────────────────────────────────────────────────────────

    @abstractmethod
    def get_manual_coprs(self) -> Dict[str, StatAccessor]:
        """
        Returns a mapping of component-OPR label → accessor for computed stats
        that cannot be directly read as a single field from the score breakdown
        (e.g. sums of multiple fields, or derived values).
        """
        raise NotImplementedError()

    # ── Match Predictions ──────────────────────────────────────────────────────

    @abstractmethod
    def get_prediction_relevant_stats(self) -> List[Tuple[str, int, int]]:
        """
        Returns a list of (stat_name, prior_mean, prior_variance) tuples that
        drive the Bayesian match prediction model for this game.
        """
        raise NotImplementedError()

    @abstractmethod
    def prediction_brier_fields(self) -> List[Tuple[str, str, str]]:
        """
        Returns tuples of
        (score_breakdown_actual_key, prediction_prob_key, brier_stat_name)
        used to compute extra Brier components for the game.
        """
        raise NotImplementedError()

    @abstractmethod
    def ranking_bonus_rp_breakdown_fields(self) -> List[str]:
        """
        Returns score-breakdown keys that indicate bonus ranking points
        earned by an alliance in a played quals match.
        """
        raise NotImplementedError()

    @abstractmethod
    def ranking_bonus_rp_prediction_fields(self) -> List[str]:
        """
        Returns prediction keys (probabilities) used to sample bonus ranking
        points for unplayed quals matches.
        """
        raise NotImplementedError()

    @abstractmethod
    def ranking_tiebreaker_breakdown_field(self) -> Optional[str]:
        """
        Returns score-breakdown key used as the ranking tiebreaker contribution
        for played quals matches, or None when not defined.
        """
        raise NotImplementedError()

    @abstractmethod
    def ranking_tiebreaker_prediction_field(self) -> Optional[str]:
        """
        Returns prediction key used as the ranking tiebreaker contribution for
        unplayed quals matches, or None when not defined.
        """
        raise NotImplementedError()

    @abstractmethod
    def ranking_win_points(self) -> int:
        """
        Returns ranking points awarded to a winning alliance in quals matches.
        """
        raise NotImplementedError()

    # ── Score Breakdown Keys ───────────────────────────────────────────────────

    @abstractmethod
    def valid_score_breakdown_keys(self) -> Set[str]:
        """Returns the set of valid score-breakdown field names for this season."""
        raise NotImplementedError()

    # ── Rankings ───────────────────────────────────────────────────────────────

    @abstractmethod
    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        """Returns display info for ranking sort columns, or None if unknown."""
        raise NotImplementedError()

    @abstractmethod
    def record_in_rankings(self) -> bool:
        """
        Returns True if W/L/T record is shown in rankings (the default).
        Override to return False for years that use a different primary metric
        (e.g. 2010, 2015, 2021).
        """
        raise NotImplementedError()

    @abstractmethod
    def qual_average_in_rankings(self) -> bool:
        """
        Returns True if qual_average replaces W/L/T record as the primary
        ranking metric.  Only True for 2015.
        """
        raise NotImplementedError()

    # ── Playoff Round Robin ─────────────────────────────────────────────────────

    @abstractmethod
    def round_robin_tiebreak_keys(self) -> List[str]:
        """
        Returns score-breakdown keys used to break round-robin ties.
        Empty list for years/games with no defined tiebreaker fields.
        """
        raise NotImplementedError()

    @abstractmethod
    def round_robin_tiebreaker_names(self) -> List[str]:
        """
        Returns human-readable names for the round-robin tiebreakers,
        corresponding one-to-one with round_robin_tiebreak_keys().
        """
        raise NotImplementedError()


class DefaultSeasonGameConfig(SeasonGameConfig):
    """Concrete baseline with no-op/default behaviors for unimplemented hooks."""

    def tiebreak_criteria(self, red: Dict, blue: Dict) -> List[TCriteria]:
        return []

    def finals_can_be_tiebroken(self) -> bool:
        return False

    def calculate_event_insights(self, matches: List[Match]) -> Optional[EventInsights]:
        return None

    def get_manual_coprs(self) -> Dict[str, StatAccessor]:
        return {}

    def get_prediction_relevant_stats(self) -> List[Tuple[str, int, int]]:
        return []

    def prediction_brier_fields(self) -> List[Tuple[str, str, str]]:
        return []

    def ranking_bonus_rp_breakdown_fields(self) -> List[str]:
        return []

    def ranking_bonus_rp_prediction_fields(self) -> List[str]:
        return []

    def ranking_tiebreaker_breakdown_field(self) -> Optional[str]:
        return None

    def ranking_tiebreaker_prediction_field(self) -> Optional[str]:
        return None

    def ranking_win_points(self) -> int:
        return 2

    def valid_score_breakdown_keys(self) -> Set[str]:
        return set()

    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        return None

    def record_in_rankings(self) -> bool:
        return True

    def qual_average_in_rankings(self) -> bool:
        return False

    def round_robin_tiebreak_keys(self) -> List[str]:
        return []

    def round_robin_tiebreaker_names(self) -> List[str]:
        return []


class RecordInRankingsMixin:
    def record_in_rankings(self) -> bool:
        return True


class NoRecordInRankingsMixin:
    def record_in_rankings(self) -> bool:
        return False


class QualAverageInRankingsMixin:
    def qual_average_in_rankings(self) -> bool:
        return True


class NoQualAverageInRankingsMixin:
    def qual_average_in_rankings(self) -> bool:
        return False


class NoBonusRankingPointsMixin:
    def ranking_bonus_rp_breakdown_fields(self) -> List[str]:
        return []

    def ranking_bonus_rp_prediction_fields(self) -> List[str]:
        return []


class FixedBonusRankingPointsMixin:
    BONUS_RP_BREAKDOWN_FIELDS: Tuple[str, ...] = ()
    BONUS_RP_PREDICTION_FIELDS: Tuple[str, ...] = ()

    def ranking_bonus_rp_breakdown_fields(self) -> List[str]:
        return list(self.BONUS_RP_BREAKDOWN_FIELDS)

    def ranking_bonus_rp_prediction_fields(self) -> List[str]:
        return list(self.BONUS_RP_PREDICTION_FIELDS)


class NoRpSeasonGameConfig(NoBonusRankingPointsMixin, DefaultSeasonGameConfig):
    """Intermediate base for seasons with no bonus ranking points."""

    pass


class BonusRpSeasonGameConfig(FixedBonusRankingPointsMixin, DefaultSeasonGameConfig):
    """Intermediate base for seasons that define bonus ranking points."""

    pass


class NoRecordSeasonGameConfig(NoRecordInRankingsMixin, DefaultSeasonGameConfig):
    """Intermediate base for seasons where W/L/T record is not shown."""

    pass


class QualAverageNoRecordSeasonGameConfig(
    QualAverageInRankingsMixin, NoRecordSeasonGameConfig
):
    """Intermediate base for seasons ranked by qual average instead of W/L/T."""

    pass


class HistoricalSeasonGameConfig(NoRpSeasonGameConfig):
    """Intermediate base for historical games with minimal game-specific hooks."""

    pass


class BreakdownSeasonGameConfig(NoRpSeasonGameConfig):
    """Intermediate base for games that expose FMS score breakdown data."""

    pass


class TotalPointsScoreTiebreakGameConfig(BreakdownSeasonGameConfig):
    """
    Shared base for games whose ranking prediction tiebreaker uses
    score breakdown `totalPoints` and predicted `score`.
    """

    def ranking_tiebreaker_breakdown_field(self) -> Optional[str]:
        return "totalPoints"

    def ranking_tiebreaker_prediction_field(self) -> Optional[str]:
        return "score"


class TripleWinPointsGameConfig(TotalPointsScoreTiebreakGameConfig):
    """Shared base for seasons awarding 3 ranking points for a win."""

    def ranking_win_points(self) -> int:
        return 3


class BonusRpBreakdownSeasonGameConfig(
    FixedBonusRankingPointsMixin, BreakdownSeasonGameConfig
):
    """Breakdown game base with configurable bonus RP field mappings."""

    pass


class TotalPointsScoreBonusRpGameConfig(
    FixedBonusRankingPointsMixin, TotalPointsScoreTiebreakGameConfig
):
    """TotalPoints/score tiebreaker base with configurable bonus RP mappings."""

    pass


class TripleWinTotalPointsScoreBonusRpGameConfig(
    FixedBonusRankingPointsMixin, TripleWinPointsGameConfig
):
    """3-win-point + totalPoints/score tiebreaker base with bonus RP mappings."""

    pass
