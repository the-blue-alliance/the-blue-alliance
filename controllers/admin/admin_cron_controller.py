from collections import defaultdict
from datetime import date, datetime, timedelta
import json
import logging
import os
import re

from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from consts.award_type import AwardType
from consts.client_type import ClientType
from consts.district_type import DistrictType
from consts.event_type import EventType
from controllers.base_controller import LoggedInHandler
from database import match_query
from helpers.award_manipulator import AwardManipulator
from helpers.district_team_manipulator import DistrictTeamManipulator
from helpers.match_helper import MatchHelper
from helpers.notification_sender import NotificationSender
from models.award import Award
from models.district_team import DistrictTeam
from models.event import Event
from models.event_team import EventTeam
from models.mobile_client import MobileClient
from models.sitevar import Sitevar
from models.subscription import Subscription
from models.team import Team
from notifications.ping import PingNotification


class AdminMobileClearEnqueue(LoggedInHandler):
    """
    Clears mobile clients with duplicate client_ids
    Will leave the most recently updated one
    """
    def get(self):
        self._require_admin()
        taskqueue.add(
            queue_name='admin',
            url='/tasks/admin/clear_mobile_duplicates',
            method='GET')

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/mobile_clear_enqueue.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminMobileClear(LoggedInHandler):
    """
    Fetch all mobile clients, order by messaging ID, then update time (desc).
    If the current client has the same ID as the last one (which is always going to be newer), mark the current one to be removed
    """
    def get(self):
        clients = MobileClient.query().fetch()
        clients = sorted(clients, key=lambda x: (x.messaging_id, x.updated))
        last = None
        to_remove = []
        last = None
        for client in clients:
            if last is not None and client.messaging_id == last.messaging_id:
                logging.info("Removing")
                to_remove.append(client.key)
            last = client
        count = len(to_remove)
        if to_remove:
            ndb.delete_multi(to_remove)
        logging.info("Removed {} duplicate mobile clients".format(count))
        template_values = {'count': count}
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/mobile_clear_do.html')
        self.response.out.write(template.render(path, template_values))


class AdminSubsClearEnqueue(LoggedInHandler):
    """
    Removes subscriptions to past years' things
    """
    def get(self):
        self._require_admin()
        taskqueue.add(
            queue_name='admin',
            url='/tasks/admin/clear_old_subs',
            method='GET')

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/subs_clear_enqueue.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminSubsClear(LoggedInHandler):
    def get(self):
        year = date.today().year - 1
        # Compile key regex
        # Matches event (2014ctgro), team@event (frc2014_2014ctgro), firehose (2014*)
        ps = "^{}[a-z]+|_{}[a-z]+|{}\*$".format(year, year, year)
        logging.info("Pattern: {}".format(ps))
        p = re.compile(ps)

        subs = Subscription.query().fetch()
        to_delete = []
        for sub in subs:
            if p.match(sub.model_key):
                to_delete.append(sub.key)
        count = len(to_delete)
        if to_delete:
            ndb.delete_multi(to_delete)
        logging.info("Removed {} old subscriptions".format(count))
        template_values = {'count': count}
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/subs_clear_do.html')
        self.response.out.write(template.render(path, template_values))


class AdminWebhooksClearEnqueue(LoggedInHandler):
    """
    Tries to ping every webhook and removes ones that don't respond
    """
    def get(self):
        self._require_admin()
        taskqueue.add(
            queue_name='admin',
            url='/tasks/admin/clear_old_webhooks',
            method='GET')

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/webhooks_clear_enqueue.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminWebhooksClear(LoggedInHandler):
    def get(self):
        webhooks = MobileClient.query(MobileClient.client_type == ClientType.WEBHOOK).fetch()
        failures = []

        notification = PingNotification()._render_webhook()

        for key in webhooks:
            if not NotificationSender.send_webhook(notification, [(key.messaging_id, key.secret)]):
                failures.append(key.key)

        count = len(failures)
        if failures:
            ndb.delete_multi(failures)
        logging.info("Deleted {} broken webhooks".format(count))

        template_values = {'count': count}
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/webhooks_clear_do.html')
        self.response.out.write(template.render(path, template_values))


class AdminCreateDistrictTeamsEnqueue(LoggedInHandler):
    """
    Trying to Enqueue a task to rebuild old district teams from event teams.
    """
    def get(self, year):
        self._require_admin()
        taskqueue.add(
            queue_name='admin',
            target='backend-tasks',
            url='/backend-tasks/do/rebuild_district_teams/{}'.format(year),
            method='GET')

        self.response.out.write("Enqueued district teams for {}".format(year))


