from google.appengine.ext import ndb
from google.appengine.ext.ndb.tasklets import Future

from consts.ranking_indexes import RankingIndexes
from database.match_query import TeamEventMatchesQuery
from helpers.match_helper import MatchHelper
from helpers.team_helper import TeamHelper
from models.event_details import EventDetails


class EventTeamStatusHelper(object):

    @classmethod
    def _build_ranking_info(cls, team_key, event_details):
        if not event_details:
            return None
        year = int(event_details.key_name[0:4])
        rankings = event_details.rankings
        team_num = team_key[3:]
        team_index = next((i for i, row in enumerate(rankings) if row[1] == team_num), None)
        if not team_index:
            return None
        team_line = rankings[team_index]
        total_teams = len(rankings) - 1  # First row is headers, that doesn't count
        rank_headers = rankings[0]
        first_sort = team_line[RankingIndexes.CUMULATIVE_RANKING_SCORE]
        matches_played = team_line[RankingIndexes.MATCHES_PLAYED]
        record = cls._build_record_string(team_line, year)
        breakdown = ", ".join("%s: %s" % tup for tup in zip(rank_headers[1:], team_line[1:]))
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
    def buildEventTeamStatus(cls, live_events, live_eventteams, team_filter):
        # Currently Competing Team Status
        live_events_with_teams = []
        for event, teams in zip(live_events, live_eventteams):
            teams = teams.get_result() if type(teams) == Future else teams
            live_teams_in_district = TeamHelper.sortTeams(filter(lambda t: t in team_filter, teams))

            teams_and_statuses_future = []
            for team in live_teams_in_district:
                teams_and_statuses_future.append([team, EventTeamStatusHelper.generateTeamAtEventStatusAsync(team.key_name, event)])
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
    def _get_playoff_status(cls, team_key, matches, alliance_number):
        """
        Returns a tuple <long status, short status> for the given team
        """
        team_number = team_key[3:]
        level_map = {
            'ef': 'octofinals',
            'qf': 'quarters',
            'sf': 'semis',
            'f': 'the finals',
        }
        for comp_level in ['f', 'sf', 'qf', 'ef']:  # playoffs
            level_str = level_map[comp_level]
            if matches[comp_level]:
                wins = 0
                losses = 0
                for match in matches[comp_level]:
                    if match.has_been_played:
                        if team_key in match.alliances[match.winning_alliance]['teams']:
                            wins += 1
                        else:
                            losses += 1
                if wins == 2:
                    if comp_level == 'f':
                        return "Team {} won the event on alliance #{}.".format(team_number, alliance_number), "Won on alliance #{}".format(alliance_number)
                    else:
                        return "Team {} won {} on alliance #{}.".format(team_number, level_str, alliance_number), "Won {} on alliance #{}".format(level_str, alliance_number)
                elif losses == 2:
                    return "Team {} got knocked out in {} on alliance #{}.".format(team_number, level_str, alliance_number), "Knocked out in {} on alliance #{}".format(level_str, alliance_number)
                else:
                    return "Team {} is currently {}-{} in {} on alliance #{}.".format(team_number, wins, losses, level_str, alliance_number), "Currently {}-{} in {} on alliance #{}".format(wins, losses, level_str, alliance_number)
        return None, None

    @classmethod
    def _get_qual_wlt(cls, team_key, matches):
        """
        Compute record for team
        Returns tuple of <wins, losses, ties, unplayed qual>
        """
        team_number = team_key[3:]
        wins = 0
        losses = 0
        ties = 0
        unplayed_qual = 0
        for match in matches['qm']:
            if match.has_been_played:
                if match.winning_alliance == '':
                    ties += 1
                elif team_key in match.alliances[match.winning_alliance]['teams']:
                    wins += 1
                else:
                    losses += 1
            else:
                unplayed_qual += 1
        return wins, losses, ties, unplayed_qual

    @classmethod
    def _get_rank(cls, team_number, event_details):
        """
        Returns tuple of <team rank, # RP, total num teams>
        Assumes 2016 format
        """
        rank = "?"
        ranking_points = 0
        num_teams = "?"
        record = "0-0-0"
        if event_details and event_details.rankings:
            num_teams = len(event_details.rankings) - 1
            for i, row in enumerate(event_details.rankings):
                if row[1] == team_number:
                    rank = i
                    ranking_points = int(float(row[2]))
                    record = row[7]
                    break
        return rank, ranking_points, record, num_teams

    @classmethod
    @ndb.tasklet
    def generateTeamAtEventStatusAsync(cls, team_key, event):
        """
        Generate Team@Event status items
        :return: a tuple future <long summary string, qual record, qual ranking, playoff status>
        """
        team_number = team_key[3:]
        matches, event_details = yield TeamEventMatchesQuery(team_key, event.key.id()).fetch_async(), EventDetails.get_by_id_async(event.key.id())
        matches = MatchHelper.organizeMatches(matches)

        # Compute alliances
        alliance_number = cls._get_alliance_number(team_key, event_details)

        # Playoff Status
        status, short_playoff_status = cls._get_playoff_status(team_key, matches, alliance_number)

        # Still in quals or team did not make it to elims
        # Compute qual W-L-T
        wins, losses, ties, unplayed_qual = cls._get_qual_wlt(team_key, matches)
        if wins == 0 and losses == 0 and ties == 0:
            # No matches played yet
            status = "Team {} has not played any matches yet.".format(team_number) if not status else status

        # Compute rank & num_teams
        # Gets record from ranking data to account for surrogate matches
        rank, ranking_points, record, num_teams = cls._get_rank(team_number, event_details)
        rank_str = "Rank {} with {} RP".format(rank, ranking_points)

        # Compute final long status for nightbot, if one isn't already there
        if unplayed_qual > 0 and not status:
            if rank is not None:
                status = "Team {} is currently rank {}/{} with a record of {} and {} ranking points.".format(team_number, rank, num_teams, record, ranking_points)
            else:
                status = "Team {} currently has a record of {}.".format(team_number, record)
        elif not status:
            if alliance_number is None:
                status = "Team {} ended qualification matches at rank {}/{} with a record of {}.".format(team_number, rank, num_teams, record)
            elif alliance_number == 0:
                status = "Team {} ended qualification matches at rank {}/{} with a record of {} and was not picked for playoff matches.".format(team_number, rank, num_teams, record)
            else:
                status = "Team {} will be competing in the playoff matches on alliance #{}.".format(team_number, alliance_number)

        raise ndb.Return(status, record, rank_str, short_playoff_status)
