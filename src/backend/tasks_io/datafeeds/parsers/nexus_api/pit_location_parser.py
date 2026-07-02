from typing import Dict

from backend.common.datafeeds.parsers.parser_base import ParserBase
from backend.common.models.event_team_pit_location import EventTeamPitLocation
from backend.common.models.keys import TeamKey
from backend.common.nexus_api.types import PitAddresses


class NexusAPIPitLocationParser(
    ParserBase[PitAddresses, Dict[TeamKey, EventTeamPitLocation]]
):

    def parse(self, response: PitAddresses) -> Dict[TeamKey, EventTeamPitLocation]:
        if not isinstance(response, dict):
            return {}

        return {
            f"frc{team_number}": EventTeamPitLocation(location=pit_location)
            for team_number, pit_location in response.items()
        }
