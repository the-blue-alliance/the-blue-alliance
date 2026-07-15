import datetime
from collections import defaultdict
from typing import DefaultDict, Dict, List, NamedTuple, Optional

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.renamed_districts import RenamedDistricts
from backend.common.helpers.insights_v2.match_alliance_points import (
    get_foul_points,
    get_total_points,
    MatchAlliancePoints,
)
from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.helpers.insights_v2.timeseries.calculator import (
    TimeseriesV2Calculator,
)
from backend.common.models.event import Event
from backend.common.models.insight_v2 import (
    InsightCategory,
    InsightV2,
    MatchRecordPointContext,
    TimeseriesData,
    TimeseriesPoint,
    TimeseriesPointWithMatchRecord,
    TimeseriesSeries,
)
from backend.common.models.keys import Year


class _RecordMatch(NamedTuple):
    score: int
    match_key: str
    alliance_teams: List[str]
    post_result_time: datetime.datetime
    year: int


_EARLIEST_PLAUSIBLE_TIMESTAMP = datetime.datetime(1992, 1, 1)


class HighScoreOverTimeV2Calculator(TimeseriesV2Calculator):
    """
    Tracks the season high score for a single year. Can only be run for a
    specific year, not year=0.

    Collects all valid matches across all events, then sorts globally by
    post_result_time in _build_timeseries_data to correctly handle concurrent
    events running in the same week.

    Also produces per-district variants for events that belong to a district.
    """

    def __init__(self) -> None:
        self._all_matches: List[_RecordMatch] = []
        self._district_matches: DefaultDict[str, List[_RecordMatch]] = defaultdict(list)

    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.HIGH_SCORE_OVER_TIME

    def on_event(self, event: Event) -> None:
        district_abbrev: Optional[str] = event.event_district_abbrev
        if district_abbrev:
            canonical_district = RenamedDistricts.get_latest_code(district_abbrev)
        else:
            canonical_district = None

        for match in event.matches or []:
            t: Optional[datetime.datetime] = (
                match.post_result_time or match.actual_time or match.time
            )
            # Some 2006 matches have weird timestamps; ignore them
            if t is not None and t < _EARLIEST_PLAUSIBLE_TIMESTAMP:
                t = None
            if t is None:
                # Older matches (2013 and earlier) don't have timestamps. Estimate
                # using the event dates instead: quals on the start date, playoffs
                # on the end date. This is imprecise but good enough for ordering.
                if match.comp_level == CompLevel.QM:
                    t = event.start_date
                else:
                    t = event.end_date
            if t is None:
                continue

            red_pts = MatchAlliancePoints(
                score=int(match.alliances[AllianceColor.RED]["score"]),  # type: ignore[union-attr]
                breakdown=(
                    match.score_breakdown[AllianceColor.RED]
                    if match.score_breakdown
                    else None
                ),
                year=match.year,
            )
            blue_pts = MatchAlliancePoints(
                score=int(match.alliances[AllianceColor.BLUE]["score"]),  # type: ignore[union-attr]
                breakdown=(
                    match.score_breakdown[AllianceColor.BLUE]
                    if match.score_breakdown
                    else None
                ),
                year=match.year,
            )

            red_clean = get_total_points(red_pts) - get_foul_points(red_pts)
            blue_clean = get_total_points(blue_pts) - get_foul_points(blue_pts)

            if red_clean < 0 and blue_clean < 0:
                continue

            if red_clean >= blue_clean:
                high_color = AllianceColor.RED
                high_score = red_clean
            else:
                high_color = AllianceColor.BLUE
                high_score = blue_clean

            record = _RecordMatch(
                score=high_score,
                match_key=match.key_name,  # type: ignore[union-attr]
                alliance_teams=list(match.alliances[high_color]["teams"]),  # type: ignore[union-attr]
                post_result_time=t,
                year=event.year,
            )
            self._all_matches.append(record)
            if canonical_district:
                self._district_matches[canonical_district].append(record)

    def _build_timeseries_data(self) -> TimeseriesData:
        return self._build_from_matches(self._all_matches)

    def _build_from_matches(self, matches: List[_RecordMatch]) -> TimeseriesData:
        if not matches:
            return TimeseriesData(
                series=[],
                x_type="year",
                x_label="Year",
                y_label="Score",
                point_context_type="match_record",
            )

        current_record = -1
        record_matches: List[_RecordMatch] = []
        for m in sorted(matches, key=lambda m: m.post_result_time):
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
            series=[TimeseriesSeries(label="District Record", points=points)],
            x_type="year",
            x_label="Year",
            y_label="Score",
            point_context_type="match_record",
        )

    def make_insights(
        self, year: Year, team_to_district: Dict[str, str]
    ) -> List[InsightV2]:
        global_data = self._build_from_matches(self._all_matches)
        insights: List[InsightV2] = []

        if global_data["series"] and any(s["points"] for s in global_data["series"]):
            global_series = global_data["series"][0]
            global_data["series"] = [
                TimeseriesSeries(label="World Record", points=global_series["points"])
            ]
            name = self.insight_name
            insights.append(
                InsightV2(
                    id=InsightV2.render_key_name(
                        year, InsightCategory.TIMESERIES, name.name
                    ),
                    name=name.name,
                    display_name=name.display_name,
                    year=year,
                    category=InsightCategory.TIMESERIES,
                    data_json=global_data,
                )
            )

        for district_abbrev, matches in sorted(self._district_matches.items()):
            data = self._build_from_matches(matches)
            if not data["series"] or not any(s["points"] for s in data["series"]):
                continue
            name = self.insight_name
            insights.append(
                InsightV2(
                    id=InsightV2.render_key_name(
                        year, InsightCategory.TIMESERIES, name.name, district_abbrev
                    ),
                    name=name.name,
                    display_name=name.display_name,
                    year=year,
                    category=InsightCategory.TIMESERIES,
                    district_abbreviation=district_abbrev,
                    data_json=data,
                )
            )

        return insights
