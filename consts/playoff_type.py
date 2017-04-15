
class PlayoffType(object):
    # Standard Brackets
    BRACKET_8_TEAM = 0
    BRACKET_16_TEAM = 1
    BRACKET_4_TEAM = 2

    # 2015 is special
    AVG_SCORE_8_TEAM = 3

    # Round Robin
    ROUND_ROBIN_6_TEAM = 4

    # Names foR Rendering
    type_names = {
        BRACKET_8_TEAM: "Elimination Bracket (8 Alliances)",
        BRACKET_4_TEAM: "Elimination Bracket (4 Alliances)",
        BRACKET_16_TEAM: "Elimination Bracket (16 Alliances)",
        AVG_SCORE_8_TEAM: "Average Score (8 Alliances)",
        ROUND_ROBIN_6_TEAM: "Round Robin (6 Alliances)"
    }
