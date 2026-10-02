from typing import List, Optional

from backend.common.game_specific.registry import get_game
from backend.common.models.event_insights import EventInsights
from backend.common.models.keys import Year
from backend.common.models.match import Match


class EventInsightsHelper:
    @classmethod
    def calculate_event_insights(
        cls, matches: List[Match], year: Year
    ) -> Optional[EventInsights]:
        return get_game(year).calculate_event_insights(matches)
