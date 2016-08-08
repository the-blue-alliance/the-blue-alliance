import cloudstorage
import csv
import datetime
import json
import logging
import os
import StringIO
import tba_config

from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from helpers.award_manipulator import AwardManipulator
from helpers.event_manipulator import EventManipulator
from helpers.event_details_manipulator import EventDetailsManipulator
from helpers.match_manipulator import MatchManipulator

from models.award import Award
from models.event import Event
from models.event_details import EventDetails
from models.match import Match
from models.team import Team

from datafeeds.csv_alliance_selections_parser import CSVAllianceSelectionsParser
from datafeeds.csv_awards_parser import CSVAwardsParser
from datafeeds.offseason_matches_parser import OffseasonMatchesParser


class TbaCSVBackupEventsEnqueue(webapp.RequestHandler):
    """
    Enqueues CSV backup
    """
    def get(self, year=None):
        if year is None:
            years = range(1992, datetime.datetime.now().year + 1)
            for y in years:
                taskqueue.add(
                    url='/tasks/enqueue/csv_backup_events/{}'.format(y),
                    method='GET')
            self.response.out.write("Enqueued backup for years: {}".format(years))
        else:
            event_keys = Event.query(Event.year == int(year)).fetch(None, keys_only=True)

            for event_key in event_keys:
                taskqueue.add(
                    url='/tasks/do/csv_backup_event/{}'.format(event_key.id()),
                    method='GET')

            template_values = {'event_keys': event_keys}
            path = os.path.join(os.path.dirname(__file__), '../templates/backup/csv_backup_enqueue.html')
            self.response.out.write(template.render(path, template_values))


class TbaCSVBackupEventDo(webapp.RequestHandler):
    """
    Backs up event awards, matches, team list, rankings, and alliance selection order
    """

    AWARDS_FILENAME_PATTERN = '/tbatv-prod-hrd.appspot.com/tba-data-backup/events/{}/{}/{}_awards.csv'  # % (year, event_key, event_key)
    MATCHES_FILENAME_PATTERN = '/tbatv-prod-hrd.appspot.com/tba-data-backup/events/{}/{}/{}_matches.csv'  # % (year, event_key, event_key)
    TEAMS_FILENAME_PATTERN = '/tbatv-prod-hrd.appspot.com/tba-data-backup/events/{}/{}/{}_teams.csv'  # % (year, event_key, event_key)
    RANKINGS_FILENAME_PATTERN = '/tbatv-prod-hrd.appspot.com/tba-data-backup/events/{}/{}/{}_rankings.csv'  # % (year, event_key, event_key)
    ALLIANCES_FILENAME_PATTERN = '/tbatv-prod-hrd.appspot.com/tba-data-backup/events/{}/{}/{}_alliances.csv'  # % (year, event_key, event_key)

    def get(self, event_key):
        event = Event.get_by_id(event_key)

        event.prepAwardsMatchesTeams()

        if event.awards:
            with cloudstorage.open(self.AWARDS_FILENAME_PATTERN.format(event.year, event_key, event_key), 'w') as awards_file:
                writer = csv.writer(awards_file, delimiter=',')
                for award in event.awards:
                    for recipient in award.recipient_list:
                        team = recipient['team_number']
                        if type(team) == int:
                            team = 'frc{}'.format(team)
                        self._writerow_unicode(writer, [award.key.id(), award.name_str, team, recipient['awardee']])

        if event.matches:
            with cloudstorage.open(self.MATCHES_FILENAME_PATTERN.format(event.year, event_key, event_key), 'w') as matches_file:
                writer = csv.writer(matches_file, delimiter=',')
                for match in event.matches:
                    red_score = match.alliances['red']['score']
                    blue_score = match.alliances['blue']['score']
                    self._writerow_unicode(writer, [match.key.id()] + match.alliances['red']['teams'] + match.alliances['blue']['teams'] + [red_score, blue_score])

        if event.teams:
            with cloudstorage.open(self.TEAMS_FILENAME_PATTERN.format(event.year, event_key, event_key), 'w') as teams_file:
                writer = csv.writer(teams_file, delimiter=',')
                self._writerow_unicode(writer, [team.key.id() for team in event.teams])

        if event.rankings:
            with cloudstorage.open(self.RANKINGS_FILENAME_PATTERN.format(event.year, event_key, event_key), 'w') as rankings_file:
                writer = csv.writer(rankings_file, delimiter=',')
                for row in event.rankings:
                    self._writerow_unicode(writer, row)

        if event.alliance_selections:
            with cloudstorage.open(self.ALLIANCES_FILENAME_PATTERN.format(event.year, event_key, event_key), 'w') as alliances_file:
                writer = csv.writer(alliances_file, delimiter=',')
                for alliance in event.alliance_selections:
                    self._writerow_unicode(writer, alliance['picks'])

        self.response.out.write("Done backing up {}!".format(event_key))

    def _writerow_unicode(self, writer, row):
        unicode_row = []
        for s in row:
            try:
                unicode_row.append(s.encode("utf-8"))
            except:
                unicode_row.append(s)
        writer.writerow(unicode_row)


