import cloudstorage
import csv
import os

from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from models.award import Award
from models.event import Event
from models.match import Match


class TbaCSVBackupEnqueue(webapp.RequestHandler):
    """
    Enqueues CSV backup
    """
    def get(self, year=None):
        if year is None:
            event_keys = Event.query().fetch(None, keys_only=True)
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

    AWARDS_FILENAME_PATTERN = '/tbatv-prod-hrd.appspot.com/tba-data-backup/{}/{}/{}_awards.csv'  # % (year, event_key, event_key)
    MATCHES_FILENAME_PATTERN = '/tbatv-prod-hrd.appspot.com/tba-data-backup/{}/{}/{}_matches.csv'  # % (year, event_key, event_key)
    TEAMS_FILENAME_PATTERN = '/tbatv-prod-hrd.appspot.com/tba-data-backup/{}/{}/{}_teams.csv'  # % (year, event_key, event_key)
    RANKINGS_FILENAME_PATTERN = '/tbatv-prod-hrd.appspot.com/tba-data-backup/{}/{}/{}_rankings.csv'  # % (year, event_key, event_key)
    ALLIANCES_FILENAME_PATTERN = '/tbatv-prod-hrd.appspot.com/tba-data-backup/{}/{}/{}_alliances.csv'  # % (year, event_key, event_key)

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
