from __future__ import annotations

from typing import List, Optional, Set

from backend.common.game_specific.base import NoRecordSeasonGameConfig
from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo


class GameSpecifics2021(NoRecordSeasonGameConfig):

    def ranking_sort_order_info(self) -> Optional[List[RankingSortOrderInfo]]:
        return [
            {"name": "Overall Score", "precision": 2},
            {"name": "Galactic Search", "precision": 2},
            {"name": "Auto-Nav", "precision": 2},
            {"name": "Hyperdrive", "precision": 2},
            {"name": "Interstellar Accuracy", "precision": 2},
            {"name": "Power Port", "precision": 2},
        ]

    def valid_score_breakdown_keys(self) -> Set[str]:
        return set(
            [
                "adjustPoints",
                "autoCellPoints",
                "autoCellsBottom",
                "autoCellsInner",
                "autoCellsOuter",
                "autoInitLinePoints",
                "autoPoints",
                "controlPanelPoints",
                "endgamePoints",
                "endgameRobot1",
                "endgameRobot2",
                "endgameRobot3",
                "endgameRungIsLevel",
                "foulCount",
                "foulPoints",
                "initLineRobot1",
                "initLineRobot2",
                "initLineRobot3",
                "rp",
                "shieldEnergizedRankingPoint",
                "shieldOperationalRankingPoint",
                "stage1Activated",
                "stage2Activated",
                "stage3Activated",
                "stage3TargetColor",
                "techFoulCount",
                "teleopCellPoints",
                "teleopCellsBottom",
                "teleopCellsInner",
                "teleopCellsOuter",
                "teleopPoints",
                "totalPoints",
            ]
        )

    def round_robin_tiebreak_keys(self) -> List[str]:
        return []

    def round_robin_tiebreaker_names(self) -> List[str]:
        return []
