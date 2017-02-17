import copy
import numpy as np

from google.appengine.ext import ndb
from google.appengine.ext.ndb.tasklets import Future

from helpers.match_helper import MatchHelper
from helpers.rankings_helper import RankingsHelper
from helpers.team_helper import TeamHelper
from models.event_details import EventDetails
from models.match import Match


class EventTeamStatusHelper(object):
    @classmethod
    def generate_team_at_event_status_string(cls, team_key, status):
        """
        Generate a team at event status string from a status dict
        """
        qual = status.get('qual')
        alliance = status.get('alliance')
        playoff = status.get('playoff')

        components = []
        if qual:
            rank = qual.get('rank')
            max_rank = qual.get('max_rank')
            record = qual.get('record')
            qual_average = qual.get('qual_average')

            max_rank_str = ''
            if max_rank:
                max_rank_str = '/{}'.format(max_rank)

            qual_str = None
            if record:
                record_str = '{}-{}-{}'.format(record['wins'], record['losses'], record['ties'])
                if rank:
                    qual_str = 'was <b>Rank {}{}</b> with a record of <b>{}</b> in quals'.format(rank, max_rank_str, record_str)
                else:
                    qual_str = 'had a record of <b>{}</b> in quals'.format(record_str)
            elif qual_average:
                if rank:
                    qual_str = 'was <b>Rank {}{}</b> with an average score of <b>{:.1f}</b> in quals'.format(rank, max_rank_str, qual_average)
                else:
                    qual_str = 'had an average score of <b>{:.1f}</b> in quals'.format(qual_average)

            if qual_str:
                components.append(qual_str)

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
            alliance_str = 'competed in the playoffs as the <b>{}</b> on <b>{}</b>'.format(pick, alliance['name'])
            components.append(alliance_str)

        if playoff:
            level = playoff.get('level')
            status = playoff.get('status')
            record = playoff.get('record')
            playoff_average = playoff.get('playoff_average')

            playoff_str = None
            if status == 'won':
                if level == 'f':
                    playoff_str = '<b>won the event</b>'
                else:
                    playoff_str = '<b>won the {}</b>'.format(Match.COMP_LEVELS_VERBOSE_FULL[level])
            elif status == 'competing':
                playoff_str = 'is <b>competing in the {}</b>'.format(Match.COMP_LEVELS_VERBOSE_FULL[level])
            elif status == 'eliminated':
                playoff_str = 'was <b>eliminated in the {}</b>'.format(Match.COMP_LEVELS_VERBOSE_FULL[level])

            if record:
                record_str = '{}-{}-{}'.format(record['wins'], record['losses'], record['ties'])
                if status == 'competing':
                    playoff_str += ' and is currently <b>{}</b>'.format(record_str)
                else:
                    playoff_str += ' with a playoff record of <b>{}</b>'.format(record_str)
            elif playoff_average:
                playoff_str += ' with a playoff average of <b>{:.1f}</b>'.format(playoff_average)

            if playoff_str:
                components.append(playoff_str)

        if not components:
            return None

        team_str = 'Team {}'.format(team_key[3:])
        if len(components) > 1:
            components[-1] = 'and {}'.format(components[-1])
        if len(components) > 2:
            join_str = ', '
        else:
            join_str = ' '

        return '{} {}.'.format(team_str, join_str.join(components))

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
            matches = MatchHelper.organizeMatches(matches)
        return copy.deepcopy({
            'qual': cls._build_qual_info(team_key, event_details, matches, event.year),
            'alliance': cls._build_alliance_info(team_key, event_details, matches),
            'playoff': cls._build_playoff_info(team_key, event_details, matches, event.year)
        })  # TODO: Results are getting mixed unless copied. 2017-02-03 -fangeugene

    @classmethod
    def _build_qual_info(cls, team_key, event_details, matches, year):
        if not matches['qm']:
            status = 'not_started'
        else:
            status = 'complete'
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
                        'rank': ranking['rank'],
                        'matches_played': ranking['matches_played'],
                        'dq': ranking['dq'],
                        'record': ranking['record'],
                        'qual_average': ranking['qual_average'],
                    }
                    break

            if qual_info:
                qual_info['max_rank'] = len(rankings)
                qual_info['ranking_sort_orders'] = RankingsHelper.get_sort_order_info(event_details)
                for info, value in zip(qual_info['ranking_sort_orders'], ranking['sort_orders']):
                    info['value'] = value

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
                    'rank': None,
                    'matches_played': matches_played,
                    'dq': None,
                    'record': {
                        'wins': wins,
                        'losses': losses,
                        'ties': ties,
                    } if year != 2015 else None,
                    'qual_average': qual_average if year == 2015 else None,
                    'max_rank': len(all_teams),
                    'ranking_sort_orders': None,
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
    def _build_playoff_info(cls, team_key, event_details, matches, year):
        # Matches needs to be all playoff matches at the event, to properly account for backups
        alliance, _ = cls._get_alliance(team_key, event_details, matches)
        complete_alliance = set(alliance['picks']) if alliance else set()
        if alliance and alliance.get('backup'):
            complete_alliance.add(alliance['backup']['in'])

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
                    if match.has_been_played:
                        for color in ['red', 'blue']:
                            match_alliance = set(match.alliances[color]['teams'])
                            if len(match_alliance.intersection(complete_alliance)) >= 2:
                                playoff_scores.append(match.alliances[color]['score'])
                                level_matches += 1
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
                                if match.has_been_played:
                                    level_played += 1
                if not status:
                    # Only set this for the first comp level that gets this far,
                    # But run through the rest to calculate the full record
                    if level_wins == 2:
                        status = {
                            'status': 'won',
                            'level': comp_level,
                        }
                    elif level_losses == 2:
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
    def buildEventTeamStatus(cls, events, eventteams, team_filter):
        # Currently Competing Team Status
        for event in events:
            event.prep_details()  # Prepare details for later
            event.prep_matches()  # Prepare matches for later

        events_with_teams = []
        for event, teams in zip(events, eventteams):
            teams = teams.get_result() if type(teams) == Future else teams
            live_teams_in_filter = TeamHelper.sortTeams(filter(lambda t: t in team_filter, teams))

            teams_and_statuses_future = []
            for team in live_teams_in_filter:
                teams_and_statuses_future.append([team, cls.generateTeamAtEventStatusAsync(team.key_name, event)])
            if teams_and_statuses_future:
                events_with_teams.append((event, teams_and_statuses_future))

        return events_with_teams

    @classmethod
    def _get_playoff_status_string(cls, team_key, alliance_status, playoff_status):
        """
        Returns a tuple <long status, short status> for the given team
        """
        if not playoff_status or not alliance_status:
            return None, None
        team_number = team_key[3:]
        alliance_name = alliance_status['name']
        level_map = {
            'ef': 'octofinals',
            'qf': 'quarters',
            'sf': 'semis',
            'f': 'the finals',
        }
        level_str = level_map[playoff_status['level']]
        if playoff_status['status'] == 'won':
            if playoff_status['level'] == 'f':
                return "Team {} won the event on {}.".format(team_number, alliance_name), "Won on {}".format(alliance_name)
            else:
                return "Team {} won {} on {}.".format(team_number, level_str, alliance_name), "Won {} on {}".format(level_str, alliance_name)
        elif playoff_status['status'] == 'eliminated':
            return "Team {} got knocked out in {} on {}.".format(team_number, level_str, alliance_name), "Knocked out in {} on {}".format(level_str, alliance_name)
        else:
            return "Team {} is currently {} in {} on {}.".format(team_number, playoff_status['current_level_record'], level_str, alliance_name), "Currently {} in {} on {}".format(playoff_status['current_level_record'], level_str, alliance_name)

    @classmethod
    @ndb.tasklet
    def generateTeamAtEventStatusAsync(cls, team_key, event):
        """
        Generate Team@Event status items
        :return: a tuple future <long summary string, qual record, qual ranking, playoff status>
        """
        team_number = team_key[3:]
        event.prep_details()
        # We need all the event's playoff matches here to properly account for backup teams
        event.prep_matches()
        qual_match_count = 0
        playoff_match_count = 0
        playoff_matches = []
        matches = event.matches
        for match in matches:
            if match.comp_level in Match.ELIM_LEVELS:
                playoff_match_count += 1
                playoff_matches.append(match)
            else:
                qual_match_count += 1
        matches = MatchHelper.organizeMatches(playoff_matches)

        team_status = cls.generate_team_at_event_status(team_key, event, matches)
        rank_status = team_status.get('rank', None)
        alliance_status = team_status.get('alliance', None)
        playoff_status = team_status.get('playoff', None)

        # Playoff Status
        status, short_playoff_status = cls._get_playoff_status_string(team_key, alliance_status, playoff_status)

        # Still in quals or team did not make it to elims
        if not rank_status or rank_status.get('played', 0) == 0:
            # No matches played yet
            status = "Team {} has not played any matches yet.".format(team_number) if not status else status
            record = '?'
            rank_str = '?'
        else:
            # Compute rank & num_teams
            # Gets record from ranking data to account for surrogate matches
            rank = rank_status.get('rank', '?')
            ranking_points = rank_status.get('first_sort', '?')
            record = rank_status.get('record', '?')
            num_teams = rank_status.get('total', '?')
            rank_str = "Rank {} with {} RP".format(rank, ranking_points)
            alliance_name = alliance_status.get('name', '?') if alliance_status else '?'

            # Compute final long status for nightbot, if one isn't already there
            matches_per_team = qual_match_count // rank_status.get('total', 1)
            if rank_status.get('played', 0) - matches_per_team > 0 and not status:
                if rank is not None:
                    status = "Team {} is currently rank {}/{} with a record of {} and {} ranking points.".format(team_number, rank, num_teams, record, ranking_points)
                else:
                    status = "Team {} currently has a record of {}.".format(team_number, record)
            elif not status:
                if alliance_status is None and playoff_match_count == 0:
                    status = "Team {} ended qualification matches at rank {}/{} with a record of {}.".format(team_number, rank, num_teams, record)
                elif alliance_status is None and playoff_match_count > 0:
                    status = "Team {} ended qualification matches at rank {}/{} with a record of {} and was not picked for playoff matches.".format(team_number, rank, num_teams, record)
                else:
                    status = "Team {} will be competing in the playoff matches on {}.".format(team_number, alliance_name)

        raise ndb.Return(status, record, rank_str, short_playoff_status)
