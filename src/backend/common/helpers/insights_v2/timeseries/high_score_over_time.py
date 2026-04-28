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

    Processes matches within each event in post_result_time order and records
    only those that break the running season record, keeping memory usage
    proportional to the number of records set (not total matches played).
    """

    def __init__(self) -> None:
        self._current_record: int = -1
        self._record_matches: List[_RecordMatch] = []

    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.HIGH_SCORE_OVER_TIME

    def on_event(self, event: Event) -> None:
        timed: List[tuple[object, datetime.datetime]] = []
        for match in event.matches or []:
            t: Optional[datetime.datetime] = (
                match.post_result_time or match.actual_time or match.time
            )
            if t is not None:
                timed.append((match, t))

        for match, t in sorted(timed, key=lambda x: x[1]):
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

            if high_score > self._current_record:
                self._current_record = high_score
                self._record_matches.append(
                    _RecordMatch(
                        score=high_score,
                        match_key=match.key_name,  # type: ignore[union-attr]
                        alliance_teams=list(match.alliances[high_color]["teams"]),  # type: ignore[union-attr]
                        post_result_time=t,
                        year=event.year,
                    )
                )

    def _build_timeseries_data(self) -> TimeseriesData:
        if not self._record_matches:
            return TimeseriesData(
                series=[],
                x_type="year",
                x_label="Year",
                y_label="Score",
                point_context_type="match_record",
            )

        now = datetime.datetime.now(datetime.timezone.utc).replace(  # pyre-ignore[16]
            tzinfo=None
        )
        points: List[TimeseriesPoint] = []

        for i, record in enumerate(self._record_matches):
            is_current = i == len(self._record_matches) - 1
            if is_current:
                held_duration_seconds = int(
                    (now - record.post_result_time).total_seconds()
                )
            else:
                next_time = self._record_matches[i + 1].post_result_time
                held_duration_seconds = int(
                    (next_time - record.post_result_time).total_seconds()
                )

            points.append(
                TimeseriesPointWithMatchRecord(
                    x=record.year,
                    y=float(record.score),
                    context=MatchRecordPointContext(
                        match_key=record.match_key,
                        alliance=record.alliance_teams,
                        held_duration_seconds=held_duration_seconds,
                        is_current=is_current,
                    ),
                )
            )

        return TimeseriesData(
            series=[TimeseriesSeries(label="World Record", points=points)],
            x_type="year",
            x_label="Year",
            y_label="Score",
            point_context_type="match_record",
        )
