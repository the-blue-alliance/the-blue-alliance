from collections import defaultdict
from typing import DefaultDict, Dict, List

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import ELIM_LEVELS
from backend.common.consts.event_type import CMP_EVENT_TYPES
from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.helpers.insights_v2.timeseries.calculator import (
    TimeseriesV2Calculator,
)
from backend.common.models.event import Event
from backend.common.models.insight_v2 import (
    InsightCategory,
    InsightV2,
    TimeseriesData,
    TimeseriesPointNoContext,
    TimeseriesSeries,
)
from backend.common.models.keys import Year


class AverageMatchScoreByWeekV2Calculator(TimeseriesV2Calculator):
    """
    Tracks the average match score (average score of a single alliance) by
    week, for a single year. Produces two insights: one across all matches,
    one across elim matches only. Championship events (which have no numeric
    week) are folded into a trailing synthetic week after the last regular
    week.
    """

    def __init__(self) -> None:
        self._week_sums: DefaultDict[int, int] = defaultdict(int)
        self._week_counts: DefaultDict[int, int] = defaultdict(int)
        self._elim_week_sums: DefaultDict[int, int] = defaultdict(int)
        self._elim_week_counts: DefaultDict[int, int] = defaultdict(int)
        self._cmp_sum = 0
        self._cmp_count = 0
        self._elim_cmp_sum = 0
        self._elim_cmp_count = 0

    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.AVERAGE_MATCH_SCORE_BY_WEEK

    def on_event(self, event: Event) -> None:
        week = event.week
        is_cmp = event.event_type_enum in CMP_EVENT_TYPES
        if week is None and not is_cmp:
            return

        for match in event.matches or []:
            if not match.has_been_played:
                continue
            red = int(match.alliances[AllianceColor.RED]["score"])  # type: ignore[union-attr]
            blue = int(match.alliances[AllianceColor.BLUE]["score"])  # type: ignore[union-attr]
            total = red + blue
            is_elim = match.comp_level in ELIM_LEVELS

            if is_cmp:
                self._cmp_sum += total
                self._cmp_count += 1
                if is_elim:
                    self._elim_cmp_sum += total
                    self._elim_cmp_count += 1
            else:
                w = week + 1  # type: ignore[operator]
                self._week_sums[w] += total
                self._week_counts[w] += 1
                if is_elim:
                    self._elim_week_sums[w] += total
                    self._elim_week_counts[w] += 1

    def _build_points(
        self,
        week_sums: Dict[int, int],
        week_counts: Dict[int, int],
        cmp_sum: int,
        cmp_count: int,
    ) -> List[TimeseriesPointNoContext]:
        trailing_week = max(week_counts.keys(), default=0) + 1

        points: List[TimeseriesPointNoContext] = [
            TimeseriesPointNoContext(
                x=week, y=float(week_sums[week]) / week_counts[week] / 2
            )
            for week in sorted(week_counts.keys())
        ]
        if cmp_count:
            points.append(
                TimeseriesPointNoContext(
                    x=trailing_week, y=float(cmp_sum) / cmp_count / 2
                )
            )
        return points

    def _build_timeseries_data(self) -> TimeseriesData:
        # Unused: make_insights is overridden to emit two insights.
        raise NotImplementedError

    def make_insights(
        self, year: Year, team_to_district: Dict[str, str]
    ) -> List[InsightV2]:
        insights: List[InsightV2] = []

        all_points = self._build_points(
            self._week_sums, self._week_counts, self._cmp_sum, self._cmp_count
        )
        if all_points:
            name = InsightV2Names.AVERAGE_MATCH_SCORE_BY_WEEK
            insights.append(
                InsightV2(
                    id=InsightV2.render_key_name(
                        year, InsightCategory.TIMESERIES, name.name
                    ),
                    name=name.name,
                    display_name=name.display_name,
                    year=year,
                    category=InsightCategory.TIMESERIES,
                    data_json=TimeseriesData(
                        series=[
                            TimeseriesSeries(label="All Matches", points=all_points)
                        ],
                        x_type="week",
                        x_label="Week",
                        y_label="Average Score",
                        point_context_type="none",
                    ),
                )
            )

        elim_points = self._build_points(
            self._elim_week_sums,
            self._elim_week_counts,
            self._elim_cmp_sum,
            self._elim_cmp_count,
        )
        if elim_points:
            name = InsightV2Names.AVERAGE_ELIM_MATCH_SCORE_BY_WEEK
            insights.append(
                InsightV2(
                    id=InsightV2.render_key_name(
                        year, InsightCategory.TIMESERIES, name.name
                    ),
                    name=name.name,
                    display_name=name.display_name,
                    year=year,
                    category=InsightCategory.TIMESERIES,
                    data_json=TimeseriesData(
                        series=[
                            TimeseriesSeries(label="Elim Matches", points=elim_points)
                        ],
                        x_type="week",
                        x_label="Week",
                        y_label="Average Score",
                        point_context_type="none",
                    ),
                )
            )

        return insights
