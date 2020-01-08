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
from consts.playoff_type import PlayoffType
from controllers.base_controller import LoggedInHandler
from database import match_query
from database.event_query import DistrictEventsQuery, EventListQuery
from database.district_query import DistrictChampsInYearQuery
from helpers.award_manipulator import AwardManipulator
from helpers.district_manipulator import DistrictManipulator
from helpers.district_team_manipulator import DistrictTeamManipulator
from helpers.event_manipulator import EventManipulator
from helpers.event_team_manipulator import EventTeamManipulator
from helpers.match_helper import MatchHelper
from helpers.notification_sender import NotificationSender
from helpers.playoff_advancement_helper import PlayoffAdvancementHelper
from helpers.search_helper import SearchHelper
from helpers.team_manipulator import TeamManipulator
from models.award import Award
from models.district import District
from models.district_team import DistrictTeam
from models.event import Event
from models.event_team import EventTeam
from models.mobile_client import MobileClient
from models.sitevar import Sitevar
from models.subscription import Subscription
from models.team import Team


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

        from helpers.tbans_helper import TBANSHelper
        for client in webhooks:
            if not TBANSHelper.ping(client):
                failures.append(client.key)

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


class AdminRebuildDivisionsEnqueue(LoggedInHandler):
    """
    Enqueue a task to build past event parent/child relationships
    """
    def get(self, year):
        self._require_admin()
        taskqueue.add(
            queue_name='admin',
            target='backend-tasks',
            url='/backend-tasks/do/rebuild_divisions/{}'.format(year),
            method='GET')


class AdminRebuildDivisionsDo(LoggedInHandler):
    """
    Add in event parent/child relationships
    Map CMP_DIVISION -> CMP_FINALS and DCMP_DIVISION -> DCMP (in the same district)
    Ensure all events end on the same day, to account for #2champz
    """
    TYPE_MAP = {
        EventType.CMP_DIVISION: EventType.CMP_FINALS,
        EventType.DISTRICT_CMP_DIVISION: EventType.DISTRICT_CMP,
    }

    def get(self, year):
        self._require_admin()
        year = int(year)
        events = EventListQuery(year).fetch()
        events_by_type = defaultdict(list)
        for event in events:
            if event.event_type_enum in self.TYPE_MAP.keys() or event.event_type_enum in self.TYPE_MAP.values():
                events_by_type[event.event_type_enum].append(event)

        output = ""
        for from_type, to_type in self.TYPE_MAP.iteritems():
            for event in events_by_type[to_type]:
                divisions = []
                for candidate_division in events_by_type[from_type]:
                    if candidate_division.end_date.date() == event.end_date.date() and candidate_division.district_key == event.district_key:
                        candidate_division.parent_event = event.key
                        divisions.append(candidate_division.key)
                        output += "Event {} is the parent of {}<br/>".format(event.key_name, candidate_division.key_name)
                        EventManipulator.createOrUpdate(candidate_division)

                event.divisions = divisions
                if divisions:
                    output += "Divisions {} added to {}<br/>".format(event.division_keys_json, event.key_name)
                EventManipulator.createOrUpdate(event)
        self.response.out.write(output)


class AdminBackfillPlayoffTypeEnqueue(LoggedInHandler):
    """
    Enqueue a task to build past event parent/child relationships
    """
    def get(self, year):
        self._require_admin()
        taskqueue.add(
            queue_name='admin',
            target='backend-tasks',
            url='/backend-tasks/do/backfill_playoff_type/{}'.format(year),
            method='GET')


class AdminBackfillPlayoffTypeDo(LoggedInHandler):
    """
    Set playoff types
    """

    # These offseasons played the 2014 game
    EXCEPTIONS_2015 = ['2015cc', '2015cacc', '2015mttd']

    def get(self, year):
        self._require_admin()
        year = int(year)
        events = EventListQuery(year).fetch()
        for event in events:
            if not event.playoff_type:
                if event.year == 2015 and event.key_name not in self.EXCEPTIONS_2015:
                    event.playoff_type = PlayoffType.AVG_SCORE_8_TEAM
                else:
                    event.playoff_type = PlayoffType.BRACKET_8_TEAM
            EventManipulator.createOrUpdate(event)
        self.response.out.write("Update {} events".format(len(events)))


