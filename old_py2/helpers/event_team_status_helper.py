import copy

from google.appengine.ext import ndb
from google.appengine.ext.ndb.tasklets import Future

from consts.playoff_type import PlayoffType
from helpers.match_helper import MatchHelper
from helpers.rankings_helper import RankingsHelper
from helpers.team_helper import TeamHelper
from models.event_details import EventDetails
from models.match import Match


class EventTeamStatusHelper(object):
    @classmethod
    def generate_team_at_event_alliance_status_string(cls, team_key, status_dict):
        if not status_dict:
            return '--'
        alliance = status_dict.get('alliance')
        if alliance:
            pick = alliance['pick']
            if pick == 0:
                pick = 'Captain'
            else:
                # Convert to ordinal number http://stackoverflow.com/questions/9647202/ordinal-numbers-replacement
                pick = '{} Pick'.format("%d%s" % (pick,"tsnrhtdd"[(pick/10%10!=1)*(pick%10<4)*pick%10::4]))
            backup = alliance['backup']
            if backup and team_key == backup['in']:
                pick = 'Backup'

            return '<b>{}</b> of <b>{}</b>'.format(pick, alliance['name'])
        else:
            return '--'

    @classmethod
    def generate_team_at_event_playoff_status_string(cls, team_key, status_dict):
        if not status_dict:
            return '--'
        playoff = status_dict.get('playoff')
        if playoff:
            level = playoff.get('level')
            status = playoff.get('status')
            record = playoff.get('record')
            level_record = playoff.get('current_level_record')
            playoff_average = playoff.get('playoff_average')

            if status == 'playing':
                record_str = '{}-{}-{}'.format(level_record['wins'], level_record['losses'], level_record['ties'])
                playoff_str = 'Currently <b>{}</b> in the <b>{}</b>'.format(record_str, Match.COMP_LEVELS_VERBOSE_FULL[level])
            else:
                if status == 'won':
                    if level == 'f':
                        playoff_str = '<b>Won the event</b>'
                    else:
                        playoff_str = '<b>Won the {}</b>'.format(Match.COMP_LEVELS_VERBOSE_FULL[level])
                elif status == 'eliminated':
                    playoff_str = '<b>Eliminated in the {}</b>'.format(Match.COMP_LEVELS_VERBOSE_FULL[level])
                else:
                    raise Exception("Unknown playoff status: {}".format(status))
                if record:
                    playoff_str += ' with a playoff record of <b>{}-{}-{}</b>'.format(record['wins'], record['losses'], record['ties'])
                if playoff_average:
                    playoff_str += ' with a playoff average of <b>{:.1f}</b>'.format(playoff_average)
            return playoff_str
        else:
            return '--'

    @classmethod
    def generate_team_at_event_status_string(cls, team_key, status_dict, formatting=True, event=None, include_team=True, verbose=False):
        """
        Generate a team at event status string from a status dict
        """
        if include_team:
            default_msg = 'Team {} is waiting for the {} to begin.'.format(team_key[3:], event.normalized_name if event else 'event')
        else:
            default_msg = 'is waiting for the {} to begin.'.format(event.normalized_name if event else 'event')
        if not status_dict:
            return default_msg

        qual = status_dict.get('qual')
        alliance = status_dict.get('alliance')
        playoff = status_dict.get('playoff')

        components = []
        if qual:
            status = qual.get('status')
            num_teams = qual.get('num_teams')
            ranking = qual.get('ranking')

            if ranking:
                rank = ranking.get('rank')
                record = ranking.get('record')
                qual_average = ranking.get('qual_average')

                num_teams_str = ''
                if num_teams:
                    num_teams_str = ' of {}'.format(num_teams) if verbose else '/{}'.format(num_teams)

                if status == 'completed':
                    is_tense = 'was'
                    has_tense = 'had'
                else:
                    is_tense = 'is'
                    has_tense = 'has'

                qual_str = None
                if record:
                    if verbose:
                        record_str = cls._build_verbose_record(record)
                    else:
                        record_str = '{}-{}-{}'.format(record['wins'], record['losses'], record['ties'])
                    if rank:
                        qual_str = '{} <b>Rank {}{}</b> with a record of <b>{}</b> in quals'.format(is_tense, rank, num_teams_str, record_str)
                    else:
                        qual_str = '{} a record of <b>{}</b> in quals'.format(has_tense, record_str)
                elif qual_average:
                    if rank:
                        qual_str = '{} <b>Rank {}{}</b> with an average score of <b>{:.1f}</b> in quals'.format(is_tense, rank, num_teams_str, qual_average)
                    else:
                        qual_str = '{} an average score of <b>{:.1f}</b> in quals'.format(has_tense, qual_average)

                if qual_str:
                    components.append(qual_str)

        pick = None
        if alliance:
            pick = alliance['pick']
            if pick == 0:
                pick = 'Captain'
            else:
                # Convert to ordinal number http://stackoverflow.com/questions/9647202/ordinal-numbers-replacement
                pick = '{} Pick'.format("%d%s" % (pick,"tsnrhtdd"[(pick/10%10!=1)*(pick%10<4)*pick%10::4]))
            backup = alliance['backup']
            if backup and team_key == backup['in']:
                pick = 'Backup'

            if not playoff:
                alliance_str = 'will be competing in the playoffs as the <b>{}</b> of <b>{}</b>'.format(pick, alliance['name'])
                components.append(alliance_str)

        if playoff:
            level = playoff.get('level')
            status = playoff.get('status')
            record = playoff.get('record')
            level_record = playoff.get('current_level_record')
            playoff_average = playoff.get('playoff_average')

            if status == 'playing':
                if verbose:
                    record_str = cls._build_verbose_record(level_record)
                else:
                    record_str = '{}-{}-{}'.format(level_record['wins'], level_record['losses'], level_record['ties'])
                playoff_str = 'is <b>{}</b> in the <b>{}</b>'.format(record_str, Match.COMP_LEVELS_VERBOSE_FULL[level])
                if alliance:
                    playoff_str += ' as the <b>{}</b> of <b>{}</b>'.format(pick, alliance['name'])
                components = [playoff_str]
            else:
                if alliance:
                    components.append('competed in the playoffs as the <b>{}</b> of <b>{}</b>'.format(pick, alliance['name']))

                if status == 'won':
                    if level == 'f':
                        playoff_str = '<b>won the event</b>'
                    else:
                        playoff_str = '<b>won the {}</b>'.format(Match.COMP_LEVELS_VERBOSE_FULL[level])
                elif status == 'eliminated':
                    playoff_str = 'was <b>eliminated in the {}</b>'.format(Match.COMP_LEVELS_VERBOSE_FULL[level])
                else:
                    raise Exception("Unknown playoff status: {}".format(status))
                if record:
                    playoff_str += ' with a playoff record of <b>{}-{}-{}</b>'.format(record['wins'], record['losses'], record['ties'])
                if playoff_average:
                    playoff_str += ' with a playoff average of <b>{:.1f}</b>'.format(playoff_average)
                components.append(playoff_str)

        if not components:
            return default_msg

        if len(components) > 1:
            components[-1] = 'and {}'.format(components[-1])
        if len(components) > 2:
            join_str = ', '
        else:
            join_str = ' '

        if include_team:
            final_string = 'Team {} {}'.format(team_key[3:], join_str.join(components))
        else:
            final_string = '{}'.format(join_str.join(components))
        if event:
            final_string += ' at the {}.'.format(event.normalized_name)
        else:
            final_string += '.'
        return final_string if formatting else final_string.replace('<b>', '').replace('</b>', '')

    @classmethod
    def generate_team_at_event_status(cls, team_key, event, matches=None):
        """
        Generate a dict containing team@event status information
        :param team_key: Key name of the team to focus on
        :param event: Event object
        :param matches: Organized matches (via MatchHelper.organizeMatches) from the event, optional
        """
        event_details = event.details
        if not matches:
            matches = event.matches
        team_matches = [m for m in matches if team_key in m.team_key_names]
        next_match = MatchHelper.upcomingMatches(team_matches, num=1)
        last_match = MatchHelper.recentMatches(team_matches, num=1)
        matches = MatchHelper.organizeMatches(matches)
        return copy.deepcopy({
            'qual': cls._build_qual_info(team_key, event_details, matches, event.year),
            'alliance': cls._build_alliance_info(team_key, event_details, matches),
            'playoff': cls._build_playoff_info(team_key, event_details, matches, event.year, event.playoff_type),
            'last_match_key': last_match[0].key_name if last_match else None,
            'next_match_key': next_match[0].key_name if next_match else None,
        })  # TODO: Results are getting mixed unless copied. 2017-02-03 -fangeugene

    @classmethod
    def _build_qual_info(cls, team_key, event_details, matches, year):
        if not matches['qm']:
            status = 'not_started'
        else:
            status = 'completed'
            for match in matches['qm']:
                if not match.has_been_played:
                    status = 'playing'
                    break

        if event_details and event_details.rankings2:
            rankings = event_details.rankings2

            qual_info = None
            for ranking in rankings:
                if ranking['team_key'] == team_key:
                    qual_info = {
                        'status': status,
                        'ranking': ranking,
                    }
                    break

            if qual_info:
                qual_info['num_teams'] = len(rankings)
                qual_info['sort_order_info'] = RankingsHelper.get_sort_order_info(event_details)

            return qual_info
        else:
            # Use matches as fallback
            all_teams = set()
            wins = 0
            losses = 0
            ties = 0
            qual_score_sum = 0
            matches_played = 0
            for match in matches['qm']:
                for color in ['red', 'blue']:
                    for team in match.alliances[color]['teams']:
                        all_teams.add(team)
                        if team == team_key and match.has_been_played and \
                                team_key not in match.alliances[color]['surrogates']:
                            matches_played += 1

                            if match.winning_alliance == color:
                                wins += 1
                            elif match.winning_alliance == '':
                                ties += 1
                            else:
                                losses += 1

                            qual_score_sum += match.alliances[color]['score']

            qual_average = float(qual_score_sum) / matches_played if matches_played else 0

            if team_key in all_teams:
                return {
                    'status': status,
                    'ranking': {
                        'rank': None,
                        'matches_played': matches_played,
                        'dq': None,
                        'record': {
                            'wins': wins,
                            'losses': losses,
                            'ties': ties,
                        } if year != 2015 else None,
                        'qual_average': qual_average if year == 2015 else None,
                        'sort_orders': None,
                        'team_key': team_key,
                    },
                    'num_teams': len(all_teams),
                    'sort_order_info': None
                }
            else:
                return None

    @classmethod
    def _build_alliance_info(cls, team_key, event_details, matches):
        if not event_details or not event_details.alliance_selections:
            return None
        alliance, number = cls._get_alliance(team_key, event_details, matches)
        if not alliance:
            return None

        # Calculate the role played by the team on the alliance
        backup_info = alliance.get('backup', {}) if alliance.get('backup') else {}
        pick = -1 if team_key == backup_info.get('in', "") else None
        for i, team in enumerate(alliance['picks']):
            if team == team_key:
                pick = i
                break

        return {
            'pick': pick,
            'name': alliance.get('name', "Alliance {}".format(number)),
            'number': number,
            'backup': alliance.get('backup'),
        }

    @classmethod
    def _build_playoff_info(cls, team_key, event_details, matches, year, playoff_type):
        # Matches needs to be all playoff matches at the event, to properly account for backups
        import numpy as np
        alliance, _ = cls._get_alliance(team_key, event_details, matches)
        complete_alliance = set(alliance['picks']) if alliance else set()
        if alliance and alliance.get('backup'):
            complete_alliance.add(alliance['backup']['in'])

        is_bo5 = playoff_type == PlayoffType.BO5_FINALS

        all_wins = 0
        all_losses = 0
        all_ties = 0
        playoff_scores = []
        status = None
        for comp_level in ['f', 'sf', 'qf', 'ef']:  # playoffs
            if matches[comp_level]:
                level_wins = 0
                level_losses = 0
                level_ties = 0
                level_matches = 0
                level_played = 0
                for match in matches[comp_level]:
                    for color in ['red', 'blue']:
                        match_alliance = set(match.alliances[color]['teams'])
                        if len(match_alliance.intersection(complete_alliance)) >= 2:
                            playoff_scores.append(match.alliances[color]['score'])
                            level_matches += 1
                            if match.has_been_played:
                                if match.winning_alliance == color:
                                    level_wins += 1
                                    all_wins += 1
                                elif not match.winning_alliance:
                                    if not (year == 2015 and comp_level != 'f'):
                                        # The match was a tie
                                        level_ties += 1
                                        all_ties += 1
                                else:
                                    level_losses += 1
                                    all_losses += 1
                                level_played += 1
                if not status:
                    # Only set this for the first comp level that gets this far,
                    # But run through the rest to calculate the full record
                    if level_wins == (3 if is_bo5 else 2):
                        status = {
                            'status': 'won',
                            'level': comp_level,
                        }
                    elif level_losses == (3 if is_bo5 else 2):
                        status = {
                            'status': 'eliminated',
                            'level': comp_level
                        }
                    elif level_matches > 0:
                        if year == 2015:
                            # This only works for past events, but 2015 is in the past so this works
                            status = {
                                'status': 'eliminated',
                                'level': comp_level,
                            }
                        else:
                            status = {
                                'status': 'playing',
                                'level': comp_level,
                            }
                    if status:
                        status['current_level_record'] = {
                            'wins': level_wins,
                            'losses': level_losses,
                            'ties': level_ties
                        } if year != 2015 or comp_level == 'f' else None

        if status:
            status['record'] =  {
                'wins': all_wins,
                'losses': all_losses,
                'ties': all_ties
            } if year != 2015 else None
            status['playoff_average'] = np.mean(playoff_scores) if year == 2015 else None
        return status

    @classmethod
    def _get_alliance(cls, team_key, event_details, matches):
        """
        Get the alliance number of the team
        Returns 0 when the team is not on an alliance
        """
        if event_details and event_details.alliance_selections:
            for i, alliance in enumerate(event_details.alliance_selections):
                alliance_number = i + 1
                if team_key in alliance['picks']:
                    return alliance, alliance_number

                backup_info = alliance.get('backup') if alliance.get('backup') else {}
                if team_key == backup_info.get('in', ""):
                    # If this team came in as a backup team
                    return alliance, alliance_number
        else:
            # No event_details. Use matches to generate alliances.
            complete_alliances = []
            for comp_level in Match.ELIM_LEVELS:
                for match in matches[comp_level]:
                    for color in ['red', 'blue']:
                        alliance = copy.copy(match.alliances[color]['teams'])
                        for i, complete_alliance in enumerate(complete_alliances):  # search for alliance. could be more efficient
                            if len(set(alliance).intersection(set(complete_alliance))) >= 2:  # if >= 2 teams are the same, then the alliance is the same
                                backups = list(set(alliance).difference(set(complete_alliance)))
                                complete_alliances[i] += backups  # ensures that backup robots are listed last
                                break
                        else:
                            complete_alliances.append(alliance)

            for complete_alliance in complete_alliances:
                if team_key in complete_alliance:
                    return {'picks': complete_alliance}, None  # Alliance number is unknown

        alliance_number = 0
        return None, alliance_number  # Team didn't make it to elims

    @classmethod
    def _build_verbose_record(cls, record):
        win_label = 'wins' if record['wins'] != 1 else 'win'
        loss_label = 'losses' if record['losses'] != 1 else 'loss'
        tie_label = 'ties' if record['ties'] != 1 else 'tie'
        return '{} {}, {} {}, and {} {}'.format(
            record['wins'], win_label,
            record['losses'], loss_label,
            record['ties'], tie_label)
