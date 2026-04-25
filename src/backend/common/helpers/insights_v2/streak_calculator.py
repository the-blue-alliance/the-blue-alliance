from abc import abstractmethod
from collections import defaultdict
from typing import Dict, List, NamedTuple, Set

from backend.common.helpers.insights_v2.compute import InsightV2Calculator
from backend.common.models.insight_v2 import InsightV2, StreakEntry
from backend.common.models.keys import Year

STREAK_TOP_N = 25


class _StreakRecord(NamedTuple):
    length: int
    start: str  # event key or year string
    end: str  # event key or year string


class StreakV2Calculator(InsightV2Calculator):
    """
    Base class for streak insights. Tracks active and all-time-best streaks per key.
    Subclasses call _advance_streak / _reset_streak from their own on_event, which
    may iterate at event granularity, match granularity, or any other unit.
    """

    def __init__(self) -> None:
        self._active: Dict[str, _StreakRecord] = {}
        self._best: Dict[str, _StreakRecord] = {}

    @property
    def team_keys(self) -> Set[str]:
        return set(self._best.keys())

    def _advance_streak(self, key: str, label: str) -> None:
        """Extend key's active streak. label identifies the current unit (event key, year, etc.)."""
        if key in self._active:
            rec = self._active[key]
            self._active[key] = _StreakRecord(rec.length + 1, rec.start, label)
        else:
            self._active[key] = _StreakRecord(1, label, label)

        active = self._active[key]
        if key not in self._best or active.length > self._best[key].length:
            self._best[key] = active

    def _reset_streak(self, key: str) -> None:
        """Break key's active streak."""
        self._active.pop(key, None)

    def _build_streak_entries(self, top_n: int = STREAK_TOP_N) -> List[StreakEntry]:
        """
        Returns up to top_n StreakEntry items, sorted by streak_length descending
        then by team number ascending. Flushes still-active streaks first.
        """
        for key, active in self._active.items():
            if key not in self._best or active.length > self._best[key].length:
                self._best[key] = active

        entries: List[StreakEntry] = []
        for key, best in self._best.items():
            active = self._active.get(key)
            is_active = (
                active is not None
                and active.length == best.length
                and active.start == best.start
            )
            entries.append(
                StreakEntry(
                    key=key,
                    key_type="team",
                    streak_length=best.length,
                    start=best.start,
                    end=best.end,
                    is_active=is_active,
                )
            )

        entries.sort(key=lambda e: (-e["streak_length"], int(e["key"][3:])))
        return entries[:top_n]

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

    @abstractmethod
    def make_insights(
        self, year: Year, team_to_district: Dict[str, str]
    ) -> List[InsightV2]: ...
