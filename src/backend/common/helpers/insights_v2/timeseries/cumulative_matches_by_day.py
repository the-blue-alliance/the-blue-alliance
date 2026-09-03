import datetime
from collections import Counter
from typing import List, Optional

from backend.common.consts.comp_level import CompLevel
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

_EARLIEST_PLAUSIBLE_TIMESTAMP = datetime.datetime(1992, 1, 1)
_UNIX_EPOCH_DAY = datetime.date(1970, 1, 1)


def _day_epoch(day: datetime.date) -> int:
    return (day - _UNIX_EPOCH_DAY).days * 86400


class CumulativeMatchesByDayV2Calculator(TimeseriesV2Calculator):
    """
    Tracks the running cumulative count of played matches over the course of a
    single season, one point per calendar day from the season's first to last
    match. Global, run for a specific year only.
    """

    def __init__(self) -> None:
        self._day_counts: Counter[datetime.date] = Counter()

    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.CUMULATIVE_MATCHES_BY_DAY

    def on_event(self, event: Event) -> None:
        for match in event.matches or []:
            if not match.has_been_played:
                continue

            t: Optional[datetime.datetime] = (
                match.post_result_time or match.actual_time or match.time
            )
            if t is not None and t < _EARLIEST_PLAUSIBLE_TIMESTAMP:
                t = None
            if t is None:
                if match.comp_level == CompLevel.QM:
                    t = event.start_date
                else:
                    t = event.end_date
            if t is None:
                continue

            day = t.date()
            if day.year != event.year:
                continue

            self._day_counts[day] += 1

    def _build_timeseries_data(self) -> TimeseriesData:
        if not self._day_counts:
            return TimeseriesData(
                series=[],
                x_type="date",
                x_label="Date",
                y_label="Matches Played",
                point_context_type="none",
            )

        first_day = min(self._day_counts)
        last_day = max(self._day_counts)

        points: List[TimeseriesPointNoContext] = []
        running = 0
        day = first_day
        while day <= last_day:
            running += self._day_counts.get(day, 0)
            points.append(TimeseriesPointNoContext(x=_day_epoch(day), y=float(running)))
            day += datetime.timedelta(days=1)

        return TimeseriesData(
            series=[TimeseriesSeries(label="Matches Played", points=points)],
            x_type="date",
            x_label="Date",
            y_label="Matches Played",
            point_context_type="none",
        )
