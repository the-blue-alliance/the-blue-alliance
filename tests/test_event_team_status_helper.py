import json

import unittest2
from appengine_fixture_loader.loader import load_fixture
from google.appengine.ext import testbed
from google.appengine.ext import ndb

from helpers.event_team_status_helper import EventTeamStatusHelper
from models.event import Event
from models.event_details import EventDetails
from models.match import Match


class TestEventTeamStatusHelper(unittest2.TestCase):

    status_359 = '{"rank": {"first_sort": 39.0, "breakdown": "Ranking Score: 39.0, Auto: 310.0, Scale/Challenge: 165.0, Goals: 448.0, Defense: 600.0, Record (W-L-T): 11-1-0, Played: 12", "record": "11-1-0", "played": 12, "rank": 1, "total": 36}, "playoff": {"level": "f", "record": "6-1-0", "status": "won"}, "alliance": {"name": "Alliance 1", "backup": null, "position": 0}}'
    status_5240 = '{"rank": {"first_sort": 28.0, "breakdown": "Ranking Score: 28.0, Auto: 260.0, Scale/Challenge: 150.0, Goals: 191.0, Defense: 575.0, Record (W-L-T): 9-3-0, Played: 12", "record": "9-3-0", "played": 12, "rank": 6, "total": 36}, "playoff": {"level": "sf", "record": "2-3-0", "status": "eliminated"}, "alliance": {"name": "Alliance 4", "backup": null, "position": 1}}'
    status_229 = '{"rank": {"first_sort": 20.0, "breakdown": "Ranking Score: 20.0, Auto: 156.0, Scale/Challenge: 130.0, Goals: 119.0, Defense: 525.0, Record (W-L-T): 6-6-0, Played: 12", "record": "6-6-0", "played": 12, "rank": 20, "total": 36}, "playoff": {"level": "f", "record": "5-3-0", "status": "eliminated"}, "alliance": {"name": "Alliance 2", "backup": {"out": "frc229", "in": "frc1665"}, "position": 2}}'
    status_1665 = '{"rank": {"first_sort": 20.0, "breakdown": "Ranking Score: 20.0, Auto: 192.0, Scale/Challenge: 105.0, Goals: 146.0, Defense: 525.0, Record (W-L-T): 6-6-0, Played: 12", "record": "6-6-0", "played": 12, "rank": 18, "total": 36}, "playoff": {"level": "f", "record": "5-3-0", "status": "eliminated"}, "alliance": {"name": "Alliance 2", "backup": {"out": "frc229", "in": "frc1665"}, "position": -1}}'
    status_5964 = '{"rank": {"rank": 23, "played": 12, "breakdown": "Ranking Score: 19.0, Auto: 218.0, Scale/Challenge: 110.0, Goals: 159.0, Defense: 520.0, Record (W-L-T): 6-6-0, Played: 12", "first_sort": 19.0, "total": 36, "record": "6-6-0"}, "alliance": null, "playoff": null}'
    status_1124 = '{"rank": null, "alliance": null, "playoff": null}'

    # Because I can't figure out how to get these to generate
    def event_key_adder(self, obj):
        obj.event = ndb.Key(Event, '2016nytr')

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        load_fixture('test_data/event_team_status.json',
                      kind={'EventDetails': EventDetails, 'Event': Event, 'Match': Match},
                      post_processor=self.event_key_adder)
        self.event = Event.get_by_id('2016nytr')
        self.assertIsNotNone(self.event)

    def tearDown(self):
        self.testbed.deactivate()

    def testEventWinner(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc359', self.event)
        expected = json.loads(self.status_359)
        self.assertDictEqual(status, expected)

    def testElimSemisAndFirstPick(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc5240', self.event)
        expected = json.loads(self.status_5240)
        self.assertDictEqual(status, expected)

    def testBackupOut(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc229', self.event)
        expected = json.loads(self.status_229)
        self.assertDictEqual(status, expected)

    def testBackupIn(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc1665', self.event)
        expected = json.loads(self.status_1665)
        self.assertDictEqual(status, expected)

    def testTeamNotPicked(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc5964', self.event)
        expected = json.loads(self.status_5964)
        self.assertDictEqual(status, expected)

    def testTeamNotThere(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc1124', self.event)
        expected = json.loads(self.status_1124)
        self.assertDictEqual(status, expected)

