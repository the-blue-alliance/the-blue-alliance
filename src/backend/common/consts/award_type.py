import enum
from typing import Dict, Set

from backend.common.consts.event_type import EventType


@enum.unique
class AwardType(enum.IntEnum):
    """
    An award type defines a logical type of award that an award falls into.
    These types are the same across both years and competitions within a year.
    In other words, an industrial design award from 2013casj and
    2010cmp will be of award type AwardType.INDUSTRIAL_DESIGN.

    An award type must be enumerated for every type of award ever awarded.
    ONCE A TYPE IS ENUMERATED, IT MUST NOT BE CHANGED.

    Award types don't care about what type of event (Regional, District,
    District Championship, Championship Division, Championship Finals, etc.)
    the award is from. In other words, RCA and CCA are of the same award type.
    """

    CHAIRMANS = 0
    WINNER = 1
    FINALIST = 2

    WOODIE_FLOWERS = 3
    DEANS_LIST = 4
    VOLUNTEER = 5
    FOUNDERS = 6
    BART_KAMEN_MEMORIAL = 7
    MAKE_IT_LOUD = 8

    ENGINEERING_INSPIRATION = 9
    ROOKIE_ALL_STAR = 10
    GRACIOUS_PROFESSIONALISM = 11
    COOPERTITION = 12
    JUDGES = 13
    HIGHEST_ROOKIE_SEED = 14
    ROOKIE_INSPIRATION = 15
    INDUSTRIAL_DESIGN = 16
    QUALITY = 17
    SAFETY = 18
    SPORTSMANSHIP = 19
    CREATIVITY = 20
    ENGINEERING_EXCELLENCE = 21
    ENTREPRENEURSHIP = 22
    EXCELLENCE_IN_DESIGN = 23
    EXCELLENCE_IN_DESIGN_CAD = 24
    EXCELLENCE_IN_DESIGN_ANIMATION = 25
    DRIVING_TOMORROWS_TECHNOLOGY = 26
    IMAGERY = 27
    MEDIA_AND_TECHNOLOGY = 28
    INNOVATION_IN_CONTROL = 29
    SPIRIT = 30
    WEBSITE = 31
    VISUALIZATION = 32
    AUTODESK_INVENTOR = 33
    FUTURE_INNOVATOR = 34
    RECOGNITION_OF_EXTRAORDINARY_SERVICE = 35
    OUTSTANDING_CART = 36
    WSU_AIM_HIGHER = 37
    LEADERSHIP_IN_CONTROL = 38
    NUM_1_SEED = 39
    INCREDIBLE_PLAY = 40
    PEOPLES_CHOICE_ANIMATION = 41
    VISUALIZATION_RISING_STAR = 42
    BEST_OFFENSIVE_ROUND = 43
    BEST_PLAY_OF_THE_DAY = 44
    FEATHERWEIGHT_IN_THE_FINALS = 45
    MOST_PHOTOGENIC = 46
    OUTSTANDING_DEFENSE = 47
    POWER_TO_SIMPLIFY = 48
    AGAINST_ALL_ODDS = 49
    RISING_STAR = 50
    CHAIRMANS_HONORABLE_MENTION = 51
    CONTENT_COMMUNICATION_HONORABLE_MENTION = 52
    TECHNICAL_EXECUTION_HONORABLE_MENTION = 53
    REALIZATION = 54
    REALIZATION_HONORABLE_MENTION = 55
    DESIGN_YOUR_FUTURE = 56
    DESIGN_YOUR_FUTURE_HONORABLE_MENTION = 57
    SPECIAL_RECOGNITION_CHARACTER_ANIMATION = 58
    HIGH_SCORE = 59
    TEACHER_PIONEER = 60
    BEST_CRAFTSMANSHIP = 61
    BEST_DEFENSIVE_MATCH = 62
    PLAY_OF_THE_DAY = 63
    PROGRAMMING = 64
    PROFESSIONALISM = 65
    GOLDEN_CORNDOG = 66
    MOST_IMPROVED_TEAM = 67
    WILDCARD = 68
    CHAIRMANS_FINALIST = 69
    OTHER = 70
    AUTONOMOUS = 71


BLUE_BANNER_AWARDS: Set[AwardType] = {
    AwardType.CHAIRMANS,
    AwardType.CHAIRMANS_FINALIST,
    AwardType.WINNER,
    AwardType.WOODIE_FLOWERS,
}


INDIVIDUAL_AWARDS: Set[AwardType] = {
    AwardType.WOODIE_FLOWERS,
    AwardType.DEANS_LIST,
    AwardType.VOLUNTEER,
    AwardType.FOUNDERS,
    AwardType.BART_KAMEN_MEMORIAL,
    AwardType.MAKE_IT_LOUD,
}


# awards not used in the district point model
NON_JUDGED_NON_TEAM_AWARDS: Set[AwardType] = {
    AwardType.HIGHEST_ROOKIE_SEED,
    AwardType.WOODIE_FLOWERS,
    AwardType.DEANS_LIST,
    AwardType.VOLUNTEER,
    AwardType.WINNER,
    AwardType.FINALIST,
    AwardType.WILDCARD,
}


NORMALIZED_NAMES = {
    AwardType.CHAIRMANS: {None: "Chairman's Award"},
    AwardType.CHAIRMANS_FINALIST: {None: "Chairman's Award Finalist"},
    AwardType.WINNER: {None: "Winner"},
    AwardType.WOODIE_FLOWERS: {
        None: "Woodie Flowers Finalist Award",
        EventType.CMP_FINALS: "Woodie Flowers Award",
    },
}


# Only searchable awards. Obscure & old awards not listed
SEARCHABLE: Dict[AwardType, str] = {
    AwardType.CHAIRMANS: "Chairman's",
    AwardType.CHAIRMANS_FINALIST: "Chairman's Finalist",
    AwardType.ENGINEERING_INSPIRATION: "Engineering Inspiration",
    AwardType.COOPERTITION: "Coopertition",
    AwardType.CREATIVITY: "Creativity",
    AwardType.ENGINEERING_EXCELLENCE: "Engineering Excellence",
    AwardType.ENTREPRENEURSHIP: "Entrepreneurship",
    AwardType.DEANS_LIST: "Dean's List",
    AwardType.BART_KAMEN_MEMORIAL: "Bart Kamen Memorial",
    AwardType.GRACIOUS_PROFESSIONALISM: "Gracious Professionalism",
    AwardType.HIGHEST_ROOKIE_SEED: "Highest Rookie Seed",
    AwardType.IMAGERY: "Imagery",
    AwardType.INDUSTRIAL_DESIGN: "Industrial Design",
    AwardType.SAFETY: "Safety",
    AwardType.INNOVATION_IN_CONTROL: "Innovation in Control",
    AwardType.QUALITY: "Quality",
    AwardType.ROOKIE_ALL_STAR: "Rookie All Star",
    AwardType.ROOKIE_INSPIRATION: "Rookie Inspiration",
    AwardType.SPIRIT: "Spirit",
    AwardType.VOLUNTEER: "Volunteer",
    AwardType.WOODIE_FLOWERS: "Woodie Flowers",
    AwardType.JUDGES: "Judges'",
}
