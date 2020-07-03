import logging
from typing import List, Optional

from backend.common.consts.award_matching_strings import AWARD_MATCHING_STRINGS
from backend.common.consts.award_type import AwardType, SORT_ORDER as AWARD_SORT_ORDER
from backend.common.models.award import Award


class AwardHelper(object):
    @classmethod
    def organizeAwards(cls, award_list: List[Award]) -> List[Award]:
        """
        Sorts awards first by sort_order and then alphabetically by name_str
        """
        max_sort_type = max(AWARD_SORT_ORDER.values()) + 1
        sorted_awards = sorted(
            award_list,
            key=lambda award: (
                AWARD_SORT_ORDER.get(award.award_type_enum, max_sort_type),
                award.name_str,
            ),
        )
        return sorted_awards

    @classmethod
    def parse_award_type(cls, name_str: str) -> Optional[AwardType]:
        """
        Returns the AwardType given a name_str, or None if there are no matches.
        """
        name_str_lower = name_str.lower()

        # to match awards without the "#1", "#2", etc suffix
        if name_str_lower == "winner":
            return AwardType.WINNER
        elif name_str_lower == "finalist":
            return AwardType.FINALIST

        for type_enum, (yes_strings, no_strings) in AWARD_MATCHING_STRINGS:
            for string in yes_strings:
                if string not in name_str_lower:
                    break
            else:
                for string in no_strings:
                    if string in name_str_lower:
                        break
                else:
                    # found a match
                    return type_enum

        # no matches
        logging.warning("Found an award without an associated type: " + name_str)
        return None
