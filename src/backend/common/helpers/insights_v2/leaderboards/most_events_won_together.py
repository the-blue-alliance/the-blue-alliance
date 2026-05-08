import itertools
from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional, Set

from backend.common.consts.award_type import AwardType
from backend.common.helpers.insights_v2.leaderboards.calculator import (
    build_leaderboard_pair_event_list_rankings,
    LeaderboardV2Calculator,
)
from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.models.event import Event
from backend.common.models.insight_v2 import (
    LeaderboardContextType,
    LeaderboardKeyType,
    LeaderboardRanking,
)


class MostEventsWonTogetherV2Calculator(LeaderboardV2Calculator):
    def __init__(self) -> None:
        super().__init__()
        self._pair_events: DefaultDict[str, List[str]] = defaultdict(list)

    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.MOST_EVENTS_WON_TOGETHER

    @property
    def key_type(self) -> LeaderboardKeyType:
        return "team_pair"

    @property
    def context_type(self) -> LeaderboardContextType:
        return "event_list"

    @property
    def min_count(self) -> int:
        return 2

    @property
    def team_keys(self) -> Set[str]:
        keys: Set[str] = set()
        for pair_key in self.counts:
            team_a, team_b = pair_key.split("|")
            keys.add(team_a)
            keys.add(team_b)
        return keys

    def _build_rankings(self, counts: Dict[str, int]) -> List[LeaderboardRanking]:
        filtered = {k: self._pair_events[k] for k in counts}
        return build_leaderboard_pair_event_list_rankings(
            filtered, min_count=self.min_count
        )

    def _get_district(
        self, key: str, team_to_district: Dict[str, str]
    ) -> Optional[str]:
        team_a, team_b = key.split("|")
        district_a = team_to_district.get(team_a)
        district_b = team_to_district.get(team_b)
        return district_a if district_a and district_a == district_b else None

    def _record_pair_event(self, pair_key: str, event_key: str) -> None:
        if event_key not in self._pair_events[pair_key]:
            self._increment(pair_key)
            self._pair_events[pair_key].append(event_key)

    def on_event(self, event: Event) -> None:
        event_key = str(event.key.id())
        for award in event.awards:
            if award.award_type_enum == AwardType.WINNER:
                teams = [str(k.id()) for k in award.team_list]
                for team_a, team_b in itertools.combinations(teams, 2):
                    pair = sorted([team_a, team_b], key=lambda k: int(k[3:]))
                    self._record_pair_event(f"{pair[0]}|{pair[1]}", event_key)
