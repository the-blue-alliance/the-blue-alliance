from __future__ import annotations

from typing import List, Optional

from backend.common.frc_api.types import ScoreDetailModelAlliance2021
from backend.common.game_specific.base import (
    NoRecordModernBreakdownSeasonGameConfig,
    PredictionStatConfig,
    TCriteria,
)
from backend.common.models.event_insights import EventInsights
from backend.common.models.match import Match
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class GameSpecifics2021(
    NoRecordModernBreakdownSeasonGameConfig[ScoreDetailModelAlliance2021]
):
    SCORE_BREAKDOWN_MODEL = ScoreDetailModelAlliance2021

    def tiebreak_criteria(
        self,
        red: ScoreDetailModelAlliance2021,
        blue: ScoreDetailModelAlliance2021,
    ) -> List[TCriteria]:
        return []

    def ranking_tiebreaker_breakdown_field(self) -> Optional[str]:
        return None

    def ranking_tiebreaker_prediction_field(self) -> Optional[str]:
        return None

    def calculate_event_insights(self, matches: List[Match]) -> Optional[EventInsights]:
        # 2021 was a remote practice-only season; no event insights are computed.
        return None

    def get_prediction_relevant_stats(self) -> List[PredictionStatConfig]:
        # 2021 was a remote practice-only season; no match predictions are run.
        return []

    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        return [
            {"name": "Overall Score", "precision": 2},
            {"name": "Galactic Search", "precision": 2},
            {"name": "Auto-Nav", "precision": 2},
            {"name": "Hyperdrive", "precision": 2},
            {"name": "Interstellar Accuracy", "precision": 2},
            {"name": "Power Port", "precision": 2},
        ]

    def round_robin_tiebreak_keys(self) -> List[str]:
        return []

    def round_robin_tiebreaker_names(self) -> List[str]:
        return []
