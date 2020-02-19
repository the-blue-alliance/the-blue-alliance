import datetime
import logging
import os
import json

from google.appengine.api import taskqueue

from google.appengine.ext import ndb

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from consts.district_type import DistrictType
from consts.event_type import EventType

from controllers.api.api_status_controller import ApiStatusController
from database.district_query import DistrictsInYearQuery
from database.event_query import DistrictEventsQuery, EventQuery
from database.match_query import EventMatchesQuery
from database.team_query import DistrictTeamsQuery
from helpers.award_manipulator import AwardManipulator
from helpers.bluezone_helper import BlueZoneHelper
from helpers.district_helper import DistrictHelper
from helpers.district_manipulator import DistrictManipulator
from helpers.event_helper import EventHelper
from helpers.event_manipulator import EventManipulator
from helpers.event_details_manipulator import EventDetailsManipulator
from helpers.event_insights_helper import EventInsightsHelper
from helpers.event_team_manipulator import EventTeamManipulator
from helpers.event_team_status_helper import EventTeamStatusHelper
from helpers.event_team_repairer import EventTeamRepairer
from helpers.event_team_updater import EventTeamUpdater
from helpers.firebase.firebase_pusher import FirebasePusher
from helpers.insights_helper import InsightsHelper
from helpers.match_helper import MatchHelper
from helpers.match_time_prediction_helper import MatchTimePredictionHelper
from helpers.matchstats_helper import MatchstatsHelper
from helpers.notification_helper import NotificationHelper
from helpers.outgoing_notification_helper import OutgoingNotificationHelper
from helpers.playoff_advancement_helper import PlayoffAdvancementHelper
from helpers.prediction_helper import PredictionHelper

from helpers.insight_manipulator import InsightManipulator
from helpers.suggestions.suggestion_fetcher import SuggestionFetcher
from helpers.team_manipulator import TeamManipulator
from helpers.match_manipulator import MatchManipulator
from models.district import District
from models.event import Event
from models.event_details import EventDetails
from models.event_team import EventTeam
from models.match import Match
from models.sitevar import Sitevar
from models.suggestion import Suggestion
from models.team import Team
from models.typeahead_entry import TypeaheadEntry


