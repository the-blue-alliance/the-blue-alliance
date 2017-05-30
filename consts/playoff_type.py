
class PlayoffType(object):
    # Standard Brackets
    BRACKET_8_TEAM = 0
    BRACKET_16_TEAM = 1
    BRACKET_4_TEAM = 2

    # 2015 is special
    AVG_SCORE_8_TEAM = 3

    # Round Robin
    ROUND_ROBIN_6_TEAM = 4

    BRACKET_TYPES = [BRACKET_8_TEAM, BRACKET_16_TEAM, BRACKET_4_TEAM]

    # Names for Rendering
    type_names = {
        BRACKET_8_TEAM: "Elimination Bracket (8 Alliances)",
        BRACKET_4_TEAM: "Elimination Bracket (4 Alliances)",
        BRACKET_16_TEAM: "Elimination Bracket (16 Alliances)",
        AVG_SCORE_8_TEAM: "Average Score (8 Alliances)",
        ROUND_ROBIN_6_TEAM: "Round Robin (6 Alliances)"
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
        if playoff_type == cls.AVG_SCORE_8_TEAM:
            if comp_level == 'sf':
                return 1, match_number - 8
            elif comp_level == 'f':
                return 1, match_number - 14
            else:  # qm, qf
                return 1, match_number
        if playoff_type == cls.ROUND_ROBIN_6_TEAM:
            # Einstein 2017 for example. 15 round robin matches from sf1-1 to sf1-15, then finals
            match_number = match_number if match_number <= 15 else match_number - 15
            if comp_level == 'f':
                return 1, match_number
            else:
                return 1, match_number
        else:
            if playoff_type == cls.BRACKET_4_TEAM and match_number <= 12:
                match_number += 12
            if comp_level in {'ef', 'qf', 'sf', 'f'}:
                return cls.BRACKET_OCTO_ELIM_MAPPING[match_number] if playoff_type == cls.BRACKET_16_TEAM \
                    else cls.BRACKET_ELIM_MAPPING[match_number]
            else:  # qm
                return 1, match_number

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
