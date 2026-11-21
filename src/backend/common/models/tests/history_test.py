from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.history import History


def test_history() -> None:
    event = Event(id="2019nyny", year=2019, event_short="nyny")
    award = Award(
        id="2019nyny_1",
        year=2019,
        award_type_enum=AwardType.WINNER,
        event_type_enum=EventType.REGIONAL,
        event=event.key,
        name_str="Winner",
    )
    history = History(events=[event], awards=[award])
    assert history["events"] == [event]
    assert history["awards"] == [award]
