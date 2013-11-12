import logging
from consts.award_type import AwardType
from models.award import Award


# Prioritized sort order for certain awards
sortOrder = [
    AwardType.CHAIRMANS,
    AwardType.FOUNDERS,
    AwardType.ENGINEERING_INSPIRATION,
    AwardType.ROOKIE_ALL_STAR,
    AwardType.WOODIE_FLOWERS,
    AwardType.VOLUNTEER,
    AwardType.DEANS_LIST,
    AwardType.WINNER,
    AwardType.FINALIST,
]


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
    (AwardType.EXCELLENCE_IN_DESIGN, (["excellence in design"], ["cad", "animation"])),
    (AwardType.EXCELLENCE_IN_DESIGN_CAD, (["excellence in design", "cad"], [])),
    (AwardType.EXCELLENCE_IN_DESIGN_ANIMATION, (["excellence in design", "animation"], [])),
    (AwardType.DEANS_LIST, (["dean", "list"], [])),
    (AwardType.BART_KAMEN_MEMORIAL, (["bart", "kamen", "memorial"], [])),
    (AwardType.DRIVING_TOMORROWS_TECHNOLOGY, (["driving", "tomorrow", "technology"], [])),
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
    (AwardType.VISUALIZATION, (["visualization"], [])),
    (AwardType.VOLUNTEER, (["volunteer"], [])),
    (AwardType.WOODIE_FLOWERS, (["woodie flowers"], [])),
    (AwardType.JUDGES, (["judge"], [])),
    (AwardType.FOUNDERS, (["founder"], [])),
    (AwardType.AUTODESK_INVENTOR, (["autodesk inventor"], [])),
    (AwardType.FUTURE_INNOVATOR, (["future innovator"], []))
]


class AwardHelper(object):
    """
    Helper to prepare awards for being used in a template
    awards['list'] is sorted by sortOrder and then the rest
    in alphabetical order by name_str
    """

    @classmethod
    def organizeAwards(self, award_list):
        awards = dict([(award.award_type_enum, award) for award in award_list])
        awards_set = set(awards)

        awards['list'] = list()
        defined_set = set()
        for item in sortOrder:
            if item in awards:
                awards['list'].append(awards[item])
                defined_set.add(item)

        difference = awards_set.difference(defined_set)
        remaining_awards = []
        for item in difference:
            remaining_awards.append(awards[item])
        remaining_awards = sorted(remaining_awards, key=lambda award: award.name_str)

        awards['list'] += remaining_awards
        return awards

    @classmethod
    def split_awards(self, awards):
        """
        For each award, uses recipient_list to add a recipient_dict property,
        where the key is the team_number and the value is a list of awardees.
        """
        for award in awards:
            recipient_dict = {}
            for recipient in award.recipient_list:
                team_number = recipient['team_number']
                awardee = recipient['awardee']
                if team_number in recipient_dict:
                    recipient_dict[team_number].append(awardee)
                else:
                    recipient_dict[team_number] = [awardee]
            award.recipient_dict = recipient_dict
        return awards

    @classmethod
<<<<<<< HEAD
    def getAwards(self, keys, year=None):
        awards = []
        for key in keys:
            if year == None:
                awards += Award.query(Award.name == key)
            else:
                awards += Award.query(Award.name == key, Award.year == year)
        return awards

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
