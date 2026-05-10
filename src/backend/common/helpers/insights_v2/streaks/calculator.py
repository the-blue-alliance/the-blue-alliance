from abc import abstractmethod
from collections import defaultdict
from typing import Dict, List, NamedTuple

from backend.common.consts.alliance_color import AllianceColor
from backend.common.helpers.insights_v2.base import InsightV2Calculator
from backend.common.helpers.insights_v2.names import InsightV2NameEntry
from backend.common.models.insight_v2 import (
    InsightCategory,
    InsightV2,
    StreakData,
    StreakEntry,
)
from backend.common.models.keys import Year
from backend.common.models.match import Match

STREAK_TOP_N = 25


class _StreakRecord(NamedTuple):
    length: int
    start: str  # event key or year string
    end: str  # event key or year string


class StreakV2Calculator(InsightV2Calculator):
    """
    Base class for streak insights. Tracks active and all completed streaks per key.
    Subclasses call _advance_streak / _reset_streak from their own on_event, which
    may iterate at event granularity, match granularity, or any other unit.
    """

    def __init__(self) -> None:
        self._active: Dict[str, _StreakRecord] = {}
        self._completed: Dict[str, List[_StreakRecord]] = defaultdict(list)

    @property
    @abstractmethod
    def insight_name(self) -> InsightV2NameEntry: ...

    @staticmethod
    def _effective_winning_alliance(match: Match) -> str:
        """
        Returns the winning alliance for a match. For 2015, scores are used
        directly because winning_alliance returns "" for all non-finals playoff
        matches in that year regardless of the actual score.
        """
        if match.year == 2015:
            red_score = int(match.alliances[AllianceColor.RED]["score"])
            blue_score = int(match.alliances[AllianceColor.BLUE]["score"])
            if red_score > blue_score:
                return AllianceColor.RED
            elif blue_score > red_score:
                return AllianceColor.BLUE
            return ""
        return match.winning_alliance

    def _advance_streak(self, key: str, label: str) -> None:
        """Extend key's active streak. label identifies the current unit (event key, year, etc.)."""
        if key in self._active:
            rec = self._active[key]
            self._active[key] = _StreakRecord(rec.length + 1, rec.start, label)
        else:
            self._active[key] = _StreakRecord(1, label, label)

    def _reset_streak(self, key: str) -> None:
        """Break key's active streak, saving it to completed history."""
        if key in self._active:
            self._completed[key].append(self._active.pop(key))

    def _build_streak_entries(self) -> List[StreakEntry]:
        """
        Returns all StreakEntry items sorted by streak_length descending then by
        team number ascending then by start ascending. A single team may appear
        multiple times if they have multiple distinct streaks (completed or active).
        Callers are responsible for slicing to their desired top-N.
        """
        entries: List[StreakEntry] = []

        for key, completed_list in self._completed.items():
            for rec in completed_list:
                entries.append(
                    StreakEntry(
                        key=key,
                        key_type="team",
                        streak_length=rec.length,
                        start=rec.start,
                        end=rec.end,
                        is_active=False,
                    )
                )

        for key, active in self._active.items():
            entries.append(
                StreakEntry(
                    key=key,
                    key_type="team",
                    streak_length=active.length,
                    start=active.start,
                    end=active.end,
                    is_active=True,
                )
            )

        entries.sort(key=lambda e: (-e["streak_length"], int(e["key"][3:]), e["start"]))
        return entries

    def _build_district_entries(
        self,
        all_entries: List[StreakEntry],
        team_to_district: Dict[str, str],
        top_n: int = STREAK_TOP_N,
    ) -> Dict[str, List[StreakEntry]]:
        """
        Groups already-sorted entries by district, producing a top_n list per district.
        Because all_entries is already sorted, each district sub-list is also sorted.
        """
        district_entries: Dict[str, List[StreakEntry]] = defaultdict(list)
        for entry in all_entries:
            if district := team_to_district.get(entry["key"]):
                bucket = district_entries[district]
                if len(bucket) < top_n:
                    bucket.append(entry)
        return dict(district_entries)

    def make_insights(
        self, year: Year, team_to_district: Dict[str, str]
    ) -> List[InsightV2]:
        # Build all entries sorted; slice to top-N for global, but pass the full
        # list to district grouping so each district gets its own independent top-N.
        all_entries = self._build_streak_entries()
        if not all_entries:
            return []

        name = self.insight_name
        insights: List[InsightV2] = [
            InsightV2(
                id=InsightV2.render_key_name(year, InsightCategory.STREAK, name.name),
                name=name.name,
                display_name=name.display_name,
                year=year,
                category=InsightCategory.STREAK,
                data_json=StreakData(entries=all_entries[:STREAK_TOP_N]),
            )
        ]

        for district_abbrev, d_entries in sorted(
            self._build_district_entries(all_entries, team_to_district).items()
        ):
            insights.append(
                InsightV2(
                    id=InsightV2.render_key_name(
                        year, InsightCategory.STREAK, name.name, district_abbrev
                    ),
                    name=name.name,
                    display_name=name.display_name,
                    year=year,
                    category=InsightCategory.STREAK,
                    district_abbreviation=district_abbrev,
                    data_json=StreakData(entries=d_entries),
                )
            )

        return insights
