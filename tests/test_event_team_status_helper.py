import json

import unittest2
from appengine_fixture_loader.loader import load_fixture
from google.appengine.ext import testbed
from google.appengine.ext import ndb

from helpers.event_team_status_helper import EventTeamStatusHelper
from models.event import Event
from models.event_details import EventDetails
from models.match import Match


class Test2016EventTeamStatusHelper(unittest2.TestCase):
    status_359 = {
        "qual": {
            "rank": 1,
            "total": 36,
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
            "rank": 6,
            "total": 36,
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
            "rank": 20,
            "total": 36,
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
            "rank": 18,
            "total": 36,
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
            "rank": 23,
            "total": 36,
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

        load_fixture('test_data/event_team_status.json',
                      kind={'EventDetails': EventDetails, 'Event': Event, 'Match': Match},
                      post_processor=self.event_key_adder)
        self.event = Event.get_by_id('2016nytr')
        self.assertIsNotNone(self.event)

    def tearDown(self):
        self.testbed.deactivate()

    def testEventWinner(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc359', self.event)
        self.assertDictEqual(status, self.status_359)

    def testElimSemisAndFirstPick(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc5240', self.event)
        self.assertDictEqual(status, self.status_5240)

    def testBackupOut(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc229', self.event)
        self.assertDictEqual(status, self.status_229)

    def testBackupIn(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc1665', self.event)
        self.assertDictEqual(status, self.status_1665)

    def testTeamNotPicked(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc5964', self.event)
        self.assertDictEqual(status, self.status_5964)

    def testTeamNotThere(self):
        status = EventTeamStatusHelper.generate_team_at_event_status('frc1124', self.event)
        self.assertDictEqual(status, self.status_1124)
