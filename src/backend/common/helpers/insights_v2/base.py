from abc import ABC, abstractmethod
from typing import Dict, List

from backend.common.models.event import Event
from backend.common.models.insight_v2 import InsightV2
from backend.common.models.keys import Year


class InsightV2Calculator(ABC):
    @abstractmethod
    def on_event(self, event: Event) -> None: ...

    @abstractmethod
    def make_insights(
        self, year: Year, team_to_district: Dict[str, str]
    ) -> List[InsightV2]: ...
