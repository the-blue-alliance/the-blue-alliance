from collections import defaultdict
from typing import DefaultDict

from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.helpers.insights_v2.timeseries.calculator import (
    TimeseriesV2Calculator,
)
from backend.common.models.event import Event
from backend.common.models.insight_v2 import (
    TimeseriesData,
    TimeseriesPointNoContext,
    TimeseriesSeries,
)


class NumMatchesByYearV2Calculator(TimeseriesV2Calculator):
    """
    Counts played matches per season across all in-season events. All-time
    (year=0) only, global, one point per year.
    """

    def __init__(self) -> None:
        self._counts: DefaultDict[int, int] = defaultdict(int)

    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.NUM_MATCHES_BY_YEAR

    def on_event(self, event: Event) -> None:
        count = sum(1 for match in (event.matches or []) if match.has_been_played)
        if count:
            self._counts[event.year] += count

    def _build_timeseries_data(self) -> TimeseriesData:
        points = [
            TimeseriesPointNoContext(x=year, y=float(self._counts[year]))
            for year in sorted(self._counts)
        ]
        return TimeseriesData(
            series=[TimeseriesSeries(label="Matches", points=points)],
            x_type="year",
            x_label="Year",
            y_label="Matches",
            point_context_type="none",
        )
