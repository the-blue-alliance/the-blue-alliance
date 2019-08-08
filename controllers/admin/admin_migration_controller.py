import os
import json
import logging
import tba_config
from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from google.appengine.ext import deferred
from google.appengine.ext.webapp import template
from controllers.base_controller import LoggedInHandler
from datafeeds.datafeed_fms_api import DatafeedFMSAPI
from models.event import Event
from models.event_details import EventDetails
from models.match import Match
from helpers.event_details_manipulator import EventDetailsManipulator
from helpers.match_helper import MatchHelper
from helpers.match_manipulator import MatchManipulator
from helpers.rankings_helper import RankingsHelper


def create_event_details(event_key):
    event = Event.get_by_id(event_key)
    if event.alliance_selections or event.district_points or event.matchstats or event.rankings:
        event_details = EventDetails(
            id=event_key,
            alliance_selections=event.alliance_selections,
            district_points=event.district_points,
            matchstats=event.matchstats,
            rankings=event.rankings)
        EventDetailsManipulator.createOrUpdate(event_details)


class AdminMigration(LoggedInHandler):
    def get(self):
        self._require_admin()
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/migration.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminMigrationCreateEventDetails(LoggedInHandler):
    def get(self):
        self._require_admin()
        for event_key in Event.query().fetch(keys_only=True):
            deferred.defer(create_event_details, event_key.id(), _queue="admin")

        self.response.out.write("DONE")


class AdminMigrationRankings(LoggedInHandler):
    def get(self, year):
        self._require_admin()

        event_keys = Event.query(Event.year==int(year)).fetch(keys_only=True)
        event_details = ndb.get_multi([ndb.Key(EventDetails, key.id()) for key in event_keys])
        updated = []
        for event_detail in event_details:
            if event_detail:
                logging.info(event_detail.key.id())
                event_detail.rankings2 = RankingsHelper.convert_rankings(event_detail)
                updated.append(event_detail)
        EventDetailsManipulator.createOrUpdate(updated)

        self.response.out.write("DONE")


class AdminMigrationPlayoffAdvancementAll(LoggedInHandler):
    def get(self):
        VALID_YEARS = tba_config.VALID_YEARS
        for year in VALID_YEARS:
                        taskqueue.add(url='/admin/migration/backfill_playoff_advancement/{}'.format(year),
                                      method='GET')
        self.response.out.write("Enqueued migrations for {} - {}".format(VALID_YEARS[0], VALID_YEARS[-1]))


class AdminMigrationPlayoffAdvancement(LoggedInHandler):
    def get(self, year):
        self._require_admin()

        event_keys = Event.query(Event.year==int(year)).fetch(keys_only=True)
        for event_key in event_keys:
            taskqueue.add(url='/tasks/math/do/playoff_advancement_update/{}'.format(event_key.id()),
                          method='GET')

        self.response.out.write("Enqueued {} migrations".format(len(event_keys)))


class AdminMigrationAddSurrogates(LoggedInHandler):
    def get(self, year):
        self._require_admin()

        events = Event.query(Event.year==int(year)).fetch()
        for event in events:
            deferred.defer(MatchHelper.add_surrogates, event, _queue="admin")

        self.response.out.write("DONE")


class AdminMigrationBackfillYearDQ(LoggedInHandler):
    def get(self, year):
        self._require_admin()    # This technically isn't needed because of app.yaml

        event_keys = Event.query(
            Event.year==int(year),
            Event.official==True,
        ).fetch(keys_only=True)
        for event_key in event_keys:
            taskqueue.add(
                url='/admin/migration/backfill_event_dq/{}'.format(event_key.id()),
                method='GET',
                queue_name='admin',
                )

        self.response.out.write("DONE")


class AdminMigrationBackfillEventDQ(LoggedInHandler):
    def get(self, event_key):
        df = DatafeedFMSAPI('v2.0', save_response=True)
        updated_matches = []
        for m1 in df.getMatches(event_key):
            m2 = m1.key.get()
            # Only update if teams and scores are equal
            if m2 and (m1.alliances['red']['teams'] == m2.alliances['red']['teams'] and
                    m1.alliances['blue']['teams'] == m2.alliances['blue']['teams'] and
                    m1.alliances['red']['score'] == m2.alliances['red']['score'] and
                    m1.alliances['blue']['score'] == m2.alliances['blue']['score']):
                old_alliances = m2.alliances
                old_alliances['red']['dqs'] = m1.alliances['red']['dqs']
                old_alliances['blue']['dqs'] = m1.alliances['blue']['dqs']
                m2.alliances_json = json.dumps(old_alliances)
                updated_matches.append(m2)
            else:
                logging.warning("Match not equal: {}".format(m1.key.id()))
        MatchManipulator.createOrUpdate(updated_matches)

        self.response.out.write("DONE")
