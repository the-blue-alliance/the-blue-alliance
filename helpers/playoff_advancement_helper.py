import copy
from collections import defaultdict

from consts.playoff_type import PlayoffType
from helpers.event_helper import EventHelper
from helpers.match_helper import MatchHelper
from models.match import Match


class PlayoffAdvancementHelper(object):

    OPPONENT = {
        'red': 'blue',
        'blue': 'red',
    }

    ROUND_ROBIN_TIEBREAKERS = {
        2017: ['Match Points'],
        2018: ['Park/Climb Points', 'Auto Points'],
        2019: ['Cargo Points', 'Hatch Panel Points'],
    }

    ADVANCEMENT_COUNT_2015 = {
        'ef': 8,
        'qf': 4,
        'sf': 2,
    }

    @classmethod
    def getPlayoffTemplate(cls, event):
        playoff_template = None

        if event.playoff_type == PlayoffType.CUSTOM:
            playoff_template = 'custom'
        if event.playoff_type == PlayoffType.AVG_SCORE_8_TEAM:
            playoff_template = 'playoff_table'
        elif event.playoff_type == PlayoffType.ROUND_ROBIN_6_TEAM:
            playoff_template = 'playoff_round_robin_6_team'

        return playoff_template

    @classmethod
    def getDoubleElimMatches(cls, event, matches):
        double_elim_matches = None
        if event.playoff_type == PlayoffType.DOUBLE_ELIM_8_TEAM:
            double_elim_matches = MatchHelper.organizeDoubleElimMatches(matches)
        return double_elim_matches

    @classmethod
    def generatePlayoffAdvancement(cls, event, matches):
        bracket_table = cls.generateBracket(matches, event, event.alliance_selections)

        playoff_advancement = None

        playoff_template = cls.getPlayoffTemplate(event)
        double_elim_matches = cls.getDoubleElimMatches(event, matches)

        if event.playoff_type == PlayoffType.AVG_SCORE_8_TEAM:
            playoff_advancement = cls.generatePlayoffAdvancement2015(matches, event.alliance_selections)
            for comp_level in ['qf', 'sf']:
                if comp_level in bracket_table:
                    del bracket_table[comp_level]
        elif event.playoff_type == PlayoffType.ROUND_ROBIN_6_TEAM:
            playoff_advancement = cls.generatePlayoffAdvancementRoundRobin(matches, event.year, event.alliance_selections)
            comp_levels = bracket_table.keys()
            for comp_level in comp_levels:
                if comp_level != 'f':
                    del bracket_table[comp_level]
        elif event.playoff_type == PlayoffType.BO3_FINALS or event.playoff_type == PlayoffType.BO5_FINALS:
            comp_levels = bracket_table.keys()
            for comp_level in comp_levels:
                if comp_level != 'f':
                    del bracket_table[comp_level]

        return bracket_table, playoff_advancement, double_elim_matches, playoff_template

    @classmethod
    def generatePlayoffAdvancementFromCSV(cls, event, csv_advancement, comp_level):
        """
        Generate properly formatted advancement info from the output of CSVAdvancementParser
        The output will be of the same format as generatePlayoffAdvancementRoundRobin
        """
        if event.playoff_type != PlayoffType.ROUND_ROBIN_6_TEAM:
            return {}

        advancement = []
        for alliance_advancement in csv_advancement:
            alliance = event.alliance_selections[alliance_advancement['alliance_number'] - 1]
            advancement.append([
                map(lambda p: int(p[3:]), alliance['picks']),
                alliance_advancement['cmp_points_matches'],
                sum(alliance_advancement['cmp_points_matches']),
                alliance_advancement['tiebreak1_matches'],
                sum(alliance_advancement['tiebreak1_matches']),
                alliance_advancement['tiebreak2_matches'],
                sum(alliance_advancement['tiebreak2_matches']),
                alliance.get('name'),
                {
                    'wins': alliance_advancement['wins'],
                    'losses': alliance_advancement['losses'],
                    'ties': alliance_advancement['ties'],
                }
            ])

        advancement = sorted(advancement, key=lambda x: -x[6])  # sort by tiebreaker2
        advancement = sorted(advancement, key=lambda x: -x[4])  # sort by tiebreaker1
        advancement = sorted(advancement, key=lambda x: -x[2])  # sort by championship points
        return {
            comp_level: advancement,
            "{}_complete".format(comp_level): True,
        }

    @classmethod
    def generateBracket(cls, matches, event, alliance_selections=None):
        complete_alliances = []
        bracket_table = defaultdict(lambda: defaultdict(dict))
        for comp_level in ['qf', 'sf', 'f']:
            for match in matches[comp_level]:
                set_key = "{}{}".format(comp_level, match.set_number)
                if set_key not in bracket_table[comp_level]:
                    bracket_table[comp_level][set_key] = {
                        'red_alliance': [],
                        'blue_alliance': [],
                        'winning_alliance': None,
                        'red_wins': 0,
                        'blue_wins': 0,
                        'red_record': {'wins': 0, 'losses': 0, 'ties': 0},
                        'blue_record': {'wins': 0, 'losses': 0, 'ties': 0},
                        'red_name': None,
                        'blue_name': None,
                    }
                for color in ['red', 'blue']:
                    alliance = copy.copy(match.alliances[color]['teams'])
                    bracket_table[comp_level][set_key]['{}_name'.format(color)] = cls._getAllianceName(alliance, alliance_selections)
                    for i, complete_alliance in enumerate(complete_alliances):  # search for alliance. could be more efficient
                        if len(set(alliance).intersection(set(complete_alliance))) >= 2:  # if >= 2 teams are the same, then the alliance is the same
                            backups = list(set(alliance).difference(set(complete_alliance)))
                            complete_alliances[i] += backups  # ensures that backup robots are listed last

                            for team_num in cls.getOrderedAlliance(complete_alliances[i], alliance_selections):
                                if team_num not in bracket_table[comp_level][set_key]['{}_alliance'.format(color)]:
                                    bracket_table[comp_level][set_key]['{}_alliance'.format(color)].append(team_num)

                            break
                    else:
                        complete_alliances.append(alliance)

                winner = match.winning_alliance
                if not winner or winner == '':
                    # if the match is a tie
                    bracket_table[comp_level][set_key]['red_record']['ties'] = \
                        bracket_table[comp_level][set_key]['red_record']['ties'] + 1
                    bracket_table[comp_level][set_key]['blue_record']['ties'] = \
                        bracket_table[comp_level][set_key]['blue_record']['ties'] + 1
                    continue

                bracket_table[comp_level][set_key]['{}_wins'.format(winner)] = \
                    bracket_table[comp_level][set_key]['{}_wins'.format(winner)] + 1
                bracket_table[comp_level][set_key]['{}_record'.format(winner)]['wins'] = \
                    bracket_table[comp_level][set_key]['{}_record'.format(winner)]['wins'] + 1
                bracket_table[comp_level][set_key]['{}_record'.format(cls.OPPONENT[winner])]['losses'] = \
                    bracket_table[comp_level][set_key]['{}_record'.format(cls.OPPONENT[winner])]['losses'] + 1
                n = 3 if event.playoff_type == PlayoffType.BO5_FINALS else 2
                if bracket_table[comp_level][set_key]['red_wins'] == n:
                    bracket_table[comp_level][set_key]['winning_alliance'] = 'red'
                if bracket_table[comp_level][set_key]['blue_wins'] == n:
                    bracket_table[comp_level][set_key]['winning_alliance'] = 'blue'

        return bracket_table

    @classmethod
    def generatePlayoffAdvancement2015(cls, matches, alliance_selections=None):
        complete_alliances = []
        advancement = defaultdict(list)  # key: comp level; value: list of [complete_alliance, [scores], average_score, num_played]
        for comp_level in ['ef', 'qf', 'sf']:
            for match in matches.get(comp_level, []):
                if not match.has_been_played:
                    continue
                for color in ['red', 'blue']:
                    alliance = cls.getOrderedAlliance(match.alliances[color]['teams'], alliance_selections)
                    for i, complete_alliance in enumerate(complete_alliances):  # search for alliance. could be more efficient
                        if len(set(alliance).intersection(set(complete_alliance))) >= 2:  # if >= 2 teams are the same, then the alliance is the same
                            backups = list(set(alliance).difference(set(complete_alliance)))
                            complete_alliances[i] += backups  # ensures that backup robots are listed last
                            break
                    else:
                        i = None
                        complete_alliances.append(alliance)

                    is_new = False
                    if i is not None:
                        for j, (complete_alliance, scores, _, _) in enumerate(advancement[comp_level]):  # search for alliance. could be more efficient
                            if len(set(complete_alliances[i]).intersection(set(complete_alliance))) >= 2:  # if >= 2 teams are the same, then the alliance is the same
                                complete_alliance = complete_alliances[i]
                                scores.append(match.alliances[color]['score'])
                                advancement[comp_level][j][2] = float(sum(scores)) / len(scores)
                                advancement[comp_level][j][3] = len(scores)
                                break
                        else:
                            is_new = True

                    score = match.alliances[color]['score']
                    if i is None:
                        advancement[comp_level].append([alliance, [score], score, 1])
                    elif is_new:
                        advancement[comp_level].append([complete_alliances[i], [score], score, 1])

            advancement[comp_level] = sorted(advancement[comp_level], key=lambda x: -x[2])  # sort by descending average score

        return advancement

    @classmethod
    def generatePlayoffAdvancementRoundRobin(cls, matches, year, alliance_selections=None):
        complete_alliances = []
        alliance_names = []
        advancement = defaultdict(list)  # key: comp level; value: list of [complete_alliance, [champ_points], sum_champ_points, [tiebreaker1], sum_tiebreaker1, [tiebreaker2], sum_tiebreaker2
        for comp_level in ['sf']:  # In case this needs to scale to more levels
            any_unplayed = False
            for match in matches.get(comp_level, []):
                if not match.has_been_played:
                    any_unplayed = True
                for color in ['red', 'blue']:
                    alliance = cls.getOrderedAlliance(match.alliances[color]['teams'], alliance_selections)
                    alliance_name = cls.getAllianceName(match.alliances[color]['teams'], alliance_selections)
                    for i, complete_alliance in enumerate(complete_alliances):  # search for alliance. could be more efficient
                        if len(set(alliance).intersection(set(complete_alliance))) >= 2:  # if >= 2 teams are the same, then the alliance is the same
                            backups = list(set(alliance).difference(set(complete_alliance)))
                            complete_alliances[i] += backups  # ensures that backup robots are listed last
                            alliance_names[i] = alliance_name
                            break
                    else:
                        i = None
                        complete_alliances.append(alliance)
                        alliance_names.append(alliance_name)

                    is_new = False
                    if i is not None:
                        for j, (complete_alliance, champ_points, _, tiebreaker1, _, tiebreaker2, _, _, record) in enumerate(advancement[comp_level]):  # search for alliance. could be more efficient
                            if len(set(complete_alliances[i]).intersection(set(complete_alliance))) >= 2:  # if >= 2 teams are the same, then the alliance is the same
                                if not match.has_been_played:
                                    cp = 0
                                elif match.winning_alliance == color:
                                    cp = 2
                                    record['wins'] += 1
                                elif match.winning_alliance == '':
                                    cp = 1
                                    record['ties'] += 1
                                else:
                                    cp = 0
                                    record['losses'] += 1
                                if match.has_been_played:
                                    champ_points.append(cp)
                                    if year == 2018:
                                        tiebreaker1.append(match.score_breakdown[color]['endgamePoints'])
                                        tiebreaker2.append(match.score_breakdown[color]['autoPoints'])
                                    elif year == 2019:
                                        tiebreaker1.append(match.score_breakdown[color]['cargoPoints'])
                                        tiebreaker2.append(match.score_breakdown[color]['hatchPanelPoints'])
                                    else:
                                        tiebreaker1.append(match.alliances[color]['score'])
                                        tiebreaker2.append(0)
                                    advancement[comp_level][j][2] = sum(champ_points)
                                    advancement[comp_level][j][4] = sum(tiebreaker1)
                                    advancement[comp_level][j][6] = sum(tiebreaker2)
                                break
                        else:
                            is_new = True

                    if year == 2018:
                        tiebreaker1 = match.score_breakdown[color]['endgamePoints'] if match.has_been_played else 0
                        tiebreaker2 = match.score_breakdown[color]['autoPoints'] if match.has_been_played else 0
                    elif year == 2019:
                        tiebreaker1 = match.score_breakdown[color]['cargoPoints'] if match.has_been_played else 0
                        tiebreaker2 = match.score_breakdown[color]['hatchPanelPoints'] if match.has_been_played else 0
                    else:
                        tiebreaker1 = match.alliances[color]['score'] if match.has_been_played else 0
                        tiebreaker2 = 0

                    record = {'wins': 0, 'losses': 0, 'ties': 0}
                    if not match.has_been_played:
                        cp = 0
                    elif match.winning_alliance == color:
                        cp = 2
                        record['wins'] += 1
                    elif match.winning_alliance == '':
                        cp = 1
                        record['ties'] += 1
                    else:
                        cp = 0
                        record['losses'] += 1
                    if i is None:
                        advancement[comp_level].append([alliance, [cp], cp, [tiebreaker1], tiebreaker1, [tiebreaker2], tiebreaker2, alliance_name, record])
                    elif is_new:
                        advancement[comp_level].append([complete_alliances[i], [cp], cp, [tiebreaker1], tiebreaker1, [tiebreaker2], tiebreaker2, alliance_names[i], record])

            advancement[comp_level] = sorted(advancement[comp_level], key=lambda x: -x[6])  # sort by tiebreaker2
            advancement[comp_level] = sorted(advancement[comp_level], key=lambda x: -x[4])  # sort by tiebreaker1
            advancement[comp_level] = sorted(advancement[comp_level], key=lambda x: -x[2])  # sort by championship points
            advancement['{}_complete'.format(comp_level)] = not any_unplayed

        return advancement

    @classmethod
    def getOrderedAlliance(cls, team_keys, alliance_selections):
        if alliance_selections:
            for alliance_selection in alliance_selections:  # search for alliance. could be more efficient
                picks = alliance_selection['picks']
                if len(set(picks).intersection(set(team_keys))) >= 2:  # if >= 2 teams are the same, then the alliance is the same
                    backups = list(set(team_keys).difference(set(picks)))
                    team_keys = picks + backups
                    break

        team_nums = []
        for team in team_keys:
            # Strip the "frc" prefix
            team_nums.append(team[3:])
        return team_nums

    @classmethod
    def _getAllianceName(cls, team_keys, alliance_selections):
        if not alliance_selections:
            return None
        for alliance_selection in alliance_selections:  # search for alliance. could be more efficient
            picks = alliance_selection['picks']
            if len(set(picks).intersection(set(team_keys))) >= 2:  # if >= 2 teams are the same, then the alliance is the same
                return alliance_selection.get('name')
        return None

    @classmethod
    def getAllianceName(cls, team_keys, alliance_selections):
        if alliance_selections:
            for alliance_selection in alliance_selections:  # search for alliance. could be more efficient
                picks = alliance_selection['picks']
                if len(set(picks).intersection(set(team_keys))) >= 2:  # if >= 2 teams are the same, then the alliance is the same
                    return alliance_selection.get('name')

        return ''

    @classmethod
    def transformBracketLevelForApi(cls, event, bracket_table, comp_level):
        level_ranks = []
        for series_level, set_bracket in bracket_table[comp_level].iteritems():
            series = int(''.join(c for c in series_level if c.isdigit()))
            data = {
                'level': "{}{}".format(comp_level, series),
                'level_name': Match.COMP_LEVELS_VERBOSE_FULL[comp_level] + (" %d" % series if comp_level != 'f' else ''),
                'rankings': None,
                'type': 'best_of_3',  # TODO handle other playoff types
                'sort_order_info': [{"name": "Wins", "type": "int", "precision": 0}],
                'extra_stats_info': [],
            }

            alliances = [cls._makeAllianceRankRow(c, set_bracket) for c in ['red', 'blue']]
            data['rankings'] = sorted(alliances, key=lambda a: a['record']['wins'], reverse=True)

            level_ranks.append(data)

        return level_ranks

    @classmethod
    def _makeAllianceRankRow(cls, color, bracket_set):
        record = bracket_set['{}_record'.format(color)]
        return {
            'team_keys': map(lambda t: "frc{}".format(t), bracket_set['{}_alliance'.format(color)]),
            'alliance_name': bracket_set['{}_name'.format(color)],
            'alliance_color': color,
            'record': record,
            'matches_played': record['wins'] + record['losses'] + record['ties'],
            'sort_orders': [bracket_set['{}_wins'.format(color)]],
            'extra_stats': [],
        }

    @classmethod
    def transform2015AdvancementLevelForApi(cls, event, playoff_advancement, comp_level):
        level_order = Match.COMP_LEVELS_PLAY_ORDER[comp_level]
        next_level = Match.COMP_LEVELS_PLAY_ORDER.keys()[Match.COMP_LEVELS_PLAY_ORDER.values().index(level_order + 1)]
        data = {
            'level':
            comp_level,
            'level_name':
            Match.COMP_LEVELS_VERBOSE_FULL[comp_level],
            'rankings': [],
            'type':
            'average_score',
            'sort_order_info': [
                {
                    'name': 'Average Score',
                    'type': 'int',
                    'precision': 2
                },
            ],
            'extra_stats_info': [
                {
                    'name':
                    'Advance to {}'.format(
                        Match.COMP_LEVELS_VERBOSE[next_level]),
                    'type':
                    'bool',
                    'precision':
                    0
                },
            ],
        }
        for i, alliance in enumerate(playoff_advancement[comp_level]):
            rank = i + 1
            data['rankings'].append(cls._make2015AllianceAdvancementRow(event, alliance, rank, comp_level))
        return [data]

    @classmethod
    def transformRoundRobinAdvancementLevelForApi(cls, event, playoff_advancement, comp_level):
        data = {
            'level': comp_level,
            'level_name': 'Round Robin ' + Match.COMP_LEVELS_VERBOSE_FULL[comp_level],
            'rankings': [],
            'type': 'round_robin',
            'sort_order_info': [
                {'name': 'Champ Points', 'type': 'int', 'precision': 0},
            ],
            'extra_stats_info': [
                {'name': 'Advance to Finals', 'type': 'bool', 'precision': 0},
            ],
        }

        for tiebreaker in cls.ROUND_ROBIN_TIEBREAKERS[event.year]:
            data['sort_order_info'].append({
                'name': tiebreaker,
                'type': 'int',
                'precision': 0,
            })

        for i, alliance in enumerate(playoff_advancement[comp_level]):
            rank = i + 1
            data['rankings'].append(cls._makeAllianceAdvancementRow(event, alliance, rank))
        return [data]

    @classmethod
    def _makeAllianceAdvancementRow(cls, event, alliance, rank):
        record = alliance[8]
        row = {
            'team_keys': map(lambda t: "frc{}".format(t), alliance[0]),
            'alliance_name': alliance[7],  # alliance name
            'record': record,
            'matches_played': record['wins'] + record['losses'] + record['ties'],
            'rank': rank,
            'sort_orders': [alliance[2], alliance[4], alliance[6]],
            'extra_stats': [int(rank <= 2)],  # top 2 teams advance
        }

        return row

    @classmethod
    def _make2015AllianceAdvancementRow(cls, event, alliance, rank, comp_level):
        team_keys = map(lambda t: "frc{}".format(t), alliance[0])
        row = {
            'team_keys': team_keys,
            'alliance_name': cls._getAllianceName(team_keys, event.alliance_selections),
            'rank': rank,
            'matches_played': alliance[3],
            'sort_orders': [alliance[2]],
            'extra_stats': [int(rank <= cls.ADVANCEMENT_COUNT_2015[comp_level])],
        }

        return row
