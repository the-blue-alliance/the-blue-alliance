from typing import TypedDict

from backend.common.models.event import Event


class EventParticipation(TypedDict):
    event: Event
    matches: dict
    wlt: dict | None
    qual_avg: float | None
    elim_avg: float | None
    rank: int | None
    awards: list[dict]
    playlist: str
    district_points: dict | None
