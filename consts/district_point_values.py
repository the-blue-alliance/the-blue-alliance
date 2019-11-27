from consts.award_type import AwardType


class DistrictPointValues(object):
    """
    A class that contains various district point constants over the years:
    Documents containing point systems:
     - 2016: same as 2015
     - 2015: http://www.firstinspires.org/sites/default/files/uploads/resource_library/frc/game-and-season-info/archive/2015/AdminManual20150407.pdf
     - 2014: http://www.firstinmichigan.org/FRC_2014/District_Standard_Points_Ranking_System.pdf
     - 2013: http://www.firstinmichigan.org/FRC_2013/2013_Rules_Supplement.pdf
     - 2012: http://www.firstinmichigan.org/FRC_2012/2012_Rules_Supplement.pdf
     - 2011: http://www.firstinmichigan.org/FRC_2011/2011_Rules_Supplement.pdf
     - 2010: http://www.firstinmichigan.org/FRC_2010/2010_Update_3.pdf
     - 2009: https://www.chiefdelphi.com/forums/showpost.php?p=759453&postcount=67
    """

    STANDARD_MULTIPLIER = 1

    # Since 2014, points earned at District CMP has 3x bonus
    DISTRICT_CMP_MULIPLIER_DEFAULT = 3
    DISTRICT_CMP_MULTIPLIER = {
        2013: 1,
        2012: 1,
        2011: 1,
        2010: 1,
        2009: 1
    }

    # In years prior to 2015, teams get points for a win/tie in a qualification match
    MATCH_WIN = 2
    MATCH_TIE = 1

    # Used to determine alliance selection points
    # Captain/First pick get 17-alliance number, second pick gets 17 - draft order
    ALLIANCE_MAX_DEFAULT = 17

    # In 2009 - 2013 (except 2010), second pick teams got fewer elim round advancement points as captain/pick 1
    # TODO many of these events don't have alliance selection data, so we can't factor this in
    ELIM_SECOND_PICK_MULTIPLIER_DEFAULT = 1
    ELIM_SECOND_PICK_MULTIPLIER = {
        2013: 0.8,
        2012: 0.8,
        2011: 0.8,
        2009: 0.8
    }

    # Used to determine elim/playoff points.
    # Teams on each round's winning alliance gets points per match won
    # For the 2015 game, these are awarded for participating in a qf/sf match, since there were no wins
    QF_WIN_DEFAULT = 5
    QF_WIN = {
        2015: 5.0
    }

    SF_WIN_DEFAULT = 5
    SF_WIN = {
        2015: 3.3,
    }

    F_WIN_DEFAULT = 5
    F_WIN = {
        2015: 5.0
    }

    # Chairman's Award
    CHAIRMANS_DEFAULT = 10
    CHAIRMANS = {
        2013: 0,
        2012: 0,
        2011: 0,
        2009: 0
    }

    # Engineering Inspiration and Rookie All-Star
    EI_AND_RAS_DEFAULT = 8
    OTHER_AWARD_DEFAULT = 5

    # Pre-2014 Awards, all worth either 5 or 2 points
    LEGACY_5_PT_AWARDS = {
        2013: [AwardType.INDUSTRIAL_DESIGN, AwardType.QUALITY, AwardType.ENGINEERING_EXCELLENCE, AwardType.INNOVATION_IN_CONTROL, AwardType.CREATIVITY],
        2012: [AwardType.INDUSTRIAL_DESIGN, AwardType.QUALITY, AwardType.ENGINEERING_EXCELLENCE, AwardType.INNOVATION_IN_CONTROL, AwardType.CREATIVITY, AwardType.ENTREPRENEURSHIP, AwardType.COOPERTITION],
        2011: [AwardType.INDUSTRIAL_DESIGN, AwardType.QUALITY, AwardType.ENGINEERING_EXCELLENCE, AwardType.INNOVATION_IN_CONTROL, AwardType.CREATIVITY, AwardType.ENTREPRENEURSHIP, AwardType.COOPERTITION, AwardType.EXCELLENCE_IN_DESIGN],
        2010: [AwardType.INDUSTRIAL_DESIGN, AwardType.QUALITY, AwardType.ENGINEERING_EXCELLENCE, AwardType.INNOVATION_IN_CONTROL, AwardType.CREATIVITY, AwardType.ROOKIE_ALL_STAR, AwardType.ENGINEERING_INSPIRATION, AwardType.ENTREPRENEURSHIP, AwardType.COOPERTITION],
        2009: [AwardType.INDUSTRIAL_DESIGN, AwardType.QUALITY, AwardType.DRIVING_TOMORROWS_TECHNOLOGY, AwardType.INNOVATION_IN_CONTROL, AwardType.CREATIVITY]
    }

    LEGACY_2_PT_AWARDS = {
        2013: [AwardType.SPIRIT, AwardType.GRACIOUS_PROFESSIONALISM, AwardType.IMAGERY, AwardType.HIGHEST_ROOKIE_SEED, AwardType.SAFETY, AwardType.JUDGES, AwardType.ROOKIE_INSPIRATION],
        2012: [AwardType.SPIRIT, AwardType.GRACIOUS_PROFESSIONALISM, AwardType.IMAGERY, AwardType.HIGHEST_ROOKIE_SEED, AwardType.SAFETY, AwardType.JUDGES, AwardType.ROOKIE_INSPIRATION, AwardType.WEBSITE],
        2011: [AwardType.SPIRIT, AwardType.GRACIOUS_PROFESSIONALISM, AwardType.IMAGERY, AwardType.HIGHEST_ROOKIE_SEED, AwardType.SAFETY, AwardType.JUDGES, AwardType.ROOKIE_INSPIRATION, AwardType.WEBSITE],
        2010: [AwardType.SPIRIT, AwardType.GRACIOUS_PROFESSIONALISM, AwardType.IMAGERY, AwardType.HIGHEST_ROOKIE_SEED, AwardType.SAFETY, AwardType.JUDGES, AwardType.ROOKIE_INSPIRATION, AwardType.WEBSITE],
        2009: [AwardType.SPIRIT, AwardType.GRACIOUS_PROFESSIONALISM, AwardType.IMAGERY, AwardType.JUDGES, AwardType.ROOKIE_INSPIRATION, AwardType.SAFETY, AwardType.WSU_AIM_HIGHER, AwardType.WEBSITE]
    }
