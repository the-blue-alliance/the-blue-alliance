from typing import List, Optional

from typing_extensions import TypedDict

from backend.common.models.event_team_status import WLTRecord
from backend.common.models.keys import TeamKey


class _EventRankingOptionalFields(TypedDict, total=False):
    # Derived in dict converter
    extra_stats: List[float]


class EventRanking(_EventRankingOptionalFields, total=True):
    rank: int
    team_key: TeamKey
    record: Optional[WLTRecord]
    qual_average: Optional[float]
    matches_played: int
    dq: int
    sort_orders: List[float]
