import datetime
import heapq
import logging
import os
import json

from collections import defaultdict

from google.appengine.api import taskqueue

from google.appengine.ext import ndb

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from consts.award_type import AwardType
from consts.district_type import DistrictType
from consts.event_type import EventType

from helpers.event_helper import EventHelper
from helpers.event_manipulator import EventManipulator
from helpers.event_team_manipulator import EventTeamManipulator
from helpers.event_team_repairer import EventTeamRepairer
from helpers.event_team_updater import EventTeamUpdater

from helpers.insight_manipulator import InsightManipulator
from helpers.team_manipulator import TeamManipulator
from helpers.match_manipulator import MatchManipulator
from helpers.matchstats_helper import MatchstatsHelper
from helpers.insights_helper import InsightsHelper

from models.award import Award
from models.event import Event
from models.event_team import EventTeam
from models.match import Match
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
        event.dirty = True  # TODO: hacky
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
        teams, event_teams, et_keys_to_del = EventTeamUpdater.update(event_key)

        teams = TeamManipulator.createOrUpdate(teams)

        if teams:
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
    """
    def get(self, event_key):
        event = Event.get_by_id(event_key)
        matchstats_dict = MatchstatsHelper.calculate_matchstats(event.matches)
        if matchstats_dict != {}:
            event.matchstats_json = json.dumps(matchstats_dict)
            event.dirty = True  # TODO: hacky
            EventManipulator.createOrUpdate(event)
        else:
            logging.warn("Matchstat calculation for {} failed!".format(event_key))

        template_values = {
            'matchstats_dict': matchstats_dict,
        }

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

        for event in events:
            taskqueue.add(
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
            match.dirty = True  # hacky

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
            url='/tasks/math/do/insights/{}/{}'.format(kind, year),
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
            url='/tasks/math/do/overallinsights/{}'.format(kind),
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
        taskqueue.add(url='/tasks/math/do/typeaheadcalc', method='GET')
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

        @ndb.toplevel
        def get_events_and_teams():
            events, teams = yield get_events_async(), get_teams_async()
            raise ndb.Return((events, teams))

        events, teams = get_events_and_teams()

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
    Enqueues calculation of district points for events within a district for a given year
    """

    def get(self, district_type_enum, year):
        district_type_enum = int(district_type_enum)
        if district_type_enum == DistrictType.NO_DISTRICT:
            self.response.out.write("Can't enqueue for non district events!")
            return

        year = int(year)

        event_keys = Event.query(Event.year == year, Event.event_district_enum == district_type_enum).fetch(None, keys_only=True)
        for event_key in event_keys:
            taskqueue.add(url='/tasks/math/do/district_points_calc/{}'.format(event_key.id()), method='GET')

        self.response.out.write("Enqueued for: {}".format([event_key.id() for event_key in event_keys]))


class DistrictPointsCalcDo(webapp.RequestHandler):
    """
    Calculates district points for an event
    """

    def get(self, event_key):
        event = Event.get_by_id(event_key)
        if event.event_district_enum == DistrictType.NO_DISTRICT:
            self.response.out.write("Can't calculate district points for a non-district event!")
            return

        match_key_futures = Match.query(Match.event == event.key).fetch_async(None, keys_only=True)
        award_key_futures = Award.query(Award.event == event.key).fetch_async(None, keys_only=True)

        match_futures = ndb.get_multi_async(match_key_futures.get_result())
        award_futures = ndb.get_multi_async(award_key_futures.get_result())

        POINTS_MULTIPLIER = 3 if event.event_type_enum == EventType.DISTRICT_CMP else 1

        data = {
            'points': defaultdict(lambda: {
                'qual_points': 0,
                'elim_points': 0,
                'alliance_points': 0,
                'award_points': 0,
                'total': 0,
            }),
            'tiebreakers': defaultdict(lambda: {  # for tiebreaker stats that can't be calculated with 'points'
                'qual_wins': 0,
                'highest_qual_scores': [],
            }),
        }

        # match points
        elim_num_wins = defaultdict(lambda: defaultdict(int))
        elim_alliances = defaultdict(lambda: defaultdict(list))
        for match_future in match_futures:
            match = match_future.get_result()
            if not match.has_been_played:
                continue

            if match.comp_level == 'qm':
                if match.winning_alliance == '':
                    for team in match.team_key_names:
                        data['points'][team]['qual_points'] += 1 * POINTS_MULTIPLIER
                else:
                    for team in match.alliances[match.winning_alliance]['teams']:
                        data['points'][team]['qual_points'] += 2 * POINTS_MULTIPLIER
                        data['tiebreakers'][team]['qual_wins'] += 1
                        winning_score = match.alliances[match.winning_alliance]['score']

                for color in ['red', 'blue']:
                    for team in match.alliances[color]['teams']:
                        score = match.alliances[color]['score']
                        data['tiebreakers'][team]['highest_qual_scores'] = heapq.nlargest(3, data['tiebreakers'][team]['highest_qual_scores'] + [score])
            else:
                if match.winning_alliance == '':
                    continue

                match_set_key = '{}_{}{}'.format(match.event.id(), match.comp_level, match.set_number)
                elim_num_wins[match_set_key][match.winning_alliance] += 1
                elim_alliances[match_set_key][match.winning_alliance] += match.alliances[match.winning_alliance]['teams']

                if elim_num_wins[match_set_key][match.winning_alliance] >= 2:
                    for team in elim_alliances[match_set_key][match.winning_alliance]:
                        data['points'][team]['elim_points'] += 5* POINTS_MULTIPLIER

        # alliance points
        if event.alliance_selections:
            selection_points = EventHelper.alliance_selections_to_points(event.alliance_selections)
            for team, points in selection_points.items():
                data['points'][team]['alliance_points'] += points * POINTS_MULTIPLIER
        else:
            logging.warning("Event {} has no alliance selection data!".format(event.key.id()))

        # award points
        for award_future in award_futures:
            award = award_future.get_result()
            if award.award_type_enum not in AwardType.NON_JUDGED_NON_TEAM_AWARDS:
                if award.award_type_enum == AwardType.CHAIRMANS:
                    point_value = 10
                elif award.award_type_enum in {AwardType.ENGINEERING_INSPIRATION, AwardType.ROOKIE_ALL_STAR}:
                    point_value = 8
                else:
                    point_value = 5
                for team in award.team_list:
                    data['points'][team.id()]['award_points'] += point_value * POINTS_MULTIPLIER

        for team, point_breakdown in data['points'].items():
            for p in point_breakdown.values():
                data['points'][team]['total'] += p

        event.district_points_json = json.dumps(data)
        event.dirty = True  # This is so hacky. -fangeugene 2014-05-08
        EventManipulator.createOrUpdate(event)

        self.response.out.write(event.district_points)
