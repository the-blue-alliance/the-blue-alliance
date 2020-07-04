import re
from typing import Dict, List, Tuple

from backend.common.consts.comp_level import COMP_LEVELS, CompLevel
from backend.common.models.match import Match


class MatchHelper(object):

    """
    Helper to put matches into sub-dictionaries for the way we render match tables
    Allows us to sort matches by key name.
    Note: Matches within a comp_level (qual, qf, sf, f, etc.) will be in order,
    but the comp levels themselves may not be in order. Doesn't matter because
    XXX_match_table.html checks for comp_level when rendering the page
    """

    @classmethod
    def natural_sort_matches(cls, matches: List[Match]) -> List[Match]:
        def convert(text):
            return int(text) if text.isdigit() else text.lower()

        def alphanum_key(match):
            return [convert(c) for c in re.split("([0-9]+)", str(match.key_name))]

        return sorted(matches, key=alphanum_key)

    @classmethod
    def play_order_sort_matches(
        cls, matches: List[Match], reverse: bool = False
    ) -> List[Match]:
        return sorted(matches, key=lambda m: m.play_order, reverse=reverse)

    @classmethod
    def organizeMatches(
        cls, match_list: List[Match]
    ) -> Tuple[int, Dict[CompLevel, List[Match]]]:
        match_list = cls.natural_sort_matches(match_list)
        matches = dict([(comp_level, list()) for comp_level in COMP_LEVELS])
        count = len(match_list)
        while len(match_list) > 0:
            match = match_list.pop(0)
            matches[match.comp_level].append(match)

        return count, matches

    @classmethod
    def recentMatches(cls, matches: List[Match], num: int = 3) -> List[Match]:
        matches = list(filter(lambda x: x.has_been_played, matches))
        matches = cls.play_order_sort_matches(matches)
        return matches[-num:]

    @classmethod
    def upcomingMatches(cls, matches: List[Match], num: int = 3) -> List[Match]:
        matches = cls.play_order_sort_matches(matches)

        last_played_match_index = None
        for i, match in enumerate(reversed(matches)):
            if match.has_been_played:
                last_played_match_index = len(matches) - i
                break

        upcoming_matches = []
        for i, match in enumerate(matches[last_played_match_index:]):
            if i == num:
                break
            if not match.has_been_played:
                upcoming_matches.append(match)
        return upcoming_matches
