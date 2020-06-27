from typing import List, Optional

from typing_extensions import TypedDict

from backend.common.models.event_team_status import WLTRecord
from backend.common.models.keys import TeamKey


class EventRanking(TypedDict):
    rank: int
    team_key: TeamKey
    record: Optional[WLTRecord]
    qual_average: Optional[float]
    matches_played: int
    dq: int
    sort_orders: List[float]
