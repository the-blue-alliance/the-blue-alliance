import enum

from backend.common.consts.string_enum import StrEnum
from backend.common.models.insight import Insight


@enum.unique
class InsightType(StrEnum):
    MATCHES = "matches"
    AWARDS = "awards"
    PREDICTIONS = "predictions"
    LEADERBOARD = "leaderboard"
    NOTABLES = "notables"


LEADERBOARD_INSIGHTS = [
    Insight.BLUE_BANNERS,
    Insight.MATCHES_PLAYED,
]

NOTABLES_INSIGHTS = [
    Insight.CA_WINNER,
    Insight.WORLD_CHAMPIONS,
]
