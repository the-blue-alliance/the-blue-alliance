from typing import List, Optional, Set

from backend.common.game_specific.base import QualAverageNoRecordSeasonGameConfig
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class GameSpecifics2015(QualAverageNoRecordSeasonGameConfig):

    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        return [
            {"name": "Qual Avg.", "precision": 1},
            {"name": "Coopertition", "precision": 0},
            {"name": "Auto", "precision": 0},
            {"name": "Container", "precision": 0},
            {"name": "Tote", "precision": 0},
            {"name": "Litter", "precision": 0},
        ]

    def valid_score_breakdown_keys(self) -> Set[str]:
        return set(
            [
                "coopertition_points",
                "auto_points",
                "container_points",
                "tote_points",
                "litter_points",
                "foul_points",
            ]
        )
