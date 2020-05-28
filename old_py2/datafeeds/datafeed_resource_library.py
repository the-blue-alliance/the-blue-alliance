from datafeeds.datafeed_base import DatafeedBase
from datafeeds.resource_library_parser import ResourceLibraryParser


class DatafeedResourceLibrary(DatafeedBase):
    RESOURCE_LIBRARY_URL_PATTERN = "https://www.firstinspires.org/resource-library/frc/%s/"

    def __init__(self, *args, **kw):
        super(DatafeedResourceLibrary, self).__init__(*args, **kw)

    def getHallOfFameTeams(self):
        url = self.RESOURCE_LIBRARY_URL_PATTERN % ("past-winners-of-the-chairmans-award")
        teams, _ = self.parse(url, ResourceLibraryParser)

        return teams
