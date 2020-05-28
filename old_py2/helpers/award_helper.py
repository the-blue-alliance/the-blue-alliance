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
    (AwardType.CHAIRMANS, (["chairman"], ["hon", "finalist"])),
    (AwardType.CHAIRMANS_HONORABLE_MENTION, (["chairman", "hon", "mention"], [])),
    (AwardType.CHAIRMANS_FINALIST, (["chairman", "finalist"], ["hon", "mention"])),
    (AwardType.ENGINEERING_INSPIRATION, (["engineering inspiration"], [])),
    (AwardType.WINNER, (["regional winner"], [])),
    (AwardType.WINNER, (["championship winner"], [])),
    (AwardType.WINNER, (["championship champion"], [])),
    (AwardType.WINNER, (["division champion"], [])),
    (AwardType.WINNER, (["championship subdivision winner"], [])),
    (AwardType.WINNER, (["district event winner"], [])),
    (AwardType.WINNER, (["winner", "1"], [])),
    (AwardType.WINNER, (["winner", "2"], [])),
    (AwardType.WINNER, (["winner", "3"], ["3d"])),
    (AwardType.WINNER, (["winner", "4"], [])),
    (AwardType.WINNER, (["division", "champion", "1"], ["finalist"])),
    (AwardType.WINNER, (["division", "champion", "2"], ["finalist"])),
    (AwardType.WINNER, (["division", "champion", "3"], ["finalist", "3d"])),
    (AwardType.WINNER, (["division", "champion", "4"], ["finalist"])),
    (AwardType.WINNER, (["championship", "champion", "1"], ["finalist"])),
    (AwardType.WINNER, (["championship", "champion", "2"], ["finalist"])),
    (AwardType.WINNER, (["championship", "champion", "3"], ["finalist", "3d"])),
    (AwardType.WINNER, (["championship", "champion", "4"], ["finalist"])),
    (AwardType.FINALIST, (["regional finalist"], ["dean"])),
    (AwardType.FINALIST, (["championship finalist"], ["dean"])),
    (AwardType.FINALIST, (["division finalist"], ["dean"])),
    (AwardType.FINALIST, (["district event finalist"], [])),
    (AwardType.FINALIST, (["finalist", "1"], ["dean"])),
    (AwardType.FINALIST, (["finalist", "2"], ["dean"])),
    (AwardType.FINALIST, (["finalist", "3"], ["dean", "3d"])),
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
    (AwardType.INDUSTRIAL_DESIGN, (["industrial design"], [])),
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
    (AwardType.VISUALIZATION, (["visualization"], ["rising"])),
    (AwardType.VOLUNTEER, (["volunteer"], [])),
    (AwardType.WOODIE_FLOWERS, (["woodie flowers"], [])),
    (AwardType.JUDGES, (["judge"], [])),
    (AwardType.FOUNDERS, (["founder"], [])),
    (AwardType.AUTODESK_INVENTOR, (["autodesk inventor"], [])),
    (AwardType.FUTURE_INNOVATOR, (["future innovator"], [])),
    (AwardType.RECOGNITION_OF_EXTRAORDINARY_SERVICE, (["recognition", "extraordinary", "service"], [])),
    (AwardType.OUTSTANDING_CART, (["outstanding", "cart"], [])),
    (AwardType.WSU_AIM_HIGHER, (["wayne", "state", "university", "aim", "higher"], [])),
    (AwardType.LEADERSHIP_IN_CONTROL, (["leadership", "control"], [])),
    (AwardType.NUM_1_SEED, (["#1", "seed"], [])),
    (AwardType.INCREDIBLE_PLAY, (["incredible", "play"], [])),
    (AwardType.PEOPLES_CHOICE_ANIMATION, (["people", "choice", "animation"], [])),
    (AwardType.VISUALIZATION_RISING_STAR, (["visualization", "rising"], [])),
    (AwardType.BEST_OFFENSIVE_ROUND, (["best", "offensive", "round"], [])),
    (AwardType.BEST_PLAY_OF_THE_DAY, (["best", "play"], [])),
    (AwardType.FEATHERWEIGHT_IN_THE_FINALS, (["featherweight", "finals"], [])),
    (AwardType.MOST_PHOTOGENIC, (["photogenic"], [])),
    (AwardType.OUTSTANDING_DEFENSE, (["outstanding defense"], [])),
    (AwardType.POWER_TO_SIMPLIFY, (["power to simplify"], [])),
    (AwardType.AGAINST_ALL_ODDS, (["against all odds"], [])),
    (AwardType.RISING_STAR, (["autodesk", "rising star"], ["hon", "mention"])),
    (AwardType.CONTENT_COMMUNICATION_HONORABLE_MENTION, (["content communication", "hon", "mention"], [])),
    (AwardType.TECHNICAL_EXECUTION_HONORABLE_MENTION, (["technical execution", "hon", "mention"], [])),
    (AwardType.REALIZATION, (["autodesk", "realization"], ["hon", "mention"])),
    (AwardType.REALIZATION_HONORABLE_MENTION, (["autodesk", "realization", "hon", "mention"], [])),
    (AwardType.DESIGN_YOUR_FUTURE, (["autodesk", "design your future"], ["hon", "mention"])),
    (AwardType.DESIGN_YOUR_FUTURE_HONORABLE_MENTION, (["autodesk", "design your future", "hon", "mention"], [])),
    (AwardType.SPECIAL_RECOGNITION_CHARACTER_ANIMATION, (["autodesk", "special recognition", "character animation"], ["hon", "mention"])),
    (AwardType.HIGH_SCORE, (["high score"], [])),
    (AwardType.TEACHER_PIONEER, (["teacher pioneer"], [])),
    (AwardType.BEST_CRAFTSMANSHIP, (["best craftsmanship"], [])),
    (AwardType.BEST_DEFENSIVE_MATCH, (["best defensive match"], [])),
    (AwardType.PLAY_OF_THE_DAY, (["play of the day"], [])),
    (AwardType.PROGRAMMING, (["programming"], [])),
    (AwardType.PROFESSIONALISM, (["professionalism"], ["gracious"])),
    (AwardType.GOLDEN_CORNDOG, (["golden corndog"], [])),
    (AwardType.MOST_IMPROVED_TEAM, (["most improved team"], [])),
    (AwardType.WILDCARD, (["wildcard"], [])),
    (AwardType.AUTONOMOUS, (["autonomous"], [])),
    (AwardType.OTHER, (["other", "offseason award", "offseason event award"], [])),
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

        # to match awards without the "#1", "#2", etc suffix
        if name_str_lower == 'winner':
            return AwardType.WINNER
        elif name_str_lower == 'finalist':
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
