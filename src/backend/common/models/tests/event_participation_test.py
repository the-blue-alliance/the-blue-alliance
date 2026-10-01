from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.models.event_participation import EventParticipation


def test_event_participation() -> None:
    event = Event(
        id="2020nyny",
        year=2020,
        event_short="nyny",
        event_type_enum=EventType.REGIONAL,
    )
    participation: EventParticipation = {
        "event": event,
        "matches": {"qm": []},
        "wlt": {"wins": 1, "losses": 2, "ties": 0},
        "qual_avg": 12.5,
        "elim_avg": None,
        "rank": 3,
        "awards": [{"name": "Winner"}],
        "playlist": "https://www.youtube.com/playlist?list=abc",
        "district_points": None,
    }
    assert participation["event"].key_name == "2020nyny"
    assert participation["rank"] == 3
    assert participation["elim_avg"] is None
    assert participation["awards"][0]["name"] == "Winner"
