
class PlayoffType(object):
    # Standard Brackets
    BRACKET_8_TEAM = 0
    BRACKET_16_TEAM = 1
    BRACKET_4_TEAM = 2

    # 2015 is special
    AVG_SCORE_8_TEAM = 3

    # Round Robin
    ROUND_ROBIN_6_TEAM = 4

    # Double Elimination Bracket
    DOUBLE_ELIM_8_TEAM = 5

    # Festival of Champions
    BO5_FINALS = 6
    BO3_FINALS = 7

    # Custom
    CUSTOM = 8

    BRACKET_TYPES = [BRACKET_8_TEAM, BRACKET_16_TEAM, BRACKET_4_TEAM]
    DOUBLE_ELIM_TYPES = [DOUBLE_ELIM_8_TEAM]

    # Names for Rendering
    type_names = {
        BRACKET_8_TEAM: "Elimination Bracket (8 Alliances)",
        BRACKET_4_TEAM: "Elimination Bracket (4 Alliances)",
        BRACKET_16_TEAM: "Elimination Bracket (16 Alliances)",
        AVG_SCORE_8_TEAM: "Average Score (8 Alliances)",
        ROUND_ROBIN_6_TEAM: "Round Robin (6 Alliances)",
        DOUBLE_ELIM_8_TEAM: "Double Elimination Bracket (8 Alliances)",
        BO3_FINALS: "Best of 3 Finals",
        BO5_FINALS: "Best of 5 Finals",
        CUSTOM: "Custom",
    }

    @classmethod
    def get_comp_level(cls, playoff_type, match_level, match_number):
        if match_level == 'Qualification':
            return 'qm'
        else:
            if playoff_type == cls.AVG_SCORE_8_TEAM:
                if match_number <= 8:
                    return 'qf'
                elif match_number <= 14:
                    return 'sf'
                else:
                    return 'f'
            elif playoff_type == cls.ROUND_ROBIN_6_TEAM:
                # Einstein 2017 for example. 15 round robin matches, then finals
                return 'sf' if match_number <= 15 else 'f'
            elif playoff_type == cls.DOUBLE_ELIM_8_TEAM:
                level, _, _ = cls.DOUBLE_ELIM_MAPPING.get(match_number)
                return level
            elif playoff_type == cls.BO3_FINALS or playoff_type == cls.BO5_FINALS:
                return 'f'
            else:
                if playoff_type == cls.BRACKET_16_TEAM:
                    return cls.get_comp_level_octo(match_number)
                elif playoff_type == cls.BRACKET_4_TEAM and match_number <= 12:
                    # Account for a 4 team bracket where numbering starts at 1
                    match_number += 12
                if match_number <= 12:
                    return 'qf'
                elif match_number <= 18:
                    return 'sf'
                else:
                    return 'f'

    @classmethod
    def get_comp_level_octo(cls, match_number):
        """ No 2015 support """
        if match_number <= 24:
            return 'ef'
        elif match_number <= 36:
            return 'qf'
        elif match_number <= 42:
            return 'sf'
        else:
            return 'f'

    @classmethod
    def get_set_match_number(cls, playoff_type, comp_level, match_number):
        if comp_level == 'qm':
            return 1, match_number

        if playoff_type == cls.AVG_SCORE_8_TEAM:
            if comp_level == 'sf':
                return 1, match_number - 8
            elif comp_level == 'f':
                return 1, match_number - 14
            else:  # qf
                return 1, match_number
        if playoff_type == cls.ROUND_ROBIN_6_TEAM:
            # Einstein 2017 for example. 15 round robin matches from sf1-1 to sf1-15, then finals
            match_number = match_number if match_number <= 15 else match_number - 15
            if comp_level == 'f':
                return 1, match_number
            else:
                return 1, match_number
        elif playoff_type == cls.DOUBLE_ELIM_8_TEAM:
            level, set, match = cls.DOUBLE_ELIM_MAPPING.get(match_number)
            return set, match
        elif playoff_type == cls.BO3_FINALS or playoff_type == cls.BO5_FINALS:
            return 1, match_number
        else:
            if playoff_type == cls.BRACKET_4_TEAM and match_number <= 12:
                match_number += 12
            return cls.BRACKET_OCTO_ELIM_MAPPING[match_number] if playoff_type == cls.BRACKET_16_TEAM \
                else cls.BRACKET_ELIM_MAPPING[match_number]

    # Determine if a match is in the winner or loser bracket
    @classmethod
    def get_double_elim_bracket(cls, level, set):
        if level == 'ef':
            return 'winner' if set <= 4 else 'loser'
        elif level == 'qf':
            return 'winner' if set <= 2 else 'loser'
        elif level == 'sf':
            return 'winner' if set == 1 else 'loser'
        elif level == 'f':
            return 'loser' if set == 1 else 'winner'

    BRACKET_ELIM_MAPPING = {
        1: (1, 1),  # (set, match)
        2: (2, 1),
        3: (3, 1),
        4: (4, 1),
        5: (1, 2),
        6: (2, 2),
        7: (3, 2),
        8: (4, 2),
        9: (1, 3),
        10: (2, 3),
        11: (3, 3),
        12: (4, 3),
        13: (1, 1),
        14: (2, 1),
        15: (1, 2),
        16: (2, 2),
        17: (1, 3),
        18: (2, 3),
        19: (1, 1),
        20: (1, 2),
        21: (1, 3),
        22: (1, 4),
        23: (1, 5),
        24: (1, 6),
    }

    BRACKET_OCTO_ELIM_MAPPING = {
        # octofinals
        1: (1, 1),  # (set, match)
        2: (2, 1),
        3: (3, 1),
        4: (4, 1),
        5: (5, 1),
        6: (6, 1),
        7: (7, 1),
        8: (8, 1),
        9: (1, 2),
        10: (2, 2),
        11: (3, 2),
        12: (4, 2),
        13: (5, 2),
        14: (6, 2),
        15: (7, 2),
        16: (8, 2),
        17: (1, 3),
        18: (2, 3),
        19: (3, 3),
        20: (4, 3),
        21: (5, 3),
        22: (6, 3),
        23: (7, 3),
        24: (8, 3),

        # quarterfinals
        25: (1, 1),
        26: (2, 1),
        27: (3, 1),
        28: (4, 1),
        29: (1, 2),
        30: (2, 2),
        31: (3, 2),
        32: (4, 2),
        33: (1, 3),
        34: (2, 3),
        35: (3, 3),
        36: (4, 3),

        # semifinals
        37: (1, 1),
        38: (2, 1),
        39: (1, 2),
        40: (2, 2),
        41: (1, 3),
        42: (2, 3),

        # finals
        43: (1, 1),
        44: (1, 2),
        45: (1, 3),
        46: (1, 4),
        47: (1, 5),
        48: (1, 6),
    }

    # Map match number -> set/match for a 8 alliance double elim bracket
    # Based off: https://www.printyourbrackets.com/fillable-brackets/8-seeded-double-fillable.pdf
    # Matches 1-6 are ef, 7-10 are qf, 11/12 are sf, 13 is f1, and 14/15 are f2
    DOUBLE_ELIM_MAPPING = {
        # octofinals (winners bracket)
        1: ('ef', 1, 1),
        2: ('ef', 2, 1),
        3: ('ef', 3, 1),
        4: ('ef', 4, 1),

        # octofinals (losers bracket)
        5: ('ef', 5, 1),
        6: ('ef', 6, 1),

        # quarterfinals (winners bracket)
        7: ('qf', 1, 1),
        8: ('qf', 2, 1),

        # quarterfinals (losers bracket)
        9: ('qf', 3, 1),
        10: ('qf', 4, 1),

        # semifinals (winners bracket)
        11: ('sf', 1, 1),

        # semifinals (losers bracket)
        12: ('sf', 2, 1),

        # finals (losers bracket)
        13: ('f', 1, 1),

        # overall finals (winners bracket)
        14: ('f', 2, 1),
        15: ('f', 2, 2),
    }
