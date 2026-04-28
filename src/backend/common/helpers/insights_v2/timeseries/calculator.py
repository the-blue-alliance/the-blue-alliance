from abc import abstractmethod
from typing import Dict, List

from backend.common.helpers.insights_v2.base import InsightV2Calculator
from backend.common.helpers.insights_v2.names import InsightV2NameEntry
from backend.common.models.insight_v2 import (
    InsightCategory,
    InsightV2,
    TimeseriesData,
)
from backend.common.models.keys import Year


class TimeseriesV2Calculator(InsightV2Calculator):
    """
    Base class for timeseries insights. Subclasses implement on_event to
    collect data and _build_timeseries_data to produce the final series.
    Timeseries insights are global (no district scoping).
    """

    @property
    @abstractmethod
    def insight_name(self) -> InsightV2NameEntry: ...

    @abstractmethod
    def _build_timeseries_data(self) -> TimeseriesData: ...

    def make_insights(
        self, year: Year, team_to_district: Dict[str, str]
    ) -> List[InsightV2]:
        data = self._build_timeseries_data()
        if not data["series"] or not any(s["points"] for s in data["series"]):
            return []

        name = self.insight_name
        return [
            InsightV2(
                id=InsightV2.render_key_name(
                    year, InsightCategory.TIMESERIES, name.name
                ),
                name=name.name,
                display_name=name.display_name,
                year=year,
                category=InsightCategory.TIMESERIES,
                data_json=data,
            )
        ]
