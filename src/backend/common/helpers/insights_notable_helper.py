from typing import DefaultDict, Dict, List

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.insights_helper_utils import (
    create_insight,
    LeaderboardInsightArguments,
    make_insights_from_functions,
)
from backend.common.models.insight import Insight, InsightEnumId, NotableEntry, NotablesData
from backend.common.models.keys import EventKey, TeamKey, Year


class InsightsNotableHelper:
    @staticmethod
    def make_insights(year: Year) -> List[Insight]:
        return make_insights_from_functions(
            year,
            [
                InsightsNotableHelper._calculate_notables_hall_of_fame,
                InsightsNotableHelper._calculate_notables_world_champions,
                InsightsNotableHelper._calculate_notables_division_winners,
                InsightsNotableHelper._calculate_notables_division_finals_appearances,
            ],
        )

    @staticmethod
    def _create_notable_insight(
        teams: Dict[TeamKey, List[EventKey]] | DefaultDict[TeamKey, List[EventKey]],
        insight_type: InsightEnumId,
        year: int,
    ) -> Insight:
        return create_insight(
            data=NotablesData(
                entries=[
                    NotableEntry(team_key=team_key, context=context)
                    for team_key, context in teams.items()
                ]
            ),
            name=Insight.INSIGHT_NAMES[insight_type],
            year=year,
        )

    @staticmethod
    def __make_notable_from_award_type_at_event_type(
        arguments: LeaderboardInsightArguments,
        award_type: AwardType,
        event_type: EventType,
        insight_type: InsightEnumId,
    ) -> Insight:
        team_context_map: Dict[TeamKey, List[EventKey]] = {}
        for award in arguments.awards:
            if (
                award.event_type_enum == event_type
                and award.award_type_enum == award_type
            ):
                for tk in award.team_list:
                    if str(tk.string_id()) not in team_context_map:
                        team_context_map[str(tk.string_id())] = []

                    team_context_map[str(tk.string_id())].append(
                        str(award.event.string_id())
                    )

        return InsightsNotableHelper._create_notable_insight(
            team_context_map,
            insight_type,
            arguments.year,
        )

    @staticmethod
    def _calculate_notables_hall_of_fame(
        arguments: LeaderboardInsightArguments,
    ) -> Insight:
        return InsightsNotableHelper.__make_notable_from_award_type_at_event_type(
            arguments,
            AwardType.CHAIRMANS,
            EventType.CMP_FINALS,
            Insight.TYPED_NOTABLES_HALL_OF_FAME,
        )

    @staticmethod
    def _calculate_notables_world_champions(
        arguments: LeaderboardInsightArguments,
    ) -> Insight:
        return InsightsNotableHelper.__make_notable_from_award_type_at_event_type(
            arguments,
            AwardType.WINNER,
            EventType.CMP_FINALS,
            Insight.TYPED_NOTABLES_WORLD_CHAMPIONS,
        )

    @staticmethod
    def _calculate_notables_division_winners(
        arguments: LeaderboardInsightArguments,
    ) -> Insight:
        return InsightsNotableHelper.__make_notable_from_award_type_at_event_type(
            arguments,
            AwardType.WINNER,
            EventType.CMP_DIVISION,
            Insight.TYPED_NOTABLES_DIVISION_WINNERS,
        )

    @staticmethod
    def _calculate_notables_division_finals_appearances(
        arguments: LeaderboardInsightArguments,
    ) -> Insight:
        team_context_map: Dict[TeamKey, List[EventKey]] = {}
        for award in arguments.awards:
            if (
                award.event_type_enum == EventType.CMP_DIVISION
                and award.award_type_enum in [AwardType.WINNER, AwardType.FINALIST]
            ):
                for tk in award.team_list:
                    if str(tk.string_id()) not in team_context_map:
                        team_context_map[str(tk.string_id())] = []

                    team_context_map[str(tk.string_id())].append(
                        str(award.event.string_id())
                    )

        return InsightsNotableHelper._create_notable_insight(
            team_context_map,
            Insight.TYPED_NOTABLES_DIVISION_FINALS_APPEARANCES,
            arguments.year,
        )
