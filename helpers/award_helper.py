import logging

from consts.award_type import AwardType


# Prioritized sort order for certain awards
sort_order = {
    AwardType.CHAIRMANS: 0,
    AwardType.FOUNDERS: 1,
    AwardType.ENGINEERING_INSPIRATION: 2,
    AwardType.ROOKIE_ALL_STAR: 3,
    AwardType.WOODIE_FLOWERS: 4,
    AwardType.VOLUNTEER: 5,
    AwardType.DEANS_LIST: 6,
    AwardType.WINNER: 7,
    AwardType.FINALIST: 8,
}


"""
An award matches an AwardType if the award's name_str contains every string in
the the first list of the tuple and does NOT contain any string in the second
list of the tuple.
"""
AWARD_MATCHING_STRINGS = [
    (AwardType.CHAIRMANS, (["chairman"], [])),
    (AwardType.ENGINEERING_INSPIRATION, (["engineering inspiration"], [])),
    (AwardType.WINNER, (["winner", "1"], [])),
    (AwardType.WINNER, (["winner", "2"], [])),
    (AwardType.WINNER, (["winner", "3"], [])),
    (AwardType.WINNER, (["winner", "4"], [])),
    (AwardType.WINNER, (["division", "champion", "1"], ["finalist"])),
    (AwardType.WINNER, (["division", "champion", "2"], ["finalist"])),
    (AwardType.WINNER, (["division", "champion", "3"], ["finalist"])),
    (AwardType.WINNER, (["division", "champion", "4"], ["finalist"])),
    (AwardType.WINNER, (["championship", "champion", "1"], ["finalist"])),
    (AwardType.WINNER, (["championship", "champion", "2"], ["finalist"])),
    (AwardType.WINNER, (["championship", "champion", "3"], ["finalist"])),
    (AwardType.WINNER, (["championship", "champion", "4"], ["finalist"])),
    (AwardType.FINALIST, (["finalist", "1"], ["dean"])),
    (AwardType.FINALIST, (["finalist", "2"], ["dean"])),
    (AwardType.FINALIST, (["finalist", "3"], ["dean"])),
    (AwardType.FINALIST, (["finalist", "4"], ["dean"])),
    (AwardType.COOPERTITION, (["coopertition"], [])),
    (AwardType.SPORTSMANSHIP, (["sportsmanship"], [])),
    (AwardType.CREATIVITY, (["creativity"], [])),
    (AwardType.ENGINEERING_EXCELLENCE, (["engineering", "excellence"], [])),
    (AwardType.ENTREPRENEURSHIP, (["entrepreneurship"], [])),
    (AwardType.ENTREPRENEURSHIP, (["kleiner", "perkins", "caufield", "byers"], [])),
    (AwardType.EXCELLENCE_IN_DESIGN, (["excellence in design"], ["cad", "animation"])),
    (AwardType.EXCELLENCE_IN_DESIGN_CAD, (["excellence in design", "cad"], [])),
    (AwardType.EXCELLENCE_IN_DESIGN_ANIMATION, (["excellence in design", "animation"], [])),
    (AwardType.DEANS_LIST, (["dean", "list"], [])),
    (AwardType.BART_KAMEN_MEMORIAL, (["bart", "kamen", "memorial"], [])),
    (AwardType.DRIVING_TOMORROWS_TECHNOLOGY, (["driving", "tomorrow", "technology"], [])),
    (AwardType.DRIVING_TOMORROWS_TECHNOLOGY, (["delphi", "driv", "tech"], [])),
    (AwardType.GRACIOUS_PROFESSIONALISM, (["gracious professionalism"], [])),
    (AwardType.HIGHEST_ROOKIE_SEED, (["highest rookie seed"], [])),
    (AwardType.IMAGERY, (["imagery"], [])),
    (AwardType.INDUSTRIAL_DEESIGN, (["industrial design"], [])),
    (AwardType.MEDIA_AND_TECHNOLOGY, (["media", "technology"], [])),
    (AwardType.MAKE_IT_LOUD, (["make", "loud"], [])),
    (AwardType.SAFETY, (["safety"], [])),
    (AwardType.INNOVATION_IN_CONTROL, (["innovation in control"], [])),
    (AwardType.QUALITY, (["quality"], [])),
    (AwardType.ROOKIE_ALL_STAR, (["rookie", "all", "star"], [])),
    (AwardType.ROOKIE_INSPIRATION, (["rookie inspiration"], [])),
    (AwardType.SPIRIT, (["spirit"], [])),
    (AwardType.WEBSITE, (["website"], [])),
    (AwardType.WEBSITE, (["web", "site"], [])),
    (AwardType.VISUALIZATION, (["visualization"], [])),
    (AwardType.VOLUNTEER, (["volunteer"], [])),
    (AwardType.WOODIE_FLOWERS, (["woodie flowers"], [])),
    (AwardType.JUDGES, (["judge"], [])),
    (AwardType.FOUNDERS, (["founder"], [])),
    (AwardType.AUTODESK_INVENTOR, (["autodesk inventor"], [])),
    (AwardType.FUTURE_INNOVATOR, (["future innovator"], [])),
    (AwardType.RECOGNITION_OF_EXTRAORDINARY_SERVICE, (["recognition", "extraordinary", "service"], [])),
    (AwardType.OUTSTANDING_CART, (["outstanding", "cart"], [])),
    (AwardType.WSU_AIM_HIGHER, (["wayne", "state", "university", "aim", "higher"], []))
]


class AwardHelper(object):
    @classmethod
    def organizeAwards(self, award_list):
        """
        Sorts awards first by sort_order and then alphabetically by name_str
        """
        sorted_awards = sorted(award_list, key=lambda award: sort_order.get(award.award_type_enum, award.name_str))
        return sorted_awards

    @classmethod
    def parse_award_type(self, name_str):
        """
        Returns the AwardType given a name_str, or None if there are no matches.
        """
        name_str_lower = name_str.lower()
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
