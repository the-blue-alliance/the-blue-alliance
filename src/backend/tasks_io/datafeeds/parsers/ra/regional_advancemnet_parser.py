from pyre_extensions import JSON

from backend.common.models.regional_pool_advancement import (
    ChampionshipStatus,
    RegionalPoolAdvancement,
    TeamRegionalPoolAdvancement,
)
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase


class RegionalAdvancementParser(ParserBase[RegionalPoolAdvancement]):

    def parse(self, response: JSON) -> RegionalPoolAdvancement:
        if not isinstance(response, dict):
            return {}
        team_advancement = response.get("teams", [])
        if not isinstance(team_advancement, list):
            return {}

        advancemnet: RegionalPoolAdvancement = {}
        year = response["season"]
        for team in team_advancement:
            if not isinstance(team, dict):
                continue

            cmp_status = ChampionshipStatus.from_api_string(team["championshipStatus"])
            if not cmp_status or cmp_status == ChampionshipStatus.NOT_INVITED:
                continue

            team_key = f"frc{team['teamNumber']}"
            qualifying_event_code = team["championshipQualifyingEventCode"]
            qualifying_award_name = team["championshipQualifyingEventAward"]
            qualifying_pool_week = team["championshipQualifyingPoolWeek"]

            team_advancement = TeamRegionalPoolAdvancement(
                cmp=True,
                cmp_status=cmp_status,
            )
            if qualifying_event_code:
                team_advancement["qualifying_event"] = (
                    f"{year}{qualifying_event_code.lower()}"
                )
            if qualifying_award_name:
                team_advancement["qualifying_award_name"] = qualifying_award_name
            if qualifying_pool_week:
                team_advancement["qualifying_pool_week"] = qualifying_pool_week

            advancemnet[team_key] = team_advancement
        return advancemnet