class EventShortNameCalcEnqueue(webapp.RequestHandler):
    """
    Enqueues Event short_name computation for official events
    """
    def get(self, year):
        event_keys = Event.query(Event.official == True, Event.year == int(year)).fetch(200, keys_only=True)
        events = ndb.get_multi(event_keys)

        for event in events:
            taskqueue.add(
                url='/tasks/math/do/event_short_name_calc_do/{}'.format(event.key.id()),
                method='GET')

        template_values = {'events': events}
        path = os.path.join(os.path.dirname(__file__), '../templates/math/event_short_name_calc_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class EventShortNameCalcDo(webapp.RequestHandler):
    """
    Computes Event short_name
    """
    def get(self, event_key):
        event = Event.get_by_id(event_key)
        event.short_name = EventHelper.getShortName(event.name)
        EventManipulator.createOrUpdate(event)

        template_values = {'event': event}
        path = os.path.join(os.path.dirname(__file__), '../templates/math/event_short_name_calc_do.html')
        self.response.out.write(template.render(path, template_values))


class EventTeamRepairDo(webapp.RequestHandler):
    """
    Repair broken EventTeams.
    """
    def get(self):
        event_teams_keys = EventTeam.query(EventTeam.year == None).fetch(keys_only=True)
        event_teams = ndb.get_multi(event_teams_keys)

        event_teams = EventTeamRepairer.repair(event_teams)
        event_teams = EventTeamManipulator.createOrUpdate(event_teams)

        # sigh. -gregmarra
        if type(event_teams) == EventTeam:
            event_teams = [event_teams]

        template_values = {
            'event_teams': event_teams,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/math/eventteam_repair_do.html')
        self.response.out.write(template.render(path, template_values))


class EventTeamUpdate(webapp.RequestHandler):
    """
    Task that updates the EventTeam index for an Event.
    Can only update or delete EventTeams for unregistered teams.
    ^^^ Does it actually do this? Eugene -- 2013/07/30
    """
    def get(self, event_key):
        _, event_teams, et_keys_to_del = EventTeamUpdater.update(event_key)

        if event_teams:
            event_teams = filter(lambda et: et.team.get() is not None, event_teams)
            event_teams = EventTeamManipulator.createOrUpdate(event_teams)

        if et_keys_to_del:
            EventTeamManipulator.delete_keys(et_keys_to_del)

        template_values = {
            'event_teams': event_teams,
            'deleted_event_teams_keys': et_keys_to_del
        }

        path = os.path.join(os.path.dirname(__file__),
                            '../templates/math/eventteam_update_do.html')
        self.response.out.write(template.render(path, template_values))


class EventTeamUpdateEnqueue(webapp.RequestHandler):
    """
    Handles enqueing building attendance for Events.
    """
    def get(self, when):
        if when == "all":
            event_keys = Event.query().fetch(10000, keys_only=True)
        else:
            event_keys = Event.query(Event.year == int(when)).fetch(10000, keys_only=True)

        for event_key in event_keys:
            taskqueue.add(
                url='/tasks/math/do/eventteam_update/' + event_key.id(),
                method='GET')

        template_values = {
            'event_keys': event_keys,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/math/eventteam_update_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class EventMatchstatsDo(webapp.RequestHandler):
    """
    Calculates match stats (OPR/DPR/CCWM) for an event
    Calculates predictions for an event
    Calculates insights for an event
    """
    def get(self, event_key):
        event = Event.get_by_id(event_key)
        matchstats_dict = MatchstatsHelper.calculate_matchstats(event.matches, event.year)
        if any([v != {} for v in matchstats_dict.values()]):
            pass
        else:
            logging.warn("Matchstat calculation for {} failed!".format(event_key))
            matchstats_dict = None

        predictions_dict = None
        if event.year in {2016, 2017, 2018, 2019, 2020} and event.event_type_enum in EventType.SEASON_EVENT_TYPES or event.enable_predictions:
            sorted_matches = MatchHelper.play_order_sort_matches(event.matches)
            match_predictions, match_prediction_stats, stat_mean_vars = PredictionHelper.get_match_predictions(sorted_matches)
            ranking_predictions, ranking_prediction_stats = PredictionHelper.get_ranking_predictions(sorted_matches, match_predictions)

            predictions_dict = {
                'match_predictions': match_predictions,
                'match_prediction_stats': match_prediction_stats,
                'stat_mean_vars': stat_mean_vars,
                'ranking_predictions': ranking_predictions,
                'ranking_prediction_stats': ranking_prediction_stats
            }

        event_insights = EventInsightsHelper.calculate_event_insights(event.matches, event.year)

        event_details = EventDetails(
            id=event_key,
            matchstats=matchstats_dict,
            predictions=predictions_dict,
            insights=event_insights,
        )
        EventDetailsManipulator.createOrUpdate(event_details)

        template_values = {
            'matchstats_dict': matchstats_dict,
        }

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            path = os.path.join(os.path.dirname(__file__), '../templates/math/event_matchstats_do.html')
            self.response.out.write(template.render(path, template_values))

    def post(self):
        self.get()


class EventMatchstatsEnqueue(webapp.RequestHandler):
    """
    Enqueues Matchstats calculation
    """
    def get(self, when):
        if when == "now":
            events = EventHelper.getEventsWithinADay()
        else:
            events = Event.query(Event.year == int(when)).fetch(500)

        EventHelper.sort_events(events)
        for event in events:
            taskqueue.add(
                queue_name='run-in-order',  # Because predictions depend on past events
                url='/tasks/math/do/event_matchstats/' + event.key_name,
                method='GET')

        template_values = {
            'event_count': len(events),
            'year': when
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/math/event_matchstats_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class FinalMatchesRepairDo(webapp.RequestHandler):
    """
    Repairs zero-indexed final matches
    """
    def get(self, year):
        year_event_keys = Event.query(Event.year == int(year)).fetch(1000, keys_only=True)

        final_match_keys = []
        for event_key in year_event_keys:
            final_match_keys.extend(Match.query(Match.event == event_key, Match.comp_level == 'f').fetch(100, keys_only=True))

        match_keys_to_repair = []
        for match_key in final_match_keys:
            key_name = match_key.id()
            if '_f0m' in key_name:
                match_keys_to_repair.append(match_key)

        deleted_keys = []
        matches_to_repair = ndb.get_multi(match_keys_to_repair)
        for match in matches_to_repair:
            deleted_keys.append(match.key)

            event = ndb.get_multi([match.event])[0]
            match.set_number = 1
            match.key = ndb.Key(Match, Match.renderKeyName(
                event.key.id(),
                match.comp_level,
                match.set_number,
                match.match_number))

        MatchManipulator.createOrUpdate(matches_to_repair)
        MatchManipulator.delete_keys(deleted_keys)

        template_values = {'deleted_keys': deleted_keys,
                           'new_matches': matches_to_repair}

        path = os.path.join(os.path.dirname(__file__), '../templates/math/final_matches_repair_do.html')
        self.response.out.write(template.render(path, template_values))


class YearInsightsEnqueue(webapp.RequestHandler):
    """
    Enqueues Insights calculation of a given kind for a given year
    """
    def get(self, kind, year):
        taskqueue.add(
            target='backend-tasks-b2',
            url='/backend-tasks-b2/math/do/insights/{}/{}'.format(kind, year),
            method='GET')

        template_values = {
            'kind': kind,
            'year': year
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/math/year_insights_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class YearInsightsDo(webapp.RequestHandler):
    """
    Calculates insights of a given kind for a given year.
    Calculations of a given kind should reuse items fetched from the datastore.
    """

    def get(self, kind, year):
        year = int(year)

        insights = None
        if kind == 'matches':
            insights = InsightsHelper.doMatchInsights(year)
        elif kind == 'awards':
            insights = InsightsHelper.doAwardInsights(year)
        elif kind == 'predictions':
            insights = InsightsHelper.doPredictionInsights(year)

        if insights != None:
            InsightManipulator.createOrUpdate(insights)

        template_values = {
            'insights': insights,
            'year': year,
            'kind': kind,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/math/year_insights_do.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):
        self.get()


class OverallInsightsEnqueue(webapp.RequestHandler):
    """
    Enqueues Overall Insights calculation for a given kind.
    """
    def get(self, kind):
        taskqueue.add(
            target='backend-tasks-b2',
            url='/backend-tasks-b2/math/do/overallinsights/{}'.format(kind),
            method='GET')

        template_values = {
            'kind': kind,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/math/overall_insights_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class OverallInsightsDo(webapp.RequestHandler):
    """
    Calculates overall insights of a given kind.
    Calculations of a given kind should reuse items fetched from the datastore.
    """

    def get(self, kind):
        insights = None
        if kind == 'matches':
            insights = InsightsHelper.doOverallMatchInsights()
        elif kind == 'awards':
            insights = InsightsHelper.doOverallAwardInsights()

        if insights != None:
            InsightManipulator.createOrUpdate(insights)

        template_values = {
            'insights': insights,
            'kind': kind,
        }

        path = os.path.join(os.path.dirname(__file__), '../templates/math/overall_insights_do.html')
        self.response.out.write(template.render(path, template_values))

    def post(self):
        self.get()


class TypeaheadCalcEnqueue(webapp.RequestHandler):
    """
    Enqueues typeahead calculations
    """
    def get(self):
        taskqueue.add(
            target='backend-tasks-b2',
            url='/backend-tasks-b2/math/do/typeaheadcalc',
            method='GET')
        template_values = {}
        path = os.path.join(os.path.dirname(__file__), '../templates/math/typeaheadcalc_enqueue.html')
        self.response.out.write(template.render(path, template_values))


class TypeaheadCalcDo(webapp.RequestHandler):
    """
    Calculates typeahead entries
    """
    def get(self):
        @ndb.tasklet
        def get_events_async():
            event_keys = yield Event.query().order(-Event.year).order(Event.name).fetch_async(keys_only=True)
            events = yield ndb.get_multi_async(event_keys)
            raise ndb.Return(events)

        @ndb.tasklet
        def get_teams_async():
            team_keys = yield Team.query().order(Team.team_number).fetch_async(keys_only=True)
            teams = yield ndb.get_multi_async(team_keys)
            raise ndb.Return(teams)

        @ndb.tasklet
        def get_districts_async():
            district_keys = yield District.query().order(-District.year).fetch_async(keys_only=True)
            districts = yield ndb.get_multi_async(district_keys)
            raise ndb.Return(districts)

        @ndb.toplevel
        def get_events_teams_districts():
            events, teams, districts = yield get_events_async(), get_teams_async(), get_districts_async()
            raise ndb.Return((events, teams, districts))

        events, teams, districts = get_events_teams_districts()

        results = {}
        for team in teams:
            if not team.nickname:
                nickname = "Team %s" % team.team_number
            else:
                nickname = team.nickname
            data = '%s | %s' % (team.team_number, nickname)
            if TypeaheadEntry.ALL_TEAMS_KEY in results:
                results[TypeaheadEntry.ALL_TEAMS_KEY].append(data)
            else:
                results[TypeaheadEntry.ALL_TEAMS_KEY] = [data]

        for district in districts:
            data = '%s District [%s]' % (district.display_name, district.abbreviation.upper())
            # all districts
            if TypeaheadEntry.ALL_DISTRICTS_KEY in results:
                if data not in results[TypeaheadEntry.ALL_DISTRICTS_KEY]:
                    results[TypeaheadEntry.ALL_DISTRICTS_KEY].append(data)
            else:
                results[TypeaheadEntry.ALL_DISTRICTS_KEY] = [data]

        for event in events:
            data = '%s %s [%s]' % (event.year, event.name, event.event_short.upper())
            # all events
            if TypeaheadEntry.ALL_EVENTS_KEY in results:
                results[TypeaheadEntry.ALL_EVENTS_KEY].append(data)
            else:
                results[TypeaheadEntry.ALL_EVENTS_KEY] = [data]
            # events by year
            if TypeaheadEntry.YEAR_EVENTS_KEY.format(event.year) in results:
                results[TypeaheadEntry.YEAR_EVENTS_KEY.format(event.year)].append(data)
            else:
                results[TypeaheadEntry.YEAR_EVENTS_KEY.format(event.year)] = [data]

        # Prepare to remove old entries
        old_entry_keys_future = TypeaheadEntry.query().fetch_async(keys_only=True)

        # Add new entries
        entries = []
        for key_name, data in results.items():
            entries.append(TypeaheadEntry(id=key_name, data_json=json.dumps(data)))
        ndb.put_multi(entries)

        # Remove old entries
        old_entry_keys = set(old_entry_keys_future.get_result())
        new_entry_keys = set([ndb.Key(TypeaheadEntry, key_name) for key_name in results.keys()])
        keys_to_delete = old_entry_keys.difference(new_entry_keys)
        logging.info("Removing the following unused TypeaheadEntries: {}".format([key.id() for key in keys_to_delete]))
        ndb.delete_multi(keys_to_delete)

        template_values = {'results': results}
        path = os.path.join(os.path.dirname(__file__), '../templates/math/typeaheadcalc_do.html')
        self.response.out.write(template.render(path, template_values))


class DistrictPointsCalcEnqueue(webapp.RequestHandler):
    """
    Enqueues calculation of district points for all season events for a given year
    """

    def get(self, year):
        year = int(year)

        event_keys = Event.query(Event.year == year, Event.event_type_enum.IN(EventType.SEASON_EVENT_TYPES)).fetch(None, keys_only=True)
        for event_key in event_keys:
            taskqueue.add(url='/tasks/math/do/district_points_calc/{}'.format(event_key.id()), method='GET')

        self.response.out.write("Enqueued for: {}".format([event_key.id() for event_key in event_keys]))


class DistrictPointsCalcDo(webapp.RequestHandler):
    """
    Calculates district points for an event
    """

    def get(self, event_key):
        event = Event.get_by_id(event_key)
        if event.event_type_enum not in EventType.SEASON_EVENT_TYPES and not self.request.get('allow-offseason', None):
            if 'X-Appengine-Taskname' not in self.request.headers:
                self.response.out.write("Can't calculate district points for a non-season event {}!"
                                        .format(event.key_name))
            return

        district_points = DistrictHelper.calculate_event_points(event)

        event_details = EventDetails(
            id=event_key,
            district_points=district_points
        )
        EventDetailsManipulator.createOrUpdate(event_details)

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            self.response.out.write(event.district_points)

        # Enqueue task to update rankings
        if event.district_key:
            taskqueue.add(url='/tasks/math/do/district_rankings_calc/{}'.format(event.district_key.id()), method='GET')


class DistrictRankingsCalcEnqueue(webapp.RequestHandler):
    """
    Enqueues calculation of rankings for all districts for a given year
    """

    def get(self, year):
        districts = DistrictsInYearQuery(int(year)).fetch()
        district_keys = [district.key.id() for district in districts]
        for district_key in district_keys:
            taskqueue.add(url='/tasks/math/do/district_rankings_calc/{}'.format(district_key), method='GET')
            taskqueue.add(url='/backend-tasks/get/district_rankings/{}'.format(district_key), method='GET')

        self.response.out.write("Enqueued for: {}".format(district_keys))


class DistrictRankingsCalcDo(webapp.RequestHandler):
    """
    Calculates district rankings for a district year
    """

    def get(self, district_key):
        district = District.get_by_id(district_key)
        if not district:
            self.response.out.write("District {} does not exist!".format(district_key))
            return

        events_future = DistrictEventsQuery(district_key).fetch_async()
        teams_future = DistrictTeamsQuery(district_key).fetch_async()

        events = events_future.get_result()
        for event in events:
            event.prep_details()
        EventHelper.sort_events(events)
        team_totals = DistrictHelper.calculate_rankings(events, teams_future, district.year)

        rankings = []
        current_rank = 1
        for key, points in team_totals:
            point_detail = {}
            point_detail["rank"] = current_rank
            point_detail["team_key"] = key
            point_detail["event_points"] = []
            for event, event_points in points["event_points"]:
                event_points['event_key'] = event.key.id()
                event_points['district_cmp'] = (
                    event.event_type_enum == EventType.DISTRICT_CMP or
                    event.event_type_enum == EventType.DISTRICT_CMP_DIVISION)
                point_detail["event_points"].append(event_points)

            point_detail["rookie_bonus"] = points.get("rookie_bonus", 0)
            point_detail["point_total"] = points["point_total"]
            rankings.append(point_detail)
            current_rank += 1

        if rankings:
            district.rankings = rankings
            DistrictManipulator.createOrUpdate(district)

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            self.response.out.write("Finished calculating rankings for: {}".format(district_key))


class EventTeamStatusCalcEnqueue(webapp.RequestHandler):
    """
    Enqueues calculation of event team status for a year
    """

    def get(self, year):
        event_keys = [e.id() for e in Event.query(Event.year==int(year)).fetch(keys_only=True)]
        for event_key in event_keys:
            taskqueue.add(url='/tasks/math/do/event_team_status/{}'.format(event_key), method='GET')

        self.response.out.write("Enqueued for: {}".format(event_keys))


class EventTeamStatusCalcDo(webapp.RequestHandler):
    """
    Calculates event team statuses for all teams at an event
    """
    def get(self, event_key):
        event = Event.get_by_id(event_key)
        event_teams = EventTeam.query(EventTeam.event==event.key).fetch()
        for event_team in event_teams:
            status = EventTeamStatusHelper.generate_team_at_event_status(event_team.team.id(), event)
            event_team.status = status
            FirebasePusher.update_event_team_status(event_key, event_team.team.id(), status)
        EventTeamManipulator.createOrUpdate(event_teams)

        if 'X-Appengine-Taskname' not in self.request.headers:  # Only write out if not in taskqueue
            self.response.out.write("Finished calculating event team statuses for: {}".format(event_key))


class UpcomingNotificationDo(webapp.RequestHandler):
    """
    Sends out notifications for upcoming matches
    """
    def get(self):
        live_events = EventHelper.getEventsWithinADay()
        NotificationHelper.send_upcoming_matches(live_events)


class UpdateLiveEventsDo(webapp.RequestHandler):
    """
    Updates live events
    """
    def get(self):
        FirebasePusher.update_live_events()


class MatchTimePredictionsEnqueue(webapp.RequestHandler):
    """
    Enqueue match time predictions for all current events
    """
    def get(self):
        live_events = EventHelper.getEventsWithinADay()
        for event in live_events:
            taskqueue.add(url='/tasks/math/do/predict_match_times/{}'.format(event.key_name),
                          method='GET')
        # taskqueue.add(url='/tasks/do/bluezone_update', method='GET')

        # Clear down events for events that aren't live
        status_sitevar = Sitevar.get_by_id('apistatus.down_events')
        if status_sitevar is not None:
            live_event_keys = set([e.key.id() for e in live_events])

            old_status = set(status_sitevar.contents)
            new_status = old_status.copy()
            for event_key in old_status:
                if event_key not in live_event_keys:
                    new_status.remove(event_key)
            status_sitevar.contents = list(new_status)
            status_sitevar.put()

            # Clear API Response cache
            ApiStatusController.clear_cache_if_needed(old_status, new_status)

        self.response.out.write("Enqueued time prediction for {} events".format(len(live_events)))


class MatchTimePredictionsDo(webapp.RequestHandler):
    """
    Predicts match times for a given live event
    Also handles detection for whether the event is down
    """
    def get(self, event_key):
        import pytz

        event = Event.get_by_id(event_key)
        if not event:
            self.abort(404)

        matches = event.matches
        if not matches or not event.timezone_id:
            return

        timezone = pytz.timezone(event.timezone_id)
        played_matches = MatchHelper.recentMatches(matches, num=0)
        unplayed_matches = MatchHelper.upcomingMatches(matches, num=len(matches))
        MatchTimePredictionHelper.predict_future_matches(event_key, played_matches, unplayed_matches, timezone, event.within_a_day)

        # Detect whether the event is down
        # An event NOT down if ANY unplayed match's predicted time is within its scheduled time by a threshold and
        # the last played match (if it exists) wasn't too long ago.
        event_down = len(unplayed_matches) > 0
        for unplayed_match in unplayed_matches:
            if ((unplayed_match.predicted_time and unplayed_match.time and
                unplayed_match.predicted_time < unplayed_match.time + datetime.timedelta(minutes=30)) or
                (played_matches == [] or played_matches[-1].actual_time is None or played_matches[-1].actual_time > datetime.datetime.now() - datetime.timedelta(minutes=30))):
                event_down = False
                break

        status_sitevar = Sitevar.get_by_id('apistatus.down_events')
        if status_sitevar is None:
            status_sitevar = Sitevar(id="apistatus.down_events", description="A list of down event keys", values_json="[]")
        old_status = set(status_sitevar.contents)
        new_status = old_status.copy()
        if event_down:
            new_status.add(event_key)
        elif event_key in new_status:
            new_status.remove(event_key)

        status_sitevar.contents = list(new_status)
        status_sitevar.put()

        # Clear API Response cache
        ApiStatusController.clear_cache_if_needed(old_status, new_status)


class RebuildPlayoffAdvancementEnqueue(webapp.RequestHandler):
    """
    Enqueue rebuilding playoff advancement details for an event
    """
    def get(self, event_key):
        event = Event.get_by_id(event_key)
        if not event:
            self.abort(404)
            return

        taskqueue.add(url='/tasks/math/do/playoff_advancement_update/{}'.format(event.key_name),
                      method='GET')

        self.response.out.write("Enqueued time prediction for {}".format(event.key_name))


class RebuildPlayoffAdvancementDo(webapp.RequestHandler):
    """
    Rebuilds playoff advancement for a given event
    """
    def get(self, event_key):
        event = Event.get_by_id(event_key)
        if not event:
            self.abort(404)

        event_future = EventQuery(event_key).fetch_async(return_updated=True)
        matches_future = EventMatchesQuery(event_key).fetch_async(return_updated=True)

        event, _ = event_future.get_result()
        matches, _ = matches_future.get_result()

        cleaned_matches = MatchHelper.deleteInvalidMatches(matches, event)
        matches = MatchHelper.organizeMatches(cleaned_matches)
        bracket_table, playoff_advancement, _, _ = PlayoffAdvancementHelper.generatePlayoffAdvancement(event, matches)

        event_details = EventDetails(
            id=event.key_name,
            playoff_advancement={
                'advancement': playoff_advancement,
                'bracket': bracket_table,
            },
        )
        EventDetailsManipulator.createOrUpdate(event_details)

        self.response.out.write("New playoff advancement for {}\n{}".format(event.key_name, json.dumps(event_details.playoff_advancement, indent=2, sort_keys=True)))


class BlueZoneUpdateDo(webapp.RequestHandler):
    """
    Update the current "best match"
    """
    def get(self):
        live_events = EventHelper.getEventsWithinADay()
        try:
            BlueZoneHelper.update_bluezone(live_events)
        except Exception, e:
            logging.error("BlueZone update failed")
            logging.exception(e)


class SuggestionQueueDailyNag(webapp.RequestHandler):
    """
    Daily job to nag a slack channel about pending suggestions
    """
    def get(self):
        hook_sitevars = Sitevar.get_by_id('slack.hookurls')
        if not hook_sitevars:
            return
        channel_url = hook_sitevars.contents.get('suggestion-nag')
        if not channel_url:
            return
        counts = map(lambda t: SuggestionFetcher.count(Suggestion.REVIEW_PENDING, t),
                     Suggestion.MODELS)

        nag_text = "There are pending suggestions!\n"
        suggestions_to_nag = False
        for count, name in zip(counts, Suggestion.MODELS):
            if count > 0:
                suggestions_to_nag = True
                nag_text += "*{0}*: {1} pending suggestions\n".format(
                    Suggestion.MODEL_NAMES.get(name),
                    count
                )

        if suggestions_to_nag:
            nag_text += "_Review them on <https://www.thebluealliance.com/suggest/review|TBA>_"
            OutgoingNotificationHelper.send_slack_alert(channel_url, nag_text)


class RemapTeamsDo(webapp.RequestHandler):
    """
    Remaps teams within an Event. Useful for offseason events.
    eg: 9254 -> 254B
    """
    def get(self, event_key):
        event = Event.get_by_id(event_key)
        if not event:
            self.abort(404)

        if not event.remap_teams:
            return

        event.prepAwardsMatchesTeams()

        # Remap matches
        EventHelper.remapteams_matches(event.matches, event.remap_teams)
        MatchManipulator.createOrUpdate(event.matches)

        # Remap alliance selections
        if event.alliance_selections:
            EventHelper.remapteams_alliances(event.alliance_selections, event.remap_teams)
        # Remap rankings
        if event.rankings:
            EventHelper.remapteams_rankings(event.rankings, event.remap_teams)
        if event.details and event.details.rankings2:
            EventHelper.remapteams_rankings2(event.details.rankings2, event.remap_teams)
        EventDetailsManipulator.createOrUpdate(event.details)

        # Remap awards
        EventHelper.remapteams_awards(event.awards, event.remap_teams)
        AwardManipulator.createOrUpdate(event.awards, auto_union=False)
