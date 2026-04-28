import datetime
from typing import List, NamedTuple, Optional

from backend.common.consts.alliance_color import AllianceColor
from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.helpers.insights_v2.timeseries.calculator import (
    TimeseriesV2Calculator,
)
from backend.common.models.event import Event
from backend.common.models.insight_v2 import (
    MatchRecordPointContext,
    TimeseriesData,
    TimeseriesPoint,
    TimeseriesPointWithMatchRecord,
    TimeseriesSeries,
)


class _RecordMatch(NamedTuple):
    score: int
    match_key: str
    alliance_teams: List[str]
    post_result_time: datetime.datetime
    year: int


class HighScoreOverTimeV2Calculator(TimeseriesV2Calculator):
    """
    Tracks the season high score for a single year. Can only be run for a
    specific year, not year=0.

    Collects all valid matches across all events, then sorts globally by
    post_result_time in _build_timeseries_data to correctly handle concurrent
    events running in the same week.
    """

    def __init__(self) -> None:
        self._all_matches: List[_RecordMatch] = []

    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.HIGH_SCORE_OVER_TIME

    def on_event(self, event: Event) -> None:
        for match in event.matches or []:
            t: Optional[datetime.datetime] = (
                match.post_result_time or match.actual_time or match.time
            )
            if t is None:
                continue

            red_score = int(match.alliances[AllianceColor.RED]["score"])  # type: ignore[union-attr]
            blue_score = int(match.alliances[AllianceColor.BLUE]["score"])  # type: ignore[union-attr]
            if red_score < 0 or blue_score < 0:
                continue

            if red_score >= blue_score:
                high_color = AllianceColor.RED
                high_score = red_score
            else:
                high_color = AllianceColor.BLUE
                high_score = blue_score

            self._all_matches.append(
                _RecordMatch(
                    score=high_score,
                    match_key=match.key_name,  # type: ignore[union-attr]
                    alliance_teams=list(match.alliances[high_color]["teams"]),  # type: ignore[union-attr]
                    post_result_time=t,
                    year=event.year,
                )
            )

    def _build_timeseries_data(self) -> TimeseriesData:
        if not self._all_matches:
            return TimeseriesData(
                series=[],
                x_type="year",
                x_label="Year",
                y_label="Score",
                point_context_type="match_record",
            )

        current_record = -1
        record_matches: List[_RecordMatch] = []
        for m in sorted(self._all_matches, key=lambda m: m.post_result_time):
            if m.score > current_record:
                current_record = m.score
                record_matches.append(m)

        points: List[TimeseriesPoint] = [
            TimeseriesPointWithMatchRecord(
                x=record.year,
                y=float(record.score),
                context=MatchRecordPointContext(
                    match_key=record.match_key,
                    alliance=record.alliance_teams,
                    post_result_time=int(record.post_result_time.timestamp()),
                    is_current=i == len(record_matches) - 1,
                ),
            )
            for i, record in enumerate(record_matches)
        ]

        return TimeseriesData(
            series=[TimeseriesSeries(label="World Record", points=points)],
            x_type="year",
            x_label="Year",
            y_label="Score",
            point_context_type="match_record",
        )
