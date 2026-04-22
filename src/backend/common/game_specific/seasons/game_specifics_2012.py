from typing import List, Optional

from backend.common.game_specific.base import HistoricalSeasonGameConfig
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class GameSpecifics2012(HistoricalSeasonGameConfig):
    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        return [
            {"name": "Qual Score", "precision": 0},
            {"name": "Hybrid", "precision": 0},
            {"name": "Bridge", "precision": 0},
            {"name": "Teleop", "precision": 0},
        ]