class TbaCSVRestoreEventsEnqueue(webapp.RequestHandler):
    """
    Enqueues CSV restore
    """
    def get(self, year=None):
        if tba_config.CONFIG["env"] == "prod":  # disable in prod for now
            logging.error("Tried to restore events from CSV for year {} in prod! No can do.".format(year))
            return

        if year is None:
            years = range(1992, datetime.datetime.now().year + 1)
            for y in years:
                taskqueue.add(
                    url='/tasks/enqueue/csv_restore_events/{}'.format(y),
                    method='GET')
            self.response.out.write("Enqueued restore for years: {}".format(years))
        else:
            event_keys = Event.query(Event.year == int(year)).fetch(None, keys_only=True)

            for event_key in event_keys:
                taskqueue.add(
                    url='/tasks/do/csv_restore_event/{}'.format(event_key.id()),
                    method='GET')

            template_values = {'event_keys': event_keys}
            path = os.path.join(os.path.dirname(__file__), '../templates/backup/csv_restore_enqueue.html')
            self.response.out.write(template.render(path, template_values))


class TbaCSVRestoreEventDo(webapp.RequestHandler):
    """
    Restores event awards, matches, team list, rankings, and alliance selection order
    """

    BASE_URL = 'https://raw.githubusercontent.com/the-blue-alliance/tba-data-backup/master/events/{}/{}/'  # % (year, event_key)
    ALLIANCES_URL = BASE_URL + '{}_alliances.csv'  # % (year, event_key, event_key)
    AWARDS_URL = BASE_URL + '{}_awards.csv'  # % (year, event_key, event_key)
    MATCHES_URL = BASE_URL + '{}_matches.csv'  # % (year, event_key, event_key)
    RANKINGS_URL = BASE_URL + '{}_rankings.csv'  # % (year, event_key, event_key)
    # TEAMS_URL = BASE_URL + '{}_teams.csv'  # % (year, event_key, event_key)  # currently unused

    def get(self, event_key):
        if tba_config.CONFIG["env"] == "prod":  # disable in prod for now
            logging.error("Tried to restore {} from CSV in prod! No can do.".format(event_key))
            return

        event = Event.get_by_id(event_key)

        # alliances
        result = urlfetch.fetch(self.ALLIANCES_URL.format(event.year, event_key, event_key))
        if result.status_code != 200:
            logging.warning('Unable to retreive url: ' + (self.ALLIANCES_URL.format(event.year, event_key, event_key)))
        else:
            data = result.content.replace('frc', '')
            alliance_selections = CSVAllianceSelectionsParser.parse(data)
            if alliance_selections and event.alliance_selections != alliance_selections:
                event.alliance_selections_json = json.dumps(alliance_selections)
                event._alliance_selections = None
                event.dirty = True
            EventManipulator.createOrUpdate(event)

            event_details = EventDetails(
                id=event_key,
                parent=event.key,
                alliance_selections=alliance_selections
            )
            EventDetailsManipulator.createOrUpdate(event_details)

        # awards
        result = urlfetch.fetch(self.AWARDS_URL.format(event.year, event_key, event_key))
        if result.status_code != 200:
            logging.warning('Unable to retreive url: ' + (self.AWARDS_URL.format(event.year, event_key, event_key)))
        else:
            # convert into expected input format
            data = StringIO.StringIO()
            writer = csv.writer(data, delimiter=',')
            for row in csv.reader(StringIO.StringIO(result.content), delimiter=','):
                writer.writerow([event.year, event.event_short, row[1], row[2].replace('frc', ''), row[3]])

            awards = []
            for award in CSVAwardsParser.parse(data.getvalue()):
                awards.append(Award(
                    id=Award.render_key_name(event.key_name, award['award_type_enum']),
                    name_str=award['name_str'],
                    award_type_enum=award['award_type_enum'],
                    year=event.year,
                    event=event.key,
                    event_type_enum=event.event_type_enum,
                    team_list=[ndb.Key(Team, 'frc{}'.format(team_number)) for team_number in award['team_number_list']],
                    recipient_json_list=award['recipient_json_list']
                ))
            AwardManipulator.createOrUpdate(awards)

        # matches
        result = urlfetch.fetch(self.MATCHES_URL.format(event.year, event_key, event_key))
        if result.status_code != 200:
            logging.warning('Unable to retreive url: ' + (self.MATCHES_URL.format(event.year, event_key, event_key)))
        else:
            data = result.content.replace('frc', '').replace('{}_'.format(event_key), '')
            match_dicts, _ = OffseasonMatchesParser.parse(data)
            matches = [
                Match(
                    id=Match.renderKeyName(
                        event.key.id(),
                        match.get("comp_level", None),
                        match.get("set_number", 0),
                        match.get("match_number", 0)),
                    event=event.key,
                    year=event.year,
                    set_number=match.get("set_number", 0),
                    match_number=match.get("match_number", 0),
                    comp_level=match.get("comp_level", None),
                    team_key_names=match.get("team_key_names", None),
                    alliances_json=match.get("alliances_json", None)
                )
            for match in match_dicts]
            MatchManipulator.createOrUpdate(matches)

        # rankings
        result = urlfetch.fetch(self.RANKINGS_URL.format(event.year, event_key, event_key))
        if result.status_code != 200:
            logging.warning('Unable to retreive url: ' + (self.RANKINGS_URL.format(event.year, event_key, event_key)))
        else:
            # convert into expected input format
            rankings = list(csv.reader(StringIO.StringIO(result.content), delimiter=','))
            if rankings and event.rankings != rankings:
                event.rankings_json = json.dumps(rankings)
                event._rankings = None
                event.dirty = True
            EventManipulator.createOrUpdate(event)

            event_details = EventDetails(
                id=event_key,
                parent=event.key,
                rankings=rankings
            )
            EventDetailsManipulator.createOrUpdate(event_details)

        self.response.out.write("Done restoring {}!".format(event_key))


