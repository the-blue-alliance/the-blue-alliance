from google.appengine.ext import ndb
from google.appengine.ext.ndb.tasklets import Future

from consts.ranking_indexes import RankingIndexes
from database.match_query import EventMatchesQuery
from helpers.match_helper import MatchHelper
from helpers.team_helper import TeamHelper
from models.event_details import EventDetails
from models.match import Match


class EventTeamStatusHelper(object):

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
            matches = [match for match in matches if match.comp_level in Match.ELIM_LEVELS]
            matches = MatchHelper.organizeMatches(matches)
        return {
            'rank': cls._build_ranking_info(team_key, event_details),
            'alliance': cls._build_alliance_info(team_key, event_details),
            'playoff': cls._build_playoff_status(team_key, event_details, matches)
        }

    @classmethod
    def _build_ranking_info(cls, team_key, event_details):
        if not event_details:
            return None
        rankings = event_details.rankings
        if not rankings:
            return None
        team_num = int(team_key[3:])
        team_index = next((row[0] for row in rankings if row[1] == team_num), None)
        if not team_index:
            return None
        team_line = rankings[team_index]
        total_teams = len(rankings) - 1  # First row is headers, that doesn't count
        rank_headers = rankings[0]
        year = int(event_details.key.id()[:4])
        first_sort = team_line[RankingIndexes.CUMULATIVE_RANKING_SCORE[year]]
        matches_played = team_line[RankingIndexes.MATCHES_PLAYED[year]]
        record = cls._build_record_string(team_line, year)
        breakdown = ", ".join("%s: %s" % tup for tup in zip(rank_headers[2:], team_line[2:]))
        # ^ a little python magic to automagically build comma-separated key/value pairs for breakdowns, but w/o team #
        return {
            'rank': team_index,
            'total': total_teams,
            'played': matches_played,
            'first_sort': first_sort,
            'record': record,
            'breakdown': breakdown
        }

    @classmethod
    def _build_alliance_info(cls, team_key, event_details):
        if not event_details or not event_details.alliance_selections:
            return None
        alliance, number = cls._get_alliance(team_key, event_details)
        if not alliance:
            return None

        # Calculate the role played by the team on the alliance
        backup_info = alliance.get('backup', {}) if alliance.get('backup') else {}
        position = -1 if team_key == backup_info.get('in', "") else None
        for i, team in enumerate(alliance['picks']):
            if team == team_key:
                position = i
                break

        return {
            'position': position,
            'name': alliance.get('name', "Alliance {}".format(number)),
            'backup': alliance.get('backup'),
        }

    @classmethod
    def _build_playoff_status(cls, team_key, event_details, matches):
        # Matches needs to be all playoff matches at the event, to properly account for backups
        alliance, alliance_number = cls._get_alliance(team_key, event_details)
        complete_alliance = set(alliance['picks']) if alliance else set()
        if alliance and alliance.get('backup'):
            complete_alliance.add(alliance['backup']['in'])

        all_wins = 0
        all_losses = 0
        all_ties = 0
        status = None
        for comp_level in ['f', 'sf', 'qf', 'ef']:  # playoffs
            if matches[comp_level]:
                level_wins = 0
                level_losses = 0
                level_ties = 0
                level_matches = 0
                for match in matches[comp_level]:
                    if match.has_been_played:
                        for color in ['red', 'blue']:
                            match_alliance = set(match.alliances[color]['teams'])
                            if len(match_alliance.intersection(complete_alliance)) >= 2:
                                level_matches += 1
                                if match.winning_alliance == color:
                                    level_wins += 1
                                    all_wins += 1
                                elif not match.winning_alliance:
                                    # The match was a tie
                                    level_ties += 1
                                    all_ties += 1
                                else:
                                    level_losses += 1
                                    all_losses += 1
                if status:
                    # Only set this for the first comp level that gets this far,
                    # But run through the rest to calculate the full record
                    continue
                if level_wins == 2:
                    status = {
                        'status': 'won',
                        'level': comp_level,
                    }
                elif level_losses == 2:
                    status ={
                        'status': 'eliminated',
                        'level': comp_level
                    }
                elif level_matches > 0:
                    status = {
                        'status': 'playing',
                        'level': comp_level,
                        'current_level_record': "{}-{}-{}".format(level_wins, level_losses, level_ties)
                    }
        if status:
            status['record'] = "{}-{}-{}".format(all_wins, all_losses, all_ties)
        return status

    @classmethod
    def _build_record_string(cls, ranking_row, year):
        indexes = RankingIndexes.RECORD_INDEXES[year]
        if not indexes:
            return None
        if isinstance(indexes, tuple):
            # The item is the indexes of (wins, losses, ties)
            return "{}-{}-{}".format(ranking_row[indexes[0]], ranking_row[indexes[1]], ranking_row[indexes[2]])
        elif isinstance(indexes, int):
            return ranking_row[indexes]
        else:
            return None

    @classmethod
    def _get_alliance(cls, team_key, event_details):
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

        alliance_number = 0
        return None, alliance_number  # Team didn't make it to elims

    @classmethod
    def buildEventTeamStatus(cls, live_events, live_eventteams, team_filter):
        # Currently Competing Team Status
        live_events_with_teams = []
        for event, teams in zip(live_events, live_eventteams):
            teams = teams.get_result() if type(teams) == Future else teams
            live_teams_in_district = TeamHelper.sortTeams(filter(lambda t: t in team_filter, teams))

            teams_and_statuses_future = []
            for team in live_teams_in_district:
                teams_and_statuses_future.append([team, cls.generateTeamAtEventStatusAsync(team.key_name, event)])
            if teams_and_statuses_future:
                live_events_with_teams.append((event, teams_and_statuses_future))

        return live_events_with_teams

    @classmethod
    def _get_alliance_number(cls, team_key, event_details):
        """
        Get the alliance number of the team
        Returns 0 when the team is not on an alliance
        """
        alliance_number = None
        if event_details and event_details.alliance_selections:
            for i, alliance in enumerate(event_details.alliance_selections):
                if team_key in alliance['picks']:
                    alliance_number = i + 1
                    break
            else:
                alliance_number = 0  # Team didn't make it to elims
        return alliance_number

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
        # We need all the event's playoff matches here to properly account for backup teams
        matches, event_details = yield EventMatchesQuery(event.key.id()).fetch_async(), EventDetails.get_by_id_async(event.key.id())
        qual_match_count = 0
        playoff_match_count = 0
        playoff_matches = []
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
