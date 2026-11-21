from typing import List

from backend.tasks_io.datafeeds.datafeed_html import DatafeedHTML
from backend.tasks_io.datafeeds.parsers.first.resource_library_parser import (
    ParsedHallOfFameTeam,
    ResourceLibraryParser,
)


class DatafeedResourceLibrary(
    DatafeedHTML[ResourceLibraryParser, ParsedHallOfFameTeam]
):
    HALL_OF_FAME_URL = "https://www.firstinspires.org/resource-library/frc/past-winners-of-the-chairmans-award"

    def get_hall_of_fame_teams(self) -> List[ParsedHallOfFameTeam]:
        teams, _ = self.parse(self.HALL_OF_FAME_URL, ResourceLibraryParser())
        return teams