class AdminClearEventTeamsDo(LoggedInHandler):
    """
    Remove all eventteams from an event
    """
    def get(self, event_key):
        self._require_admin()
        event = Event.get_by_id(event_key)
        if not event:
            self.abort(404)
            return
        existing_event_team_keys = set(EventTeam.query(EventTeam.event == event.key).fetch(1000, keys_only=True))
        EventTeamManipulator.delete_keys(existing_event_team_keys)

        self.response.out.write("Deleted {} EventTeams from {}".format(len(existing_event_team_keys), event_key))


class AdminCreateDistrictTeamsDo(LoggedInHandler):
    def get(self, year):
        year = int(year)
        team_districts = defaultdict(list)
        logging.info("Fetching events in {}".format(year))
        year_events = Event.query(year == Event.year, Event.district_key == None, Event.event_district_enum != None).fetch()
        for event in year_events:
            logging.info("Fetching EventTeams for {}".format(event.key_name))
            event_teams = EventTeam.query(EventTeam.event == event.key).fetch()
            for event_team in event_teams:
                team_districts[event_team.team.id()].append(event.district_key.id())

        new_district_teams = []
        for team_key, districts in team_districts.iteritems():
            most_frequent_district_key = max(set(districts), key=districts.count)
            logging.info("Assuming team {} belongs to {}".format(team_key, most_frequent_district_key))
            dt_key = DistrictTeam.renderKeyName(most_frequent_district_key, team_key)
            new_district_teams.append(DistrictTeam(id=dt_key, year=year, team=ndb.Key(Team, team_key), district_key=ndb.Key(District, most_frequent_district_key)))

        logging.info("Finishing updating old district teams from event teams")
        DistrictTeamManipulator.createOrUpdate(new_district_teams)
        self.response.out.write("Finished creating district teams for {}".format(year))


class AdminCreateDistrictsEnqueue(LoggedInHandler):
    """
    Create District models from old DCMPs
    """
    def get(self, year):
        self._require_admin()
        taskqueue.add(
            queue_name='admin',
            target='backend-tasks',
            url='/backend-tasks-b2/do/rebuild_districts/{}'.format(year),
            method='GET'
        )
        self.response.out.write("Enqueued district creation for {}".format(year))


