from typing import TypedDict

from backend.common.models.event_team_status import WLTRecord
from backend.common.models.keys import TeamKey


class _EventRankingOptionalFields(TypedDict, total=False):
    # Derived in dict converter
    extra_stats: list[float]


class EventRanking(_EventRankingOptionalFields, total=True):
    rank: int
    team_key: TeamKey
    record: WLTRecord | None
    qual_average: float | None
    matches_played: int
    dq: int
    sort_orders: list[float]