class AdminCreateDistrictTeamsDo(LoggedInHandler):
    def get(self, year):
        year = int(year)
        team_districts = defaultdict(list)
        logging.info("Fetching events in {}".format(year))
        year_events = Event.query(year == Event.year, Event.event_district_enum != DistrictType.NO_DISTRICT, Event.event_district_enum != None).fetch()
        for event in year_events:
            logging.info("Fetching EventTeams for {}".format(event.key_name))
            event_teams = EventTeam.query(EventTeam.event == event.key).fetch()
            for event_team in event_teams:
                team_districts[event_team.team.id()].append(event.event_district_enum)

        new_district_teams = []
        for team_key, districts in team_districts.iteritems():
            most_frequent_district = max(set(districts), key=districts.count)
            logging.info("Assuming team {} belongs to {}".format(team_key, DistrictType.type_names[most_frequent_district]))
            dt_key = DistrictTeam.renderKeyName(year, most_frequent_district, team_key)
            new_district_teams.append(DistrictTeam(id=dt_key, year=year, team=ndb.Key(Team, team_key), district=most_frequent_district))

        logging.info("Finishing updating old district teams from event teams")
        DistrictTeamManipulator.createOrUpdate(new_district_teams)
        self.response.out.write("Finished creating district teams for {}".format(year))


class AdminPostEventTasksDo(LoggedInHandler):
    """
    Runs cleanup tasks after an event is over if necessary
    """
    def get(self, event_key):
        # Fetch for later
        event_future = Event.get_by_id_async(event_key)
        matches_future = match_query.EventMatchesQuery(event_key).fetch_async()

        # Rebuild event teams
        taskqueue.add(
            url='/tasks/math/do/eventteam_update/' + event_key,
            method='GET')

        # Create Winner/Finalist awards for offseason events
        awards = []
        event = event_future.get_result()
        if event.event_type_enum == EventType.OFFSEASON:
            matches = MatchHelper.organizeMatches(matches_future.get_result())
            bracket = MatchHelper.generateBracket(matches, event.alliance_selections)
            if 'f' in bracket:
                winning_alliance = '{}_alliance'.format(bracket['f'][1]['winning_alliance'])
                if winning_alliance == 'red_alliance':
                    losing_alliance = 'blue_alliance'
                else:
                    losing_alliance = 'red_alliance'

                awards.append(Award(
                    id=Award.render_key_name(event.key_name, AwardType.WINNER),
                    name_str="Winner",
                    award_type_enum=AwardType.WINNER,
                    year=event.year,
                    event=event.key,
                    event_type_enum=event.event_type_enum,
                    team_list=[ndb.Key(Team, 'frc{}'.format(team)) for team in bracket['f'][1][winning_alliance] if team.isdigit()],
                    recipient_json_list=[json.dumps({'team_number': team, 'awardee': None}) for team in bracket['f'][1][winning_alliance]],
                ))

                awards.append(Award(
                    id=Award.render_key_name(event.key_name, AwardType.FINALIST),
                    name_str="Finalist",
                    award_type_enum=AwardType.FINALIST,
                    year=event.year,
                    event=event.key,
                    event_type_enum=event.event_type_enum,
                    team_list=[ndb.Key(Team, 'frc{}'.format(team)) for team in bracket['f'][1][losing_alliance] if team.isdigit()],
                    recipient_json_list=[json.dumps({'team_number': team, 'awardee': None}) for team in bracket['f'][1][losing_alliance]],
                ))
                AwardManipulator.createOrUpdate(awards)

        self.response.out.write("Finished post-event tasks for {}. Created awards: {}".format(event_key, awards))


class AdminRegistrationDayEnqueue(LoggedInHandler):
    def post(self):
        """
        Configures scheduling a registration day in advance
        This will enqueue the requested year's event details task every X minutes
        Also updates the "short cache" sitevar to reduce timeouts for that day
        :param date_string: YYYY-mm-dd formatted day on which we poll faster
        :param event_year: The year of events to fetch
        :param interval: How many minutes between fetches
        """
        self._require_admin()
        date_string = self.request.get("date_string")
        event_year = self.request.get("event_year")
        interval = self.request.get("interval")

        start = datetime.strptime(date_string, "%Y-%m-%d")
        event_year = int(event_year)
        interval = int(interval)

        # Enqueue the tasks
        now = datetime.now()
        for i in xrange(0, 24*60, interval):
            # 24*60 is number of minutes per day
            task_eta = start + timedelta(minutes=i)
            if task_eta < now:
                # Don't enqueue tasks in the past
                continue
            taskqueue.add(
                queue_name='datafeed',
                target='backend-tasks',
                url='/backend-tasks/get/event_list/{}'.format(event_year),
                eta=task_eta,
                method='GET'
            )

        # Set the cache timeout sitevar
        end_timestamp = (start + timedelta(days=1) - datetime(1970, 1, 1)).total_seconds()
        cache_key_regex = ".*{}.*".format(event_year)
        turbo_mode_json = {
            'regex':  cache_key_regex,
            'valid_until': int(end_timestamp),
            'cache_length': 61
        }
        turbo_sitevar = Sitevar.get_or_insert('turbo_mode', description="Temporarily shorten cache expiration")
        turbo_sitevar.contents = turbo_mode_json
        turbo_sitevar.put()

        self.response.out.write("Enqueued {} tasks to update {} events starting at {}".format((24*60/interval), event_year, start))
