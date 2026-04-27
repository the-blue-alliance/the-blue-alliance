from typing import cast

from backend.common.models.event_team_pit_location import EventTeamPitLocation
from backend.common.nexus_api.types import PitAddresses
from backend.tasks_io.datafeeds.parsers.nexus_api.pit_location_parser import (
    NexusAPIPitLocationParser,
)


def test_bad_format() -> None:
    data = cast(PitAddresses, [])
    parsed = NexusAPIPitLocationParser().parse(data)
    assert parsed == {}


def test_no_pits() -> None:
    data = cast(PitAddresses, "No pits.")
    parsed = NexusAPIPitLocationParser().parse(data)
    assert parsed == {}


def test_parse_pits() -> None:
    data: PitAddresses = {"100": "A1"}
    parsed = NexusAPIPitLocationParser().parse(data)
    assert parsed == {
        "frc100": EventTeamPitLocation(location="A1"),
    }
