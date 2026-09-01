from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, DefaultDict, Dict, List, Optional, Sequence, Tuple

from backend.common.consts.comp_level import CompLevel
from backend.common.game_specific.base import SuccessRateCounter
from backend.common.game_specific.registry import get_game
from backend.common.helpers.insights_v2.base import InsightV2Calculator
from backend.common.helpers.insights_v2.names import InsightV2Names
from backend.common.models.event import Event
from backend.common.models.insight_v2 import (
    AverageStat,
    GameStat,
    GameStatsData,
    GameStatsScope,
    GameStatsScopeType,
    InsightCategory,
    InsightV2,
)
from backend.common.models.keys import Year
from backend.common.models.match import Match

CHAMPIONSHIP_WEEK_LABEL = "Championship"
CHAMPIONSHIP_WEEK_ORDER = 999

Tally = DefaultDict[str, Tuple[int, int]]
AvgTally = DefaultDict[str, Tuple[float, float]]


def _new_tally() -> Tally:
    return defaultdict(lambda: (0, 0))


def _new_avg_tally() -> AvgTally:
    return defaultdict(lambda: (0.0, 0.0))


def _rates(tally: Tally, counters: Sequence[SuccessRateCounter]) -> List[GameStat]:
    return [
        GameStat(
            name=counter.name,
            label=counter.label,
            count=tally[counter.name][0],
            opportunities=tally[counter.name][1],
        )
        for counter in counters
        if tally[counter.name][1] > 0
    ]


def _averages(tally: AvgTally) -> List[AverageStat]:
    return [
        AverageStat(
            name=name, label=name.replace("_", " ").title(), value=total / weight
        )
        for name, (total, weight) in tally.items()
        if weight > 0
    ]


@dataclass
class ScopeTallies:
    """Running counts for one scope, kept split the way they are reported."""

    qual: Tally = field(default_factory=_new_tally)
    playoff: Tally = field(default_factory=_new_tally)
    qual_avg: AvgTally = field(default_factory=_new_avg_tally)
    playoff_avg: AvgTally = field(default_factory=_new_avg_tally)

    def add(
        self,
        counters: Sequence[SuccessRateCounter],
        qual_matches: List[Match],
        playoff_matches: List[Match],
    ) -> None:
        for tally, matches in (
            (self.qual, qual_matches),
            (self.playoff, playoff_matches),
        ):
            for match in matches:
                for counter in counters:
                    count, opportunities = counter.measure(match)
                    running_count, running_opportunities = tally[counter.name]
                    tally[counter.name] = (
                        running_count + count,
                        running_opportunities + opportunities,
                    )

    def add_averages(
        self,
        qual_stats: Optional[Dict[str, Any]],
        playoff_stats: Optional[Dict[str, Any]],
        qual_weight: int,
        playoff_weight: int,
    ) -> None:
        for tally, stats, weight in (
            (self.qual_avg, qual_stats, qual_weight),
            (self.playoff_avg, playoff_stats, playoff_weight),
        ):
            if not stats or weight == 0:
                continue
            for name, value in stats.items():
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    continue
                total, running_weight = tally[name]
                tally[name] = (total + value * weight, running_weight + weight)

    def is_empty(self, counters: Sequence[SuccessRateCounter]) -> bool:
        return (
            not _rates(self.qual, counters)
            and not _rates(self.playoff, counters)
            and not _averages(self.qual_avg)
            and not _averages(self.playoff_avg)
        )


