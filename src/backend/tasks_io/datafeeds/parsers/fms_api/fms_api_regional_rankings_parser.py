from dataclasses import dataclass
from typing import cast, Dict, List, Tuple

from backend.common.frc_api.types import (
    RegionalRankingTeamDetailListModelV31,
    RegionalRankingTeamDetailModelV31,
)
from backend.common.models.keys import TeamKey
from backend.common.models.regional_pool_advancement import (
    ChampionshipStatus,
    RegionalPoolAdvancement,
    TeamRegionalPoolAdvancement,
)
from backend.tasks_io.datafeeds.parsers.parser_paginated import ParserPaginated


@dataclass
class TParsedRegionalAdvancement:
    advancement: RegionalPoolAdvancement
    adjustments: Dict[TeamKey, int]


class FMSAPIRegionalRankingsParser(
    ParserPaginated[RegionalRankingTeamDetailListModelV31, TParsedRegionalAdvancement]
):
    def parse(
        self, response: RegionalRankingTeamDetailListModelV31
    ) -> Tuple[TParsedRegionalAdvancement, bool]:
        current_page = response["pageCurrent"]
        total_pages = response["pageTotal"]
        year = response["season"]

        advancement: RegionalPoolAdvancement = {}
        adjustments: Dict[TeamKey, int] = {}

        api_teams = cast(
            List[RegionalRankingTeamDetailModelV31], response.get("teams") or []
        )
        for team_data in api_teams:
            team_key = f"frc{team_data['teamNumber']}"

            if adjust := team_data.get("adjustPoints"):
                adjustments[team_key] = adjust

            # Map the API championship status to our internal enum
            api_status = team_data.get("championshipStatus")
            if not api_status or api_status == "None" or api_status == "NotQualified":
                continue

            # Convert API status string to ChampionshipStatus enum
            status_map = {
                "QualifiedAtEventByRanking": ChampionshipStatus.EVENT_QUALIFIED,
                "QualifiedAtEventByAward": ChampionshipStatus.EVENT_QUALIFIED,
                "QualifiedFromRegionalPool": ChampionshipStatus.POOL_QUALIFIED,
                "Prequalified": ChampionshipStatus.PRE_QUALIFIED,
            }

            cmp_status = status_map.get(api_status)
            if not cmp_status:
                continue

            # Build the team advancement record
            team_advancement = TeamRegionalPoolAdvancement(
                cmp=(not team_data.get("declinedFirstCmp", False)),
                cmp_status=cmp_status,
            )

            # Add optional fields if present
            qualifying_event_code = team_data.get("qualifiedFirstCmpEventCode")
            qualifying_award_name = team_data.get("qualifiedFirstCmpAwardName")
            qualifying_pool_week = team_data.get("qualifiedFirstCmpEventWeek")

            if qualifying_event_code:
                team_advancement["qualifying_event"] = (
                    f"{year}{qualifying_event_code.lower()}"
                )
            if qualifying_award_name:
                team_advancement["qualifying_award_name"] = qualifying_award_name
            if qualifying_pool_week:
                team_advancement["qualifying_pool_week"] = qualifying_pool_week

            advancement[team_key] = team_advancement

        return (
            TParsedRegionalAdvancement(
                advancement=advancement,
                adjustments=adjustments,
            ),
            (current_page < total_pages),
        )
