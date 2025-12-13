from dataclasses import dataclass
from typing import Dict

from pyre_extensions import JSON

from backend.common.models.keys import TeamKey
from backend.common.models.regional_pool_advancement import (
    ChampionshipStatus,
    RegionalPoolAdvancement,
    TeamRegionalPoolAdvancement,
)
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase


@dataclass
class TParsedRegionalAdvancement:
    advancement: RegionalPoolAdvancement
    adjustments: Dict[TeamKey, int]


class RegionalAdvancementParser(ParserBase[TParsedRegionalAdvancement]):

    def parse(self, response: JSON) -> TParsedRegionalAdvancement:
        if not isinstance(response, dict):
            return TParsedRegionalAdvancement(advancement={}, adjustments={})
        team_advancement = response.get("teams", [])
        if not isinstance(team_advancement, list):
            return TParsedRegionalAdvancement(advancement={}, adjustments={})

        advancement: RegionalPoolAdvancement = {}
        adjustments: Dict[TeamKey, int] = {}
        year = response["season"]
        for team in team_advancement:
            if not isinstance(team, dict):
                continue

            team_key = f"frc{team['teamNumber']}"
            if adjust := team.get("adjustPoints"):
                adjustments[team_key] = adjust

            cmp_status = ChampionshipStatus(team["championshipStatus"])
            if not cmp_status or cmp_status == ChampionshipStatus.NOT_INVITED:
                continue

            qualifying_event_code = team["championshipQualifyingEventCode"]
            qualifying_award_name = team["championshipQualifyingEventAward"]
            qualifying_pool_week = team["championshipQualifyingPoolWeek"]

            team_advancement = TeamRegionalPoolAdvancement(
                cmp=(cmp_status != ChampionshipStatus.DECLINED),
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

            advancement[team_key] = team_advancement

        return TParsedRegionalAdvancement(
            advancement=advancement,
            adjustments=adjustments,
        )
