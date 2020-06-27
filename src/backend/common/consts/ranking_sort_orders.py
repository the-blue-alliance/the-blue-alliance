from typing import Dict, List

from backend.common.models.ranking_sort_order_info import RankingSortOrderInfo

SORT_ORDER_INFO: Dict[int, List[RankingSortOrderInfo]] = {
    2020: [
        {"name": "Ranking Score", "precision": 2},
        {"name": "Auto", "precision": 0},
        {"name": "End Game", "precision": 0},
        {"name": "Teleop Cell + CPanel", "precision": 0},
    ],
    2019: [
        {"name": "Ranking Score", "precision": 2},
        {"name": "Cargo", "precision": 0},
        {"name": "Hatch Panel", "precision": 0},
        {"name": "HAB Climb", "precision": 0},
        {"name": "Sandstorm Bonus", "precision": 0},
    ],
    2018: [
        {"name": "Ranking Score", "precision": 2},
        {"name": "Park/Climb Points", "precision": 0},
        {"name": "Auto", "precision": 0},
        {"name": "Ownership", "precision": 0},
        {"name": "Vault", "precision": 0},
    ],
    2017: [
        {"name": "Ranking Score", "precision": 2},
        {"name": "Match Points", "precision": 0},
        {"name": "Auto", "precision": 0},
        {"name": "Rotor", "precision": 0},
        {"name": "Touchpad", "precision": 0},
        {"name": "Pressure", "precision": 0},
    ],
    2016: [
        {"name": "Ranking Score", "precision": 0},
        {"name": "Auto", "precision": 0},
        {"name": "Scale/Challenge", "precision": 0},
        {"name": "Goals", "precision": 0},
        {"name": "Defense", "precision": 0},
    ],
    2015: [
        {"name": "Qual Avg.", "precision": 1},
        {"name": "Coopertition", "precision": 0},
        {"name": "Auto", "precision": 0},
        {"name": "Container", "precision": 0},
        {"name": "Tote", "precision": 0},
        {"name": "Litter", "precision": 0},
    ],
    2014: [
        {"name": "Qual Score", "precision": 0},
        {"name": "Assist", "precision": 0},
        {"name": "Auto", "precision": 0},
        {"name": "Truss & Catch", "precision": 0},
        {"name": "Teleop", "precision": 0},
    ],
    2013: [
        {"name": "Qual Score", "precision": 0},
        {"name": "Auto", "precision": 0},
        {"name": "Climb", "precision": 0},
        {"name": "Teleop", "precision": 0},
    ],
    2012: [
        {"name": "Qual Score", "precision": 0},
        {"name": "Hybrid", "precision": 0},
        {"name": "Bridge", "precision": 0},
        {"name": "Teleop", "precision": 0},
    ],
    2011: [
        {"name": "Qual Score", "precision": 0},
        {"name": "Ranking Score", "precision": 2},
    ],
    2010: [
        {"name": "Seeding Score", "precision": 0},
        {"name": "Coopertition Bonus", "precision": 0},
        {"name": "Hanging Points", "precision": 0},
    ],
    2009: [
        {"name": "Qual Score", "precision": 0},
        {"name": "Seeding Score", "precision": 2},
        {"name": "Match Points", "precision": 0},
    ],
    2008: [
        {"name": "Qual Score", "precision": 0},
        {"name": "Seeding Score", "precision": 2},
        {"name": "Match Points", "precision": 0},
    ],
    2007: [
        {"name": "Qual Score", "precision": 0},
        {"name": "Seeding Score", "precision": 2},
        {"name": "Match Points", "precision": 0},
    ],
    2006: [
        {"name": "Qual Score", "precision": 0},
        {"name": "Seeding Score", "precision": 2},
        {"name": "Match Points", "precision": 0},
    ],
}
