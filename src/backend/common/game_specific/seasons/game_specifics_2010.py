from typing import List, Optional

from backend.common.game_specific.base import SeasonGameConfig
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class GameSpecifics2010(SeasonGameConfig):
    def record_in_rankings(self) -> bool:
        return False

    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        return [
            {"name": "Seeding Score", "precision": 0},
            {"name": "Coopertition Bonus", "precision": 0},
            {"name": "Hanging Points", "precision": 0},
        ]
