from typing import List, Optional, Set

from backend.common.game_specific.base import BreakdownSeasonGameConfig
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class GameSpecifics2014(BreakdownSeasonGameConfig):
    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        return [
            {"name": "Qual Score", "precision": 0},
            {"name": "Assist", "precision": 0},
            {"name": "Auto", "precision": 0},
            {"name": "Truss & Catch", "precision": 0},
            {"name": "Teleop", "precision": 0},
        ]

    def valid_score_breakdown_keys(self) -> Set[str]:
        return set(["auto", "assist", "truss+catch", "teleop_goal+foul"])