class GameStatsV2Calculator(InsightV2Calculator):
    """
    Computes the v2 "game_stats" insight: for every count/opportunities
    objective a season declares, how often alliances achieved it, and the
    average value of every numeric statistic the season's per-event insights
    expose (average score, average win margin, average game-piece points,
    etc.) - across the season overall, within each competition week, and at
    each individual event.

    The count/opportunities objectives come from that year's
    SeasonGameConfig.success_rate_counters(). The averages come from that
    year's SeasonGameConfig.calculate_event_insights(), reusing whichever
    plain numeric (non-list) entries it returns - this is what distinguishes
    "non-binary" averages from the count/opportunities/percentage triples and
    the `high_score` tuple that also live in that dict. Neither hook needing
    data for a season means no insight, so the registry needs no year gating.

    Emits at most one insight, named "game_stats". Only runs for a specific
    year (never year=0) and is not district-scoped.
    """

    def __init__(self) -> None:
        self._counters: Sequence[SuccessRateCounter] = []
        self._counters_year: Optional[Year] = None
        self._overall = ScopeTallies()
        self._weeks: DefaultDict[str, ScopeTallies] = defaultdict(ScopeTallies)
        self._week_order: Dict[str, int] = {}
        self._event_scopes: List[GameStatsScope] = []

    def on_event(self, event: Event) -> None:
        counters = self._counters_for(event.year)

        played = [m for m in event.matches or [] if m.has_been_played]
        if not played:
            return
        qual_matches = [m for m in played if m.comp_level == CompLevel.QM]
        playoff_matches = [m for m in played if m.comp_level != CompLevel.QM]

        # Some seasons' calculate_event_insights() only guard their
        # breakdown-derived stats against a missing score_breakdown, not the
        # raw-score-derived ones (e.g. average_score) - so a group of
        # matches with no score_breakdown at all can still come back with
        # spurious all-zero averages instead of None. Guard here instead of
        # trusting that per season.
        has_qual_breakdown = any(m.score_breakdown is not None for m in qual_matches)
        has_playoff_breakdown = any(
            m.score_breakdown is not None for m in playoff_matches
        )
        event_insights = get_game(event.year).calculate_event_insights(played)
        qual_stats = (
            event_insights.get("qual")
            if event_insights and has_qual_breakdown
            else None
        )
        playoff_stats = (
            event_insights.get("playoff")
            if event_insights and has_playoff_breakdown
            else None
        )

        week_label = event.week_str or CHAMPIONSHIP_WEEK_LABEL
        self._week_order.setdefault(
            week_label,
            event.week if event.week is not None else CHAMPIONSHIP_WEEK_ORDER,
        )

        event_tallies = ScopeTallies()
        for tallies in (self._overall, self._weeks[week_label], event_tallies):
            tallies.add(counters, qual_matches, playoff_matches)
            tallies.add_averages(
                qual_stats, playoff_stats, len(qual_matches), len(playoff_matches)
            )

        if not event_tallies.is_empty(counters):
            self._event_scopes.append(
                self._build_scope(
                    "event",
                    event.short_name or event.name,
                    event.key_name,
                    event.week,
                    event_tallies,
                )
            )

    def make_insights(
        self, year: Year, team_to_district: Dict[str, str]
    ) -> List[InsightV2]:
        counters = self._counters_for(year)
        if self._overall.is_empty(counters):
            return []

        scopes = [self._build_scope("overall", "Overall", None, None, self._overall)]
        for week_label in sorted(self._weeks, key=lambda w: self._week_order[w]):
            week = self._week_order[week_label]
            week_tallies = self._weeks[week_label]
            if week_tallies.is_empty(counters):
                continue
            scopes.append(
                self._build_scope(
                    "week",
                    week_label,
                    None,
                    None if week == CHAMPIONSHIP_WEEK_ORDER else week,
                    week_tallies,
                )
            )
        scopes += self._event_scopes

        name = InsightV2Names.GAME_STATS
        return [
            InsightV2(
                id=InsightV2.render_key_name(
                    year, InsightCategory.GAME_STATS, name.name
                ),
                name=name.name,
                display_name=name.display_name,
                year=year,
                category=InsightCategory.GAME_STATS,
                data_json=GameStatsData(scopes=scopes),
            )
        ]

    def _counters_for(self, year: Year) -> Sequence[SuccessRateCounter]:
        if self._counters_year != year:
            self._counters_year = year
            self._counters = get_game(year).success_rate_counters()
        return self._counters

    def _build_scope(
        self,
        scope_type: GameStatsScopeType,
        label: str,
        key: Optional[str],
        week: Optional[int],
        tallies: ScopeTallies,
    ) -> GameStatsScope:
        return GameStatsScope(
            scope_type=scope_type,
            label=label,
            key=key,
            week=week,
            qual=_rates(tallies.qual, self._counters),
            playoff=_rates(tallies.playoff, self._counters),
            qual_averages=_averages(tallies.qual_avg),
            playoff_averages=_averages(tallies.playoff_avg),
        )
