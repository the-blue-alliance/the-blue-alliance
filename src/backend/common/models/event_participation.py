from typing import Dict, List, Optional

from typing_extensions import TypedDict

from backend.common.models.event import Event


class EventParticipation(TypedDict):
    event: Event
    matches: Dict
    wlt: Optional[Dict]
    qual_avg: Optional[float]
    elim_avg: Optional[float]
    rank: Optional[int]
    awards: List[Dict]
    playlist: str
    district_points: Optional[Dict]