class AdminCreateDistrictsDo(LoggedInHandler):
    def get(self, year):
        year = int(year)
        year_dcmps = DistrictChampsInYearQuery(year).fetch()
        districts_to_write = []

        for dcmp in year_dcmps:
            district_abbrev = DistrictType.type_abbrevs[dcmp.event_district_enum]
            district_key = District.renderKeyName(year, district_abbrev)
            logging.info("Creating {}".format(district_key))

            district = District(
                id=district_key,
                year=year,
                abbreviation=district_abbrev,
                display_name=DistrictType.type_names[dcmp.event_district_enum],
                elasticsearch_name=next((k for k, v in DistrictType.elasticsearch_names.iteritems() if v == dcmp.event_district_enum), None)
            )
            districts_to_write.append(district)

        logging.info("Writing {} new districts".format(len(districts_to_write)))
        DistrictManipulator.createOrUpdate(districts_to_write, run_post_update_hook=False)

        for dcmp in year_dcmps:
            district_abbrev = DistrictType.type_abbrevs[dcmp.event_district_enum]
            district_key = District.renderKeyName(year, district_abbrev)
            district_events_future = DistrictEventsQuery(district_key).fetch_async()

            district_events = district_events_future.get_result()
            logging.info("Found {} events to update".format(len(district_events)))
            events_to_write = []
            for event in district_events:
                event.district_key = ndb.Key(District, district_key)
                events_to_write.append(event)
            EventManipulator.createOrUpdate(events_to_write)

        for dcmp in year_dcmps:
            district_abbrev = DistrictType.type_abbrevs[dcmp.event_district_enum]
            district_key = District.renderKeyName(year, district_abbrev)
            districtteams_future = DistrictTeam.query(DistrictTeam.year == year, DistrictTeam.district == DistrictType.abbrevs.get(district_abbrev, None)).fetch_async()

            districtteams = districtteams_future.get_result()
            logging.info("Found {} DistrictTeams to update".format(len(districtteams)))
            districtteams_to_write = []
            for districtteam in districtteams:
                districtteam.district_key = ndb.Key(District, district_key)
                districtteams_to_write.append(districtteam)
            DistrictTeamManipulator.createOrUpdate(districtteams_to_write)


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
        if event.event_type_enum in {EventType.OFFSEASON, EventType.FOC}:
            matches = MatchHelper.organizeMatches(matches_future.get_result())
            bracket = PlayoffAdvancementHelper.generateBracket(matches, event, event.alliance_selections)
            if 'f' in bracket:
                winning_alliance = '{}_alliance'.format(bracket['f']['f1']['winning_alliance'])
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
                    team_list=[ndb.Key(Team, 'frc{}'.format(team)) for team in bracket['f']['f1'][winning_alliance] if team.isdigit()],
                    recipient_json_list=[json.dumps({'team_number': team, 'awardee': None}) for team in bracket['f']['f1'][winning_alliance]],
                ))

                awards.append(Award(
                    id=Award.render_key_name(event.key_name, AwardType.FINALIST),
                    name_str="Finalist",
                    award_type_enum=AwardType.FINALIST,
                    year=event.year,
                    event=event.key,
                    event_type_enum=event.event_type_enum,
                    team_list=[ndb.Key(Team, 'frc{}'.format(team)) for team in bracket['f']['f1'][losing_alliance] if team.isdigit()],
                    recipient_json_list=[json.dumps({'team_number': team, 'awardee': None}) for team in bracket['f']['f1'][losing_alliance]],
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


class AdminRunPostUpdateHooksEnqueue(LoggedInHandler):
    def get(self, model_type):
        if model_type == 'events':
            taskqueue.add(
                queue_name='admin',
                url='/tasks/admin/do/run_post_update_hooks/events',
                method='GET')
            self.response.out.write("Enqueued run post update hooks for events")
        elif model_type == 'teams':
            taskqueue.add(
                queue_name='admin',
                url='/tasks/admin/do/run_post_update_hooks/teams',
                method='GET')
            self.response.out.write("Enqueued run post update hooks for teams")
        else:
            self.response.out.write("Unknown model type: {}".format(model_type))


class AdminRunPostUpdateHooksDo(LoggedInHandler):
    def get(self, model_type):
        if model_type == 'events':
            event_keys = Event.query().fetch(keys_only=True)
            for event_key in event_keys:
                taskqueue.add(
                    queue_name='admin',
                    url='/tasks/admin/do/run_event_post_update_hook/' + event_key.id(),
                    method='GET')
        elif model_type == 'teams':
            team_keys = Team.query().fetch(keys_only=True)
            for team_key in team_keys:
                taskqueue.add(
                    queue_name='admin',
                    url='/tasks/admin/do/run_team_post_update_hook/' + team_key.id(),
                    method='GET')


class AdminRunEventPostUpdateHookDo(LoggedInHandler):
    def get(self, event_key):
        event = Event.get_by_id(event_key)
        EventManipulator.runPostUpdateHook([event])


class AdminRunTeamPostUpdateHookDo(LoggedInHandler):
    def get(self, team_key):
        team = Team.get_by_id(team_key)
        TeamManipulator.runPostUpdateHook([team])


class AdminUpdateAllTeamSearchIndexEnqueue(LoggedInHandler):
    def get(self):
        taskqueue.add(
            queue_name='search-index-update',
            url='/tasks/do/update_all_team_search_index',
            method='GET')
        self.response.out.write("Enqueued update all team search index")


class AdminUpdateAllTeamSearchIndexDo(LoggedInHandler):
    def get(self):
        team_keys = Team.query().fetch(keys_only=True)
        for team_key in team_keys:
            taskqueue.add(
                queue_name='search-index-update',
                url='/tasks/do/update_team_search_index/' + team_key.id(),
                method='GET')


class AdminUpdateTeamSearchIndexDo(LoggedInHandler):
    def get(self, team_key):
        team = Team.get_by_id(team_key)
        SearchHelper.update_team_awards_index(team)
        SearchHelper.update_team_location_index(team)
