import json

import unittest2
from appengine_fixture_loader.loader import load_fixture
from google.appengine.ext import testbed
from google.appengine.ext import ndb

from helpers.event_simulator import EventSimulator
from helpers.event_team_status_helper import EventTeamStatusHelper
from models.event import Event
from models.event_details import EventDetails
from models.match import Match


class TestSimulated2016nytrEventTeamStatusHelper(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_taskqueue_stub(root_path=".")
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

    def tearDown(self):
        self.testbed.deactivate()

    def testSimulatedEvent(self):
        es = EventSimulator()
        event = Event.get_by_id('2016nytr')
        status = EventTeamStatusHelper.generate_team_at_event_status('frc359', event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc359', status),
            None)

        es.step()
        event = Event.get_by_id('2016nytr')
        status = EventTeamStatusHelper.generate_team_at_event_status('frc359', event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc359', status),
            'Team 359 is <b>Rank 15/36</b> with a record of <b>0-0-0</b> in quals.')

        for _ in xrange(5):
            es.step()
        event = Event.get_by_id('2016nytr')
        status = EventTeamStatusHelper.generate_team_at_event_status('frc359', event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc359', status),
            'Team 359 is <b>Rank 6/36</b> with a record of <b>1-0-0</b> in quals.')

        for _ in xrange(67):
            es.step()
        event = Event.get_by_id('2016nytr')
        status = EventTeamStatusHelper.generate_team_at_event_status('frc359', event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc359', status),
            'Team 359 was <b>Rank 1/36</b> with a record of <b>11-1-0</b> in quals.')

        es.step()
        event = Event.get_by_id('2016nytr')
        status = EventTeamStatusHelper.generate_team_at_event_status('frc359', event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc359', status),
            'Team 359 was <b>Rank 1/36</b> with a record of <b>11-1-0</b> in quals and will be competing in the playoffs as the <b>Captain</b> of <b>Alliance 1</b>.')

        es.step()  # QF schedule added
        event = Event.get_by_id('2016nytr')
        status = EventTeamStatusHelper.generate_team_at_event_status('frc359', event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc359', status),
            'Team 359 is <b>0-0-0</b> in the <b>Quarterfinals</b> as the <b>Captain</b> of <b>Alliance 1</b>.')

        es.step()  # qf1m1
        event = Event.get_by_id('2016nytr')
        status = EventTeamStatusHelper.generate_team_at_event_status('frc359', event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc359', status),
            'Team 359 is <b>1-0-0</b> in the <b>Quarterfinals</b> as the <b>Captain</b> of <b>Alliance 1</b>.')

        es.step()  # qf2m1
        es.step()  # qf3m1
        es.step()  # qf4m1
        es.step()  # qf1m2
        event = Event.get_by_id('2016nytr')
        status = EventTeamStatusHelper.generate_team_at_event_status('frc359', event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc359', status),
            'Team 359 is <b>0-0-0</b> in the <b>Semifinals</b> as the <b>Captain</b> of <b>Alliance 1</b>.')

        es.step()  # qf2m2
        es.step()  # qf3m2
        es.step()  # qf4m2
        es.step()  # qf2m3
        es.step()  # qf4m3
        es.step()  # sf1m1
        event = Event.get_by_id('2016nytr')
        status = EventTeamStatusHelper.generate_team_at_event_status('frc359', event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc359', status),
            'Team 359 is <b>1-0-0</b> in the <b>Semifinals</b> as the <b>Captain</b> of <b>Alliance 1</b>.')

        es.step()  # sf2m1
        es.step()  # sf1m2
        event = Event.get_by_id('2016nytr')
        status = EventTeamStatusHelper.generate_team_at_event_status('frc359', event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc359', status),
            'Team 359 is <b>0-0-0</b> in the <b>Finals</b> as the <b>Captain</b> of <b>Alliance 1</b>.')

        es.step()  # sf2m2
        es.step()  # sf2m3
        es.step()  # f1m1
        event = Event.get_by_id('2016nytr')
        status = EventTeamStatusHelper.generate_team_at_event_status('frc359', event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc359', status),
            'Team 359 is <b>1-0-0</b> in the <b>Finals</b> as the <b>Captain</b> of <b>Alliance 1</b>.')

        es.step()  # f1m2
        event = Event.get_by_id('2016nytr')
        status = EventTeamStatusHelper.generate_team_at_event_status('frc359', event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc359', status),
            'Team 359 is <b>1-1-0</b> in the <b>Finals</b> as the <b>Captain</b> of <b>Alliance 1</b>.')

        es.step()  # f1m3
        event = Event.get_by_id('2016nytr')
        status = EventTeamStatusHelper.generate_team_at_event_status('frc359', event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc359', status),
            'Team 359 was <b>Rank 1/36</b> with a record of <b>11-1-0</b> in quals, competed in the playoffs as the <b>Captain</b> of <b>Alliance 1</b>, and <b>won the event</b> with a playoff record of <b>6-1-0</b>.')


class Test2016nytrEventTeamStatusHelper(unittest2.TestCase):
    status_359 = {
        "qual": {
            "status": "completed",
            "rank": 1,
            "max_rank": 36,
            "matches_played": 12,
            "dq": 0,
            "record": {
                "wins": 11,
                "losses": 1,
                "ties": 0
            },
            "qual_average": None,
            "ranking_sort_orders": [
                {
                  "name": "Ranking Score",
                  "precision": 0,
                  "value": 39
                },
                {
                  "name": "Auto",
                  "precision": 0,
                  "value": 310
                },
                {
                  "name": "Scale/Challenge",
                  "precision": 0,
                  "value": 165
                },
                {
                  "name": "Goals",
                  "precision": 0,
                  "value": 448
                },
                {
                  "name": "Defense",
                  "precision": 0,
                  "value": 600
                }
            ],
        },
        "playoff": {
            "level": "f",
            "record": {
                "wins": 6,
                "losses": 1,
                "ties": 0
            },
            "current_level_record": {
                "wins": 2,
                "losses": 1,
                "ties": 0
            },
            "playoff_average": None,
            "status": "won"
        },
        "alliance": {
            "name": "Alliance 1",
            "number": 1,
            "backup": None,
            "pick": 0
        }
    }

    status_5240 = {
        "qual": {
            "status": "completed",
            "rank": 6,
            "max_rank": 36,
            "matches_played": 12,
            "dq": 0,
            "record": {
                "wins": 9,
                "losses": 3,
                "ties": 0
            },
            "qual_average": None,
            "ranking_sort_orders": [
                {
                  "name": "Ranking Score",
                  "precision": 0,
                  "value": 28
                },
                {
                  "name": "Auto",
                  "precision": 0,
                  "value": 260
                },
                {
                  "name": "Scale/Challenge",
                  "precision": 0,
                  "value": 150
                },
                {
                  "name": "Goals",
                  "precision": 0,
                  "value": 191
                },
                {
                  "name": "Defense",
                  "precision": 0,
                  "value": 575
                }
            ],
        },
        "playoff": {
            "level": "sf",
            "record": {
                "wins": 2,
                "losses": 3,
                "ties": 0
            },
            "current_level_record": {
                "wins": 0,
                "losses": 2,
                "ties": 0
            },
            "playoff_average": None,
            "status": "eliminated"
        },
        "alliance": {
            "name": "Alliance 4",
            "number": 4,
            "backup": None,
            "pick": 1
        }
    }

    status_229 = {
        "qual": {
            "status": "completed",
            "rank": 20,
            "max_rank": 36,
            "matches_played": 12,
            "dq": 0,
            "record": {
                "wins": 6,
                "losses": 6,
                "ties": 0
            },
            "qual_average": None,
            "ranking_sort_orders": [
                {
                  "name": "Ranking Score",
                  "precision": 0,
                  "value": 20
                },
                {
                  "name": "Auto",
                  "precision": 0,
                  "value": 156
                },
                {
                  "name": "Scale/Challenge",
                  "precision": 0,
                  "value": 130
                },
                {
                  "name": "Goals",
                  "precision": 0,
                  "value": 119
                },
                {
                  "name": "Defense",
                  "precision": 0,
                  "value": 525
                }
            ],
        },
        "playoff": {
            "level": "f",
            "record": {
                "wins": 5,
                "losses": 3,
                "ties": 0
            },
            "current_level_record": {
                "wins": 1,
                "losses": 2,
                "ties": 0
            },
            "playoff_average": None,
            "status": "eliminated"
        },
        "alliance": {
            "name": "Alliance 2",
            "number": 2,
            "backup": {"out": "frc229", "in": "frc1665"},
            "pick": 2
        }

    }

    status_1665 = {
        "qual": {
            "status": "completed",
            "rank": 18,
            "max_rank": 36,
            "matches_played": 12,
            "dq": 0,
            "record": {
                "wins": 6,
                "losses": 6,
                "ties": 0
            },
            "qual_average": None,
            "ranking_sort_orders": [
                {
                  "name": "Ranking Score",
                  "precision": 0,
                  "value": 20
                },
                {
                  "name": "Auto",
                  "precision": 0,
                  "value": 192
                },
                {
                  "name": "Scale/Challenge",
                  "precision": 0,
                  "value": 105
                },
                {
                  "name": "Goals",
                  "precision": 0,
                  "value": 146
                },
                {
                  "name": "Defense",
                  "precision": 0,
                  "value": 525
                }
            ],
        },
        "playoff": {
            "level": "f",
            "record": {
                "wins": 5,
                "losses": 3,
                "ties": 0
            },
            "current_level_record": {
                "wins": 1,
                "losses": 2,
                "ties": 0
            },
            "playoff_average": None,
            "status": "eliminated"
        },
        "alliance": {
            "name": "Alliance 2",
            "number": 2,
            "backup": {"out": "frc229", "in": "frc1665"},
            "pick": -1
        }

    }

    status_5964 = {
        "qual": {
            "status": "completed",
            "rank": 23,
            "max_rank": 36,
            "matches_played": 12,
            "dq": 0,
            "record": {
                "wins": 6,
                "losses": 6,
                "ties": 0
            },
            "qual_average": None,
            "ranking_sort_orders": [
                {
                  "name": "Ranking Score",
                  "precision": 0,
                  "value": 19
                },
                {
                  "name": "Auto",
                  "precision": 0,
                  "value": 218
                },
                {
                  "name": "Scale/Challenge",
                  "precision": 0,
                  "value": 110
                },
                {
                  "name": "Goals",
                  "precision": 0,
                  "value": 159
                },
                {
                  "name": "Defense",
                  "precision": 0,
                  "value": 520
                }
            ],
        },
        "playoff": None,
        "alliance": None
    }

    status_1124 = {
        "qual": None,
        "playoff": None,
        "alliance": None
    }

    # Because I can't figure out how to get these to generate
    def event_key_adder(self, obj):
        obj.event = ndb.Key(Event, '2016nytr')

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        load_fixture('test_data/fixtures/2016nytr_event_team_status.json',
                      kind={'EventDetails': EventDetails, 'Event': Event, 'Match': Match},
                      post_processor=self.event_key_adder)
        self.event = Event.get_by_id('2016nytr')
        self.assertIsNotNone(self.event)

    def tearDown(self):
        self.testbed.deactivate()

    def testEventWinner(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc359', self.event)
        self.assertDictEqual(status, self.status_359)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc359', status),
            'Team 359 was <b>Rank 1/36</b> with a record of <b>11-1-0</b> in quals, competed in the playoffs as the <b>Captain</b> of <b>Alliance 1</b>, and <b>won the event</b> with a playoff record of <b>6-1-0</b>.')

    def testElimSemisAndFirstPick(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc5240', self.event)
        self.assertDictEqual(status, self.status_5240)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc5240', status),
            'Team 5240 was <b>Rank 6/36</b> with a record of <b>9-3-0</b> in quals, competed in the playoffs as the <b>1st Pick</b> of <b>Alliance 4</b>, and was <b>eliminated in the Semifinals</b> with a playoff record of <b>2-3-0</b>.')

    def testBackupOut(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc229', self.event)
        self.assertDictEqual(status, self.status_229)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc229', status),
            'Team 229 was <b>Rank 20/36</b> with a record of <b>6-6-0</b> in quals, competed in the playoffs as the <b>2nd Pick</b> of <b>Alliance 2</b>, and was <b>eliminated in the Finals</b> with a playoff record of <b>5-3-0</b>.')

    def testBackupIn(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc1665', self.event)
        self.assertDictEqual(status, self.status_1665)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc1665', status),
            'Team 1665 was <b>Rank 18/36</b> with a record of <b>6-6-0</b> in quals, competed in the playoffs as the <b>Backup</b> of <b>Alliance 2</b>, and was <b>eliminated in the Finals</b> with a playoff record of <b>5-3-0</b>.')

    def testTeamNotPicked(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc5964', self.event)
        self.assertDictEqual(status, self.status_5964)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc5964', status),
            'Team 5964 was <b>Rank 23/36</b> with a record of <b>6-6-0</b> in quals.')

    def testTeamNotThere(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc1124', self.event)
        self.assertDictEqual(status, self.status_1124)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc1124', status),
            None)


class Test2016nytrEventTeamStatusHelperNoEventDetails(unittest2.TestCase):
    status_359 = {
        "qual": {
            "status": "completed",
            "rank": None,
            "max_rank": 36,
            "matches_played": 12,
            "dq": None,
            "record": {
                "wins": 11,
                "losses": 1,
                "ties": 0
            },
            "qual_average": None,
            "ranking_sort_orders": None,
        },
        "playoff": {
            "level": "f",
            "record": {
                "wins": 6,
                "losses": 1,
                "ties": 0
            },
            "current_level_record": {
                "wins": 2,
                "losses": 1,
                "ties": 0
            },
            "playoff_average": None,
            "status": "won"
        },
        "alliance": None
    }

    status_5240 = {
        "qual": {
            "status": "completed",
            "rank": None,
            "max_rank": 36,
            "matches_played": 12,
            "dq": None,
            "record": {
                "wins": 9,
                "losses": 3,
                "ties": 0
            },
            "qual_average": None,
            "ranking_sort_orders": None,
        },
        "playoff": {
            "level": "sf",
            "record": {
                "wins": 2,
                "losses": 3,
                "ties": 0
            },
            "current_level_record": {
                "wins": 0,
                "losses": 2,
                "ties": 0
            },
            "playoff_average": None,
            "status": "eliminated"
        },
        "alliance": None
    }

    status_229 = {
        "qual": {
            "status": "completed",
            "rank": None,
            "max_rank": 36,
            "matches_played": 12,
            "dq": None,
            "record": {
                "wins": 6,
                "losses": 6,
                "ties": 0
            },
            "qual_average": None,
            "ranking_sort_orders": None,
        },
        "playoff": {
            "level": "f",
            "record": {
                "wins": 5,
                "losses": 3,
                "ties": 0
            },
            "current_level_record": {
                "wins": 1,
                "losses": 2,
                "ties": 0
            },
            "playoff_average": None,
            "status": "eliminated"
        },
        "alliance": None

    }

    status_1665 = {
        "qual": {
            "status": "completed",
            "rank": None,
            "max_rank": 36,
            "matches_played": 12,
            "dq": None,
            "record": {
                "wins": 6,
                "losses": 6,
                "ties": 0
            },
            "qual_average": None,
            "ranking_sort_orders": None,
        },
        "playoff": {
            "level": "f",
            "record": {
                "wins": 5,
                "losses": 3,
                "ties": 0
            },
            "current_level_record": {
                "wins": 1,
                "losses": 2,
                "ties": 0
            },
            "playoff_average": None,
            "status": "eliminated"
        },
        "alliance": None

    }

    status_5964 = {
        "qual": {
            "status": "completed",
            "rank": None,
            "max_rank": 36,
            "matches_played": 12,
            "dq": None,
            "record": {
                "wins": 6,
                "losses": 6,
                "ties": 0
            },
            "qual_average": None,
            "ranking_sort_orders": None
        },
        "playoff": None,
        "alliance": None
    }

    status_1124 = {
        "qual": None,
        "playoff": None,
        "alliance": None
    }

    # Because I can't figure out how to get these to generate
    def event_key_adder(self, obj):
        obj.event = ndb.Key(Event, '2016nytr')

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        load_fixture('test_data/fixtures/2016nytr_event_team_status.json',
                      kind={'EventDetails': EventDetails, 'Event': Event, 'Match': Match},
                      post_processor=self.event_key_adder)
        self.event = Event.get_by_id('2016nytr')
        EventDetails.get_by_id('2016nytr').key.delete()  # Remove EventDetails
        self.assertIsNotNone(self.event)

    def tearDown(self):
        self.testbed.deactivate()

    def testEventWinner(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc359', self.event)
        self.assertDictEqual(status, self.status_359)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc359', status),
            'Team 359 had a record of <b>11-1-0</b> in quals and <b>won the event</b> with a playoff record of <b>6-1-0</b>.')

    def testElimSemisAndFirstPick(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc5240', self.event)
        self.assertDictEqual(status, self.status_5240)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc5240', status),
            'Team 5240 had a record of <b>9-3-0</b> in quals and was <b>eliminated in the Semifinals</b> with a playoff record of <b>2-3-0</b>.')

    def testBackupOut(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc229', self.event)
        self.assertDictEqual(status, self.status_229)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc229', status),
            'Team 229 had a record of <b>6-6-0</b> in quals and was <b>eliminated in the Finals</b> with a playoff record of <b>5-3-0</b>.')

    def testBackupIn(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc1665', self.event)
        self.assertDictEqual(status, self.status_1665)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc1665', status),
            'Team 1665 had a record of <b>6-6-0</b> in quals and was <b>eliminated in the Finals</b> with a playoff record of <b>5-3-0</b>.')

    def testTeamNotPicked(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc5964', self.event)
        self.assertDictEqual(status, self.status_5964)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc5964', status),
            'Team 5964 had a record of <b>6-6-0</b> in quals.')

    def testTeamNotThere(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc1124', self.event)
        self.assertDictEqual(status, self.status_1124)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc1124', status),
            None)


class Test2016casjEventTeamStatusHelperNoEventDetails(unittest2.TestCase):
    status_254 = {
        "qual": {
            "status": "completed",
            "rank": None,
            "max_rank": 64,
            "matches_played": 8,
            "dq": None,
            "record": {
                "wins": 8,
                "losses": 0,
                "ties": 0
            },
            "qual_average": None,
            "ranking_sort_orders": None,
        },
        "playoff": {
            "level": "f",
            "record": {
                "wins": 6,
                "losses": 0,
                "ties": 0
            },
            "current_level_record": {
                "wins": 2,
                "losses": 0,
                "ties": 0
            },
            "playoff_average": None,
            "status": "won"
        },
        "alliance": None
    }

    # Because I can't figure out how to get these to generate
    def event_key_adder(self, obj):
        obj.event = ndb.Key(Event, '2016casj')

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        load_fixture('test_data/fixtures/2016casj.json',
                      kind={'EventDetails': EventDetails, 'Event': Event, 'Match': Match},
                      post_processor=self.event_key_adder)
        self.event = Event.get_by_id('2016casj')
        self.assertIsNotNone(self.event)

    def tearDown(self):
        self.testbed.deactivate()

    def testEventSurrogate(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc254', self.event)
        self.assertDictEqual(status, self.status_254)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc254', status),
            'Team 254 had a record of <b>8-0-0</b> in quals and <b>won the event</b> with a playoff record of <b>6-0-0</b>.')


class Test2015casjEventTeamStatusHelper(unittest2.TestCase):
    status_254 = {
        "qual": {
            "status": "completed",
            "rank": 1,
            "max_rank": 57,
            "matches_played": 10,
            "dq": 0,
            "record": None,
            "qual_average": 200.4,
            "ranking_sort_orders": [
                {
                  "name": "Qual Avg.",
                  "precision": 1,
                  "value": 200.4
                },
                {
                  "name": "Coopertition",
                  "precision": 0,
                  "value": 280
                },
                {
                  "name": "Auto",
                  "precision": 0,
                  "value": 200
                },
                {
                  "name": "Container",
                  "precision": 0,
                  "value": 836
                },
                {
                  "name": "Tote",
                  "precision": 0,
                  "value": 522
                },
                {
                  "name": "Litter",
                  "precision": 0,
                  "value": 166
                }
            ],
        },
        "playoff": {
            "level": "f",
            "record": None,
            "current_level_record": {
                "wins": 2,
                "losses": 0,
                "ties": 0
            },
            "playoff_average": 224.14285714285714,
            "status": "won"
        },
        "alliance": {
            "name": "Alliance 1",
            "number": 1,
            "backup": None,
            "pick": 0
        }
    }

    status_846 = {
        "qual": {
            "status": "completed",
            "rank": 8,
            "max_rank": 57,
            "matches_played": 10,
            "dq": 0,
            "record": None,
            "qual_average": 97.0,
            "ranking_sort_orders": [
                {
                  "name": "Qual Avg.",
                  "precision": 1,
                  "value": 97.0
                },
                {
                  "name": "Coopertition",
                  "precision": 0,
                  "value": 200
                },
                {
                  "name": "Auto",
                  "precision": 0,
                  "value": 20
                },
                {
                  "name": "Container",
                  "precision": 0,
                  "value": 372
                },
                {
                  "name": "Tote",
                  "precision": 0,
                  "value": 294
                },
                {
                  "name": "Litter",
                  "precision": 0,
                  "value": 108
                }
            ],
        },
        "playoff": {
            "level": "sf",
            "record": None,
            "current_level_record": None,
            "playoff_average": 133.6,
            "status": "eliminated"
        },
        "alliance": {
            "name": "Alliance 3",
            "number": 3,
            "backup": None,
            "pick": 1
        }
    }

    status_8 = {
        "qual": {
            "status": "completed",
            "rank": 53,
            "max_rank": 57,
            "matches_played": 10,
            "dq": 0,
            "record": None,
            "qual_average": 42.6,
            "ranking_sort_orders": [
                {
                  "name": "Qual Avg.",
                  "precision": 1,
                  "value": 42.6
                },
                {
                  "name": "Coopertition",
                  "precision": 0,
                  "value": 120
                },
                {
                  "name": "Auto",
                  "precision": 0,
                  "value": 0
                },
                {
                  "name": "Container",
                  "precision": 0,
                  "value": 84
                },
                {
                  "name": "Tote",
                  "precision": 0,
                  "value": 150
                },
                {
                  "name": "Litter",
                  "precision": 0,
                  "value": 72
                }
            ],
        },
        "playoff": None,
        "alliance": None
    }

    status_1124 = {
        "qual": None,
        "playoff": None,
        "alliance": None
    }

    # Because I can't figure out how to get these to generate
    def event_key_adder(self, obj):
        obj.event = ndb.Key(Event, '2015casj')

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        load_fixture('test_data/fixtures/2015casj.json',
                      kind={'EventDetails': EventDetails, 'Event': Event, 'Match': Match},
                      post_processor=self.event_key_adder)
        self.event = Event.get_by_id('2015casj')
        self.assertIsNotNone(self.event)

    def tearDown(self):
        self.testbed.deactivate()

    def testEventWinner(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc254', self.event)
        self.assertDictEqual(status, self.status_254)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc254', status),
            'Team 254 was <b>Rank 1/57</b> with an average score of <b>200.4</b> in quals, competed in the playoffs as the <b>Captain</b> of <b>Alliance 1</b>, and <b>won the event</b> with a playoff average of <b>224.1</b>.')

    def testElimSemisAndFirstPick(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc846', self.event)
        self.assertDictEqual(status, self.status_846)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc846', status),
            'Team 846 was <b>Rank 8/57</b> with an average score of <b>97.0</b> in quals, competed in the playoffs as the <b>1st Pick</b> of <b>Alliance 3</b>, and was <b>eliminated in the Semifinals</b> with a playoff average of <b>133.6</b>.')

    def testTeamNotPicked(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc8', self.event)
        self.assertDictEqual(status, self.status_8)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc8', status),
            'Team 8 was <b>Rank 53/57</b> with an average score of <b>42.6</b> in quals.')

    def testTeamNotThere(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc1124', self.event)
        self.assertDictEqual(status, self.status_1124)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc1124', status),
            None)


class Test2015casjEventTeamStatusHelperNoEventDetails(unittest2.TestCase):
    status_254 = {
        "qual": {
            "status": "completed",
            "rank": None,
            "max_rank": 57,
            "matches_played": 10,
            "dq": None,
            "record": None,
            "qual_average": 200.4,
            "ranking_sort_orders": None,
        },
        "playoff": {
            "level": "f",
            "record": None,
            "current_level_record": {
                "wins": 2,
                "losses": 0,
                "ties": 0
            },
            "playoff_average": 224.14285714285714,
            "status": "won"
        },
        "alliance": None
    }

    status_846 = {
        "qual": {
            "status": "completed",
            "rank": None,
            "max_rank": 57,
            "matches_played": 10,
            "dq": None,
            "record": None,
            "qual_average": 97.0,
            "ranking_sort_orders": None,
        },
        "playoff": {
            "level": "sf",
            "record": None,
            "current_level_record": None,
            "playoff_average": 133.6,
            "status": "eliminated"
        },
        "alliance": None
    }

    status_8 = {
        "qual": {
            "status": "completed",
            "rank": None,
            "max_rank": 57,
            "matches_played": 10,
            "dq": None,
            "record": None,
            "qual_average": 42.6,
            "ranking_sort_orders": None,
        },
        "playoff": None,
        "alliance": None
    }

    status_1124 = {
        "qual": None,
        "playoff": None,
        "alliance": None
    }

    # Because I can't figure out how to get these to generate
    def event_key_adder(self, obj):
        obj.event = ndb.Key(Event, '2015casj')

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        load_fixture('test_data/fixtures/2015casj.json',
                      kind={'EventDetails': EventDetails, 'Event': Event, 'Match': Match},
                      post_processor=self.event_key_adder)
        self.event = Event.get_by_id('2015casj')
        EventDetails.get_by_id('2015casj').key.delete()  # Remove EventDetails
        self.assertIsNotNone(self.event)

    def tearDown(self):
        self.testbed.deactivate()

    def testEventWinner(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc254', self.event)
        self.assertDictEqual(status, self.status_254)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc254', status),
            'Team 254 had an average score of <b>200.4</b> in quals and <b>won the event</b> with a playoff average of <b>224.1</b>.')

    def testElimSemisAndFirstPick(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc846', self.event)
        self.assertDictEqual(status, self.status_846)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc846', status),
            'Team 846 had an average score of <b>97.0</b> in quals and was <b>eliminated in the Semifinals</b> with a playoff average of <b>133.6</b>.')

    def testTeamNotPicked(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc8', self.event)
        self.assertDictEqual(status, self.status_8)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc8', status),
            'Team 8 had an average score of <b>42.6</b> in quals.')

    def testTeamNotThere(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc1124', self.event)
        self.assertDictEqual(status, self.status_1124)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string('frc1124', status),
            None)
