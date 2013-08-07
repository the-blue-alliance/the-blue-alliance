import datetime
import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.event_type import EventType
from datafeeds.usfirst_matches_parser import UsfirstMatchesParser
from helpers.event_team_updater import EventTeamUpdater
from models.event import Event
from models.event_team import EventTeam
from models.match import Match
from models.team import Team


def set_up_matches(html, event):
    with open(html, 'r') as f:
        parsed_matches, _ = UsfirstMatchesParser.parse(f.read())
        matches = [Match(
            id=Match.renderKeyName(
                event,
                match.get("comp_level", None),
                match.get("set_number", 0),
                match.get("match_number", 0)),
            event=event.key,
            game=Match.FRC_GAMES_BY_YEAR.get(event.year, "frc_unknown"),
            set_number=match.get("set_number", 0),
            match_number=match.get("match_number", 0),
            comp_level=match.get("comp_level", None),
            team_key_names=match.get("team_key_names", None),
            alliances_json=match.get("alliances_json", None)
            )
            for match in parsed_matches]
        return matches


class TestEventTeamUpdater(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        past_event = Event(
            id="2011tstupdaterpast",
            end_date=datetime.datetime.now() - datetime.timedelta(days=1),
            event_short="tstupdaterpast",
            event_type_enum=EventType.REGIONAL,
            start_date=datetime.datetime.now() - datetime.timedelta(days=2),
            year=2011,
        )
        past_event.put()
        past_event_matches = set_up_matches(
            'test_data/usfirst_html/usfirst_event_matches_2012ct.html',
            past_event)
        for match in past_event_matches:
            match.put()

        future_event = Event(
            id="2011tstupdaterfuture",
            end_date=datetime.datetime.now() + datetime.timedelta(days=2),
            event_short="tstupdaterfuture",
            event_type_enum=EventType.REGIONAL,
            start_date=datetime.datetime.now() + datetime.timedelta(days=1),
            year=2011,
        )
        future_event.put()
        future_event_matches = set_up_matches(
            'test_data/usfirst_html/usfirst_event_matches_2012ct.html',
            future_event)
        for match in future_event_matches:
            match.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_update_past(self):
        teams, event_teams, et_keys_to_delete = EventTeamUpdater.update('2011tstupdaterpast')
        self.assertEqual([team.team_number for team in teams],
                         [95, 178, 176, 1922, 173, 2785, 228, 177, 1099, 175, 1027, 3017, 1493, 118, 229, 2791, 155, 549, 195, 4134, 20, 2836, 869, 1665, 4055, 3555, 126, 1699, 1559, 3464, 2168, 3461, 1991, 3467, 2067, 230, 1124, 3104, 236, 237, 1511, 250, 1880, 558, 694, 571, 3634, 3525, 999, 181, 1073, 3146, 1071, 1740, 3719, 3718, 2170, 663, 4122, 3182, 839, 1784, 3654, 743])
        self.assertEqual(set([et.key_name for et in event_teams]).symmetric_difference({'2011tstupdaterpast_frc95', '2011tstupdaterpast_frc178', '2011tstupdaterpast_frc176', '2011tstupdaterpast_frc1922', '2011tstupdaterpast_frc173', '2011tstupdaterpast_frc2785', '2011tstupdaterpast_frc228', '2011tstupdaterpast_frc177', '2011tstupdaterpast_frc1099', '2011tstupdaterpast_frc175', '2011tstupdaterpast_frc1027', '2011tstupdaterpast_frc3017', '2011tstupdaterpast_frc1493', '2011tstupdaterpast_frc118', '2011tstupdaterpast_frc229', '2011tstupdaterpast_frc2791', '2011tstupdaterpast_frc155', '2011tstupdaterpast_frc549', '2011tstupdaterpast_frc195', '2011tstupdaterpast_frc4134', '2011tstupdaterpast_frc20', '2011tstupdaterpast_frc2836', '2011tstupdaterpast_frc869', '2011tstupdaterpast_frc1665', '2011tstupdaterpast_frc4055', '2011tstupdaterpast_frc3555', '2011tstupdaterpast_frc126', '2011tstupdaterpast_frc1699', '2011tstupdaterpast_frc1559', '2011tstupdaterpast_frc3464', '2011tstupdaterpast_frc2168', '2011tstupdaterpast_frc3461', '2011tstupdaterpast_frc1991', '2011tstupdaterpast_frc3467', '2011tstupdaterpast_frc2067', '2011tstupdaterpast_frc230', '2011tstupdaterpast_frc1124', '2011tstupdaterpast_frc3104', '2011tstupdaterpast_frc236', '2011tstupdaterpast_frc237', '2011tstupdaterpast_frc1511', '2011tstupdaterpast_frc250', '2011tstupdaterpast_frc1880', '2011tstupdaterpast_frc558', '2011tstupdaterpast_frc694', '2011tstupdaterpast_frc571', '2011tstupdaterpast_frc3634', '2011tstupdaterpast_frc3525', '2011tstupdaterpast_frc999', '2011tstupdaterpast_frc181', '2011tstupdaterpast_frc1073', '2011tstupdaterpast_frc3146', '2011tstupdaterpast_frc1071', '2011tstupdaterpast_frc1740', '2011tstupdaterpast_frc3719', '2011tstupdaterpast_frc3718', '2011tstupdaterpast_frc2170', '2011tstupdaterpast_frc663', '2011tstupdaterpast_frc4122', '2011tstupdaterpast_frc3182', '2011tstupdaterpast_frc839', '2011tstupdaterpast_frc1784', '2011tstupdaterpast_frc3654', '2011tstupdaterpast_frc743'}),
                         set())
        self.assertEqual(et_keys_to_delete, set())

        event_team = EventTeam(
            id="%s_%s" % ('2011tstupdaterpast', 'frc9999'),
            event=ndb.Key(Event, '2011tstupdaterpast'),
            team=ndb.Key(Team, 'frc9999'),
            year=None)
        event_team.put()

        teams, event_teams, et_keys_to_delete = EventTeamUpdater.update('2011tstupdaterpast')
        self.assertEqual(set([team.team_number for team in teams]).symmetric_difference({95, 178, 176, 1922, 173, 2785, 228, 177, 1099, 175, 1027, 3017, 1493, 118, 229, 2791, 155, 549, 195, 4134, 20, 2836, 869, 1665, 4055, 3555, 126, 1699, 1559, 3464, 2168, 3461, 1991, 3467, 2067, 230, 1124, 3104, 236, 237, 1511, 250, 1880, 558, 694, 571, 3634, 3525, 999, 181, 1073, 3146, 1071, 1740, 3719, 3718, 2170, 663, 4122, 3182, 839, 1784, 3654, 743}),
                         set())
        self.assertEqual(set([et.key_name for et in event_teams]).symmetric_difference({'2011tstupdaterpast_frc95', '2011tstupdaterpast_frc178', '2011tstupdaterpast_frc176', '2011tstupdaterpast_frc1922', '2011tstupdaterpast_frc173', '2011tstupdaterpast_frc2785', '2011tstupdaterpast_frc228', '2011tstupdaterpast_frc177', '2011tstupdaterpast_frc1099', '2011tstupdaterpast_frc175', '2011tstupdaterpast_frc1027', '2011tstupdaterpast_frc3017', '2011tstupdaterpast_frc1493', '2011tstupdaterpast_frc118', '2011tstupdaterpast_frc229', '2011tstupdaterpast_frc2791', '2011tstupdaterpast_frc155', '2011tstupdaterpast_frc549', '2011tstupdaterpast_frc195', '2011tstupdaterpast_frc4134', '2011tstupdaterpast_frc20', '2011tstupdaterpast_frc2836', '2011tstupdaterpast_frc869', '2011tstupdaterpast_frc1665', '2011tstupdaterpast_frc4055', '2011tstupdaterpast_frc3555', '2011tstupdaterpast_frc126', '2011tstupdaterpast_frc1699', '2011tstupdaterpast_frc1559', '2011tstupdaterpast_frc3464', '2011tstupdaterpast_frc2168', '2011tstupdaterpast_frc3461', '2011tstupdaterpast_frc1991', '2011tstupdaterpast_frc3467', '2011tstupdaterpast_frc2067', '2011tstupdaterpast_frc230', '2011tstupdaterpast_frc1124', '2011tstupdaterpast_frc3104', '2011tstupdaterpast_frc236', '2011tstupdaterpast_frc237', '2011tstupdaterpast_frc1511', '2011tstupdaterpast_frc250', '2011tstupdaterpast_frc1880', '2011tstupdaterpast_frc558', '2011tstupdaterpast_frc694', '2011tstupdaterpast_frc571', '2011tstupdaterpast_frc3634', '2011tstupdaterpast_frc3525', '2011tstupdaterpast_frc999', '2011tstupdaterpast_frc181', '2011tstupdaterpast_frc1073', '2011tstupdaterpast_frc3146', '2011tstupdaterpast_frc1071', '2011tstupdaterpast_frc1740', '2011tstupdaterpast_frc3719', '2011tstupdaterpast_frc3718', '2011tstupdaterpast_frc2170', '2011tstupdaterpast_frc663', '2011tstupdaterpast_frc4122', '2011tstupdaterpast_frc3182', '2011tstupdaterpast_frc839', '2011tstupdaterpast_frc1784', '2011tstupdaterpast_frc3654', '2011tstupdaterpast_frc743'}),
                         set())
        self.assertEqual(set([et_key.id() for et_key in et_keys_to_delete]).symmetric_difference({'2011tstupdaterpast_frc9999'}),
                         set())

    def test_update_future(self):
        teams, event_teams, et_keys_to_delete = EventTeamUpdater.update('2011tstupdaterfuture')
        self.assertEqual([team.team_number for team in teams],
                         [95, 178, 176, 1922, 173, 2785, 228, 177, 1099, 175, 1027, 3017, 1493, 118, 229, 2791, 155, 549, 195, 4134, 20, 2836, 869, 1665, 4055, 3555, 126, 1699, 1559, 3464, 2168, 3461, 1991, 3467, 2067, 230, 1124, 3104, 236, 237, 1511, 250, 1880, 558, 694, 571, 3634, 3525, 999, 181, 1073, 3146, 1071, 1740, 3719, 3718, 2170, 663, 4122, 3182, 839, 1784, 3654, 743])
        self.assertEqual(set([et.key_name for et in event_teams]).symmetric_difference({'2011tstupdaterfuture_frc95', '2011tstupdaterfuture_frc178', '2011tstupdaterfuture_frc176', '2011tstupdaterfuture_frc1922', '2011tstupdaterfuture_frc173', '2011tstupdaterfuture_frc2785', '2011tstupdaterfuture_frc228', '2011tstupdaterfuture_frc177', '2011tstupdaterfuture_frc1099', '2011tstupdaterfuture_frc175', '2011tstupdaterfuture_frc1027', '2011tstupdaterfuture_frc3017', '2011tstupdaterfuture_frc1493', '2011tstupdaterfuture_frc118', '2011tstupdaterfuture_frc229', '2011tstupdaterfuture_frc2791', '2011tstupdaterfuture_frc155', '2011tstupdaterfuture_frc549', '2011tstupdaterfuture_frc195', '2011tstupdaterfuture_frc4134', '2011tstupdaterfuture_frc20', '2011tstupdaterfuture_frc2836', '2011tstupdaterfuture_frc869', '2011tstupdaterfuture_frc1665', '2011tstupdaterfuture_frc4055', '2011tstupdaterfuture_frc3555', '2011tstupdaterfuture_frc126', '2011tstupdaterfuture_frc1699', '2011tstupdaterfuture_frc1559', '2011tstupdaterfuture_frc3464', '2011tstupdaterfuture_frc2168', '2011tstupdaterfuture_frc3461', '2011tstupdaterfuture_frc1991', '2011tstupdaterfuture_frc3467', '2011tstupdaterfuture_frc2067', '2011tstupdaterfuture_frc230', '2011tstupdaterfuture_frc1124', '2011tstupdaterfuture_frc3104', '2011tstupdaterfuture_frc236', '2011tstupdaterfuture_frc237', '2011tstupdaterfuture_frc1511', '2011tstupdaterfuture_frc250', '2011tstupdaterfuture_frc1880', '2011tstupdaterfuture_frc558', '2011tstupdaterfuture_frc694', '2011tstupdaterfuture_frc571', '2011tstupdaterfuture_frc3634', '2011tstupdaterfuture_frc3525', '2011tstupdaterfuture_frc999', '2011tstupdaterfuture_frc181', '2011tstupdaterfuture_frc1073', '2011tstupdaterfuture_frc3146', '2011tstupdaterfuture_frc1071', '2011tstupdaterfuture_frc1740', '2011tstupdaterfuture_frc3719', '2011tstupdaterfuture_frc3718', '2011tstupdaterfuture_frc2170', '2011tstupdaterfuture_frc663', '2011tstupdaterfuture_frc4122', '2011tstupdaterfuture_frc3182', '2011tstupdaterfuture_frc839', '2011tstupdaterfuture_frc1784', '2011tstupdaterfuture_frc3654', '2011tstupdaterfuture_frc743'}),
                         set())
        self.assertEqual(et_keys_to_delete, set())

        event_team = EventTeam(
            id="%s_%s" % ('2011tstupdaterfuture', 'frc9999'),
            event=ndb.Key(Event, '2011tstupdaterfuture'),
            team=ndb.Key(Team, 'frc9999'),
            year=None)
        event_team.put()

        teams, event_teams, et_keys_to_delete = EventTeamUpdater.update('2011tstupdaterfuture')
        self.assertEqual(set([team.team_number for team in teams]).symmetric_difference({95, 178, 176, 1922, 173, 2785, 228, 177, 1099, 175, 1027, 3017, 1493, 118, 229, 2791, 155, 549, 195, 4134, 20, 2836, 869, 1665, 4055, 3555, 126, 1699, 1559, 3464, 2168, 3461, 1991, 3467, 2067, 230, 1124, 3104, 236, 237, 1511, 250, 1880, 558, 694, 571, 3634, 3525, 999, 181, 1073, 3146, 1071, 1740, 3719, 3718, 2170, 663, 4122, 3182, 839, 1784, 3654, 743}),
                         set())
        self.assertEqual(set([et.key_name for et in event_teams]).symmetric_difference({'2011tstupdaterfuture_frc95', '2011tstupdaterfuture_frc178', '2011tstupdaterfuture_frc176', '2011tstupdaterfuture_frc1922', '2011tstupdaterfuture_frc173', '2011tstupdaterfuture_frc2785', '2011tstupdaterfuture_frc228', '2011tstupdaterfuture_frc177', '2011tstupdaterfuture_frc1099', '2011tstupdaterfuture_frc175', '2011tstupdaterfuture_frc1027', '2011tstupdaterfuture_frc3017', '2011tstupdaterfuture_frc1493', '2011tstupdaterfuture_frc118', '2011tstupdaterfuture_frc229', '2011tstupdaterfuture_frc2791', '2011tstupdaterfuture_frc155', '2011tstupdaterfuture_frc549', '2011tstupdaterfuture_frc195', '2011tstupdaterfuture_frc4134', '2011tstupdaterfuture_frc20', '2011tstupdaterfuture_frc2836', '2011tstupdaterfuture_frc869', '2011tstupdaterfuture_frc1665', '2011tstupdaterfuture_frc4055', '2011tstupdaterfuture_frc3555', '2011tstupdaterfuture_frc126', '2011tstupdaterfuture_frc1699', '2011tstupdaterfuture_frc1559', '2011tstupdaterfuture_frc3464', '2011tstupdaterfuture_frc2168', '2011tstupdaterfuture_frc3461', '2011tstupdaterfuture_frc1991', '2011tstupdaterfuture_frc3467', '2011tstupdaterfuture_frc2067', '2011tstupdaterfuture_frc230', '2011tstupdaterfuture_frc1124', '2011tstupdaterfuture_frc3104', '2011tstupdaterfuture_frc236', '2011tstupdaterfuture_frc237', '2011tstupdaterfuture_frc1511', '2011tstupdaterfuture_frc250', '2011tstupdaterfuture_frc1880', '2011tstupdaterfuture_frc558', '2011tstupdaterfuture_frc694', '2011tstupdaterfuture_frc571', '2011tstupdaterfuture_frc3634', '2011tstupdaterfuture_frc3525', '2011tstupdaterfuture_frc999', '2011tstupdaterfuture_frc181', '2011tstupdaterfuture_frc1073', '2011tstupdaterfuture_frc3146', '2011tstupdaterfuture_frc1071', '2011tstupdaterfuture_frc1740', '2011tstupdaterfuture_frc3719', '2011tstupdaterfuture_frc3718', '2011tstupdaterfuture_frc2170', '2011tstupdaterfuture_frc663', '2011tstupdaterfuture_frc4122', '2011tstupdaterfuture_frc3182', '2011tstupdaterfuture_frc839', '2011tstupdaterfuture_frc1784', '2011tstupdaterfuture_frc3654', '2011tstupdaterfuture_frc743'}),
                         set())
        self.assertEqual(set([et_key.id() for et_key in et_keys_to_delete]),
                         set())
