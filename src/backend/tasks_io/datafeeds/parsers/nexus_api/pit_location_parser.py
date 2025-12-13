from typing import cast, Dict

from pyre_extensions import JSON

from backend.common.models.event_team_pit_location import EventTeamPitLocation
from backend.common.models.keys import TeamKey
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase


class NexusAPIPitLocationParser(ParserBase[Dict[TeamKey, EventTeamPitLocation]]):

    def parse(self, response: JSON) -> Dict[TeamKey, EventTeamPitLocation]:
        if response == "No pits." or not isinstance(response, dict):
            return {}

        return {
            f"frc{team_number}": EventTeamPitLocation(location=cast(str, pit_location))
            for team_number, pit_location in response.items()
        }
