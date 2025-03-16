from pyre_extensions import JSON

from backend.common.models.event_team_pit_location import EventTeamPitLocation
from backend.tasks_io.datafeeds.parsers.nexus_api.pit_location_parser import (
    NexusAPIPitLocationParser,
)


def test_bad_format() -> None:
    data: JSON = []
    parsed = NexusAPIPitLocationParser().parse(data)
    assert parsed == {}


def test_no_pits() -> None:
    data: JSON = "No pits."
    parsed = NexusAPIPitLocationParser().parse(data)
    assert parsed == {}


def test_parse_pits() -> None:
    data: JSON = {"100": "A1"}
    parsed = NexusAPIPitLocationParser().parse(data)
    assert parsed == {
        "frc100": EventTeamPitLocation(location="A1"),
    }
