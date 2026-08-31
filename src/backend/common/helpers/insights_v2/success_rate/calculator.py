from collections import defaultdict
from dataclasses import dataclass, field
from typing import DefaultDict, Dict, List, Optional, Sequence, Tuple

from backend.common.consts.comp_level import CompLevel
from backend.common.game_specific.base import SuccessRateCounter
from backend.common.game_specific.registry import get_game
from backend.common.helpers.insights_v2.base import InsightV2Calculator
from backend.common.helpers.insights_v2.names import InsightV2Names
from backend.common.models.event import Event
from backend.common.models.insight_v2 import (
    InsightCategory,
    InsightV2,
    SuccessRate,
    SuccessRateData,
    SuccessRateScope,
    SuccessRateScopeType,
)
from backend.common.models.keys import Year
from backend.common.models.match import Match

CHAMPIONSHIP_WEEK_LABEL = "Championship"
CHAMPIONSHIP_WEEK_ORDER = 999

Tally = DefaultDict[str, Tuple[int, int]]


def _new_tally() -> Tally:
    return defaultdict(lambda: (0, 0))


def _rates(tally: Tally, counters: Sequence[SuccessRateCounter]) -> List[SuccessRate]:
    return [
        SuccessRate(
            name=counter.name,
            label=counter.label,
            count=tally[counter.name][0],
            opportunities=tally[counter.name][1],
        )
        for counter in counters
        if tally[counter.name][1] > 0
    ]


@dataclass
class ScopeTallies:
    """Running counts for one scope, kept split the way they are reported."""

    qual: Tally = field(default_factory=_new_tally)
    playoff: Tally = field(default_factory=_new_tally)

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

    def is_empty(self, counters: Sequence[SuccessRateCounter]) -> bool:
        return not _rates(self.qual, counters) and not _rates(self.playoff, counters)


class SuccessRateV2Calculator(InsightV2Calculator):
    """
    Computes the v2 "success_rate" insight: for every count/opportunities
    objective a season declares, how often alliances achieved it - across the
    season overall, within each competition week, and at each individual event.

    The objectives themselves come from that year's
    SeasonGameConfig.success_rate_counters(); this calculator only handles the
    year-agnostic plumbing of bucketing matches into scopes and assembling the
    wire format. A season declaring no counters (pre-2016, and 2021) yields no
    insight, so the registry needs no year gating.

    Emits at most one insight, named "success_rates". Only runs for a specific
    year (never year=0) and is not district-scoped.
    """

    def __init__(self) -> None:
        self._counters: Sequence[SuccessRateCounter] = []
        self._counters_year: Optional[Year] = None
        self._overall = ScopeTallies()
        self._weeks: DefaultDict[str, ScopeTallies] = defaultdict(ScopeTallies)
        self._week_order: Dict[str, int] = {}
        self._event_scopes: List[SuccessRateScope] = []

    def on_event(self, event: Event) -> None:
        counters = self._counters_for(event.year)
        if not counters:
            return

        played = [m for m in event.matches or [] if m.has_been_played]
        qual_matches = [m for m in played if m.comp_level == CompLevel.QM]
        playoff_matches = [m for m in played if m.comp_level != CompLevel.QM]
        if not played:
            return

        week_label = event.week_str or CHAMPIONSHIP_WEEK_LABEL
        self._week_order.setdefault(
            week_label,
            event.week if event.week is not None else CHAMPIONSHIP_WEEK_ORDER,
        )

        event_tallies = ScopeTallies()
        for tallies in (self._overall, self._weeks[week_label], event_tallies):
            tallies.add(counters, qual_matches, playoff_matches)

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
        if not counters or self._overall.is_empty(counters):
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

        name = InsightV2Names.SUCCESS_RATES
        return [
            InsightV2(
                id=InsightV2.render_key_name(
                    year, InsightCategory.SUCCESS_RATE, name.name
                ),
                name=name.name,
                display_name=name.display_name,
                year=year,
                category=InsightCategory.SUCCESS_RATE,
                data_json=SuccessRateData(scopes=scopes),
            )
        ]

    def _counters_for(self, year: Year) -> Sequence[SuccessRateCounter]:
        if self._counters_year != year:
            self._counters_year = year
            self._counters = get_game(year).success_rate_counters()
        return self._counters

    def _build_scope(
        self,
        scope_type: SuccessRateScopeType,
        label: str,
        key: Optional[str],
        week: Optional[int],
        tallies: ScopeTallies,
    ) -> SuccessRateScope:
        return SuccessRateScope(
            scope_type=scope_type,
            label=label,
            key=key,
            week=week,
            qual=_rates(tallies.qual, self._counters),
            playoff=_rates(tallies.playoff, self._counters),
        )
