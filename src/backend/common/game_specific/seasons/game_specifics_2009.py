from typing import List, Optional

from backend.common.game_specific.base import HistoricalSeasonGameConfig
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class GameSpecifics2009(HistoricalSeasonGameConfig):
    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        return [
            {"name": "Qual Score", "precision": 0},
            {"name": "Seeding Score", "precision": 2},
            {"name": "Match Points", "precision": 0},
        ]
