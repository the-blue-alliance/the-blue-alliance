class AwardType(object):
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
    INDUSTRIAL_DEESIGN = 16
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

    BLUE_BANNER_AWARDS = {CHAIRMANS, WINNER}
    INDIVIDUAL_AWARDS = {WOODIE_FLOWERS, DEANS_LIST, VOLUNTEER, FOUNDERS,
                         BART_KAMEN_MEMORIAL, MAKE_IT_LOUD}