class TbaCSVBackupTeamsEnqueue(webapp.RequestHandler):
    """
    Enqueues CSV teams backup
    """
    def get(self):
        taskqueue.add(
            url='/tasks/do/csv_backup_teams',
            method='GET')
        self.response.out.write("Enqueued CSV teams backup")


class TbaCSVBackupTeamsDo(webapp.RequestHandler):
    """
    Backs up teams
    """
    TEAMS_FILENAME_PATTERN = '/tbatv-prod-hrd.appspot.com/tba-data-backup/teams/teams.csv'

    def get(self):
        team_keys = Team.query().order(Team.team_number).fetch(None, keys_only=True)
        team_futures = ndb.get_multi_async(team_keys)

        if team_futures:
            with cloudstorage.open(self.TEAMS_FILENAME_PATTERN, 'w') as teams_file:
                writer = csv.writer(teams_file, delimiter=',')
                for team_future in team_futures:
                    team = team_future.get_result()
                    self._writerow_unicode(writer, [team.key.id(), team.nickname, team.name, team.city, team.state_prov, team.country, team.website, team.rookie_year])

        self.response.out.write("Done backing up teams!")

    def _writerow_unicode(self, writer, row):
        unicode_row = []
        for s in row:
            try:
                unicode_row.append(s.encode("utf-8"))
            except:
                unicode_row.append(s)
        writer.writerow(unicode_row)
