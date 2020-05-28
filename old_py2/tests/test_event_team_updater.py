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


CUR_YEAR = datetime.datetime.now().year


def set_up_matches(html, event):
    with open(html, 'r') as f:
        parsed_matches, _ = UsfirstMatchesParser.parse(f.read())
        matches = [Match(id=Match.renderKeyName(event.key.id(),
                                                match.get("comp_level", None),
                                                match.get("set_number", 0),
                                                match.get("match_number", 0)),
                         event=event.key,
                         year=event.year,
                         set_number=match.get("set_number", 0),
                         match_number=match.get("match_number", 0),
                         comp_level=match.get("comp_level", None),
                         team_key_names=match.get("team_key_names", None),
                         alliances_json=match.get("alliances_json", None))
                   for match in parsed_matches]
        return matches


class TestEventTeamUpdater(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        past_event = Event(
            id="{}tstupdaterpast".format(CUR_YEAR),
            end_date=datetime.datetime.now() - datetime.timedelta(days=1),
            event_short="tstupdaterpast",
            event_type_enum=EventType.REGIONAL,
            start_date=datetime.datetime.now() - datetime.timedelta(days=2),
            year=CUR_YEAR,
        )
        past_event.put()
        past_event_matches = set_up_matches(
            'test_data/usfirst_html/usfirst_event_matches_2012ct.html',
            past_event)
        ndb.put_multi(past_event_matches)

        future_event = Event(
            id="{}tstupdaterfuture".format(CUR_YEAR),
            end_date=datetime.datetime.now() + datetime.timedelta(days=2),
            event_short="tstupdaterfuture",
            event_type_enum=EventType.REGIONAL,
            start_date=datetime.datetime.now() + datetime.timedelta(days=1),
            year=CUR_YEAR,
        )
        future_event.put()
        future_event_matches = set_up_matches(
            'test_data/usfirst_html/usfirst_event_matches_2012ct.html',
            future_event)
        ndb.put_multi(future_event_matches)

        past_year_event = Event(
            id="{}tstupdaterpastyear".format(CUR_YEAR - 1),
            end_date=datetime.datetime.now() - datetime.timedelta(days=1),
            event_short="tstupdaterpastyear",
            event_type_enum=EventType.REGIONAL,
            start_date=datetime.datetime.now() - datetime.timedelta(days=2),
            year=CUR_YEAR - 1,
        )
        past_year_event.put()
        past_year_event_matches = set_up_matches(
            'test_data/usfirst_html/usfirst_event_matches_2012ct.html',
            past_year_event)
        ndb.put_multi(past_year_event_matches)

    def tearDown(self):
        self.testbed.deactivate()

    def test_update_future(self):
        teams, event_teams, et_keys_to_delete = EventTeamUpdater.update('{}tstupdaterfuture'.format(CUR_YEAR))
        self.assertEqual(set([team.team_number for team in teams]).symmetric_difference({95, 178, 176, 1922, 173, 2785, 228, 177, 1099, 175, 1027, 3017, 1493, 118, 229, 2791, 155, 549, 195, 4134, 20, 2836, 869, 1665, 4055, 3555, 126, 1699, 1559, 3464, 2168, 3461, 1991, 3467, 2067, 230, 1124, 3104, 236, 237, 1511, 250, 1880, 558, 694, 571, 3634, 3525, 999, 181, 1073, 3146, 1071, 1740, 3719, 3718, 2170, 663, 4122, 3182, 839, 1784, 3654, 743}),
                         set())
        self.assertEqual(set([et.key_name for et in event_teams]).symmetric_difference({'{}tstupdaterfuture_frc95'.format(CUR_YEAR), '{}tstupdaterfuture_frc178'.format(CUR_YEAR), '{}tstupdaterfuture_frc176'.format(CUR_YEAR), '{}tstupdaterfuture_frc1922'.format(CUR_YEAR), '{}tstupdaterfuture_frc173'.format(CUR_YEAR), '{}tstupdaterfuture_frc2785'.format(CUR_YEAR), '{}tstupdaterfuture_frc228'.format(CUR_YEAR), '{}tstupdaterfuture_frc177'.format(CUR_YEAR), '{}tstupdaterfuture_frc1099'.format(CUR_YEAR), '{}tstupdaterfuture_frc175'.format(CUR_YEAR), '{}tstupdaterfuture_frc1027'.format(CUR_YEAR), '{}tstupdaterfuture_frc3017'.format(CUR_YEAR), '{}tstupdaterfuture_frc1493'.format(CUR_YEAR), '{}tstupdaterfuture_frc118'.format(CUR_YEAR), '{}tstupdaterfuture_frc229'.format(CUR_YEAR), '{}tstupdaterfuture_frc2791'.format(CUR_YEAR), '{}tstupdaterfuture_frc155'.format(CUR_YEAR), '{}tstupdaterfuture_frc549'.format(CUR_YEAR), '{}tstupdaterfuture_frc195'.format(CUR_YEAR), '{}tstupdaterfuture_frc4134'.format(CUR_YEAR), '{}tstupdaterfuture_frc20'.format(CUR_YEAR), '{}tstupdaterfuture_frc2836'.format(CUR_YEAR), '{}tstupdaterfuture_frc869'.format(CUR_YEAR), '{}tstupdaterfuture_frc1665'.format(CUR_YEAR), '{}tstupdaterfuture_frc4055'.format(CUR_YEAR), '{}tstupdaterfuture_frc3555'.format(CUR_YEAR), '{}tstupdaterfuture_frc126'.format(CUR_YEAR), '{}tstupdaterfuture_frc1699'.format(CUR_YEAR), '{}tstupdaterfuture_frc1559'.format(CUR_YEAR), '{}tstupdaterfuture_frc3464'.format(CUR_YEAR), '{}tstupdaterfuture_frc2168'.format(CUR_YEAR), '{}tstupdaterfuture_frc3461'.format(CUR_YEAR), '{}tstupdaterfuture_frc1991'.format(CUR_YEAR), '{}tstupdaterfuture_frc3467'.format(CUR_YEAR), '{}tstupdaterfuture_frc2067'.format(CUR_YEAR), '{}tstupdaterfuture_frc230'.format(CUR_YEAR), '{}tstupdaterfuture_frc1124'.format(CUR_YEAR), '{}tstupdaterfuture_frc3104'.format(CUR_YEAR), '{}tstupdaterfuture_frc236'.format(CUR_YEAR), '{}tstupdaterfuture_frc237'.format(CUR_YEAR), '{}tstupdaterfuture_frc1511'.format(CUR_YEAR), '{}tstupdaterfuture_frc250'.format(CUR_YEAR), '{}tstupdaterfuture_frc1880'.format(CUR_YEAR), '{}tstupdaterfuture_frc558'.format(CUR_YEAR), '{}tstupdaterfuture_frc694'.format(CUR_YEAR), '{}tstupdaterfuture_frc571'.format(CUR_YEAR), '{}tstupdaterfuture_frc3634'.format(CUR_YEAR), '{}tstupdaterfuture_frc3525'.format(CUR_YEAR), '{}tstupdaterfuture_frc999'.format(CUR_YEAR), '{}tstupdaterfuture_frc181'.format(CUR_YEAR), '{}tstupdaterfuture_frc1073'.format(CUR_YEAR), '{}tstupdaterfuture_frc3146'.format(CUR_YEAR), '{}tstupdaterfuture_frc1071'.format(CUR_YEAR), '{}tstupdaterfuture_frc1740'.format(CUR_YEAR), '{}tstupdaterfuture_frc3719'.format(CUR_YEAR), '{}tstupdaterfuture_frc3718'.format(CUR_YEAR), '{}tstupdaterfuture_frc2170'.format(CUR_YEAR), '{}tstupdaterfuture_frc663'.format(CUR_YEAR), '{}tstupdaterfuture_frc4122'.format(CUR_YEAR), '{}tstupdaterfuture_frc3182'.format(CUR_YEAR), '{}tstupdaterfuture_frc839'.format(CUR_YEAR), '{}tstupdaterfuture_frc1784'.format(CUR_YEAR), '{}tstupdaterfuture_frc3654'.format(CUR_YEAR), '{}tstupdaterfuture_frc743'.format(CUR_YEAR)}),
                         set())
        self.assertEqual(et_keys_to_delete, set())

        event_team = EventTeam(
            id="%s_%s" % ('{}tstupdaterfuture'.format(CUR_YEAR), 'frc9999'),
            event=ndb.Key(Event, '{}tstupdaterfuture'.format(CUR_YEAR)),
            team=ndb.Key(Team, 'frc9999'),
            year=CUR_YEAR)
        event_team.put()

        teams, event_teams, et_keys_to_delete = EventTeamUpdater.update('{}tstupdaterfuture'.format(CUR_YEAR))
        self.assertEqual(set([team.team_number for team in teams]).symmetric_difference({95, 178, 176, 1922, 173, 2785, 228, 177, 1099, 175, 1027, 3017, 1493, 118, 229, 2791, 155, 549, 195, 4134, 20, 2836, 869, 1665, 4055, 3555, 126, 1699, 1559, 3464, 2168, 3461, 1991, 3467, 2067, 230, 1124, 3104, 236, 237, 1511, 250, 1880, 558, 694, 571, 3634, 3525, 999, 181, 1073, 3146, 1071, 1740, 3719, 3718, 2170, 663, 4122, 3182, 839, 1784, 3654, 743}),
                         set())
        self.assertEqual(set([et.key_name for et in event_teams]).symmetric_difference({'{}tstupdaterfuture_frc95'.format(CUR_YEAR), '{}tstupdaterfuture_frc178'.format(CUR_YEAR), '{}tstupdaterfuture_frc176'.format(CUR_YEAR), '{}tstupdaterfuture_frc1922'.format(CUR_YEAR), '{}tstupdaterfuture_frc173'.format(CUR_YEAR), '{}tstupdaterfuture_frc2785'.format(CUR_YEAR), '{}tstupdaterfuture_frc228'.format(CUR_YEAR), '{}tstupdaterfuture_frc177'.format(CUR_YEAR), '{}tstupdaterfuture_frc1099'.format(CUR_YEAR), '{}tstupdaterfuture_frc175'.format(CUR_YEAR), '{}tstupdaterfuture_frc1027'.format(CUR_YEAR), '{}tstupdaterfuture_frc3017'.format(CUR_YEAR), '{}tstupdaterfuture_frc1493'.format(CUR_YEAR), '{}tstupdaterfuture_frc118'.format(CUR_YEAR), '{}tstupdaterfuture_frc229'.format(CUR_YEAR), '{}tstupdaterfuture_frc2791'.format(CUR_YEAR), '{}tstupdaterfuture_frc155'.format(CUR_YEAR), '{}tstupdaterfuture_frc549'.format(CUR_YEAR), '{}tstupdaterfuture_frc195'.format(CUR_YEAR), '{}tstupdaterfuture_frc4134'.format(CUR_YEAR), '{}tstupdaterfuture_frc20'.format(CUR_YEAR), '{}tstupdaterfuture_frc2836'.format(CUR_YEAR), '{}tstupdaterfuture_frc869'.format(CUR_YEAR), '{}tstupdaterfuture_frc1665'.format(CUR_YEAR), '{}tstupdaterfuture_frc4055'.format(CUR_YEAR), '{}tstupdaterfuture_frc3555'.format(CUR_YEAR), '{}tstupdaterfuture_frc126'.format(CUR_YEAR), '{}tstupdaterfuture_frc1699'.format(CUR_YEAR), '{}tstupdaterfuture_frc1559'.format(CUR_YEAR), '{}tstupdaterfuture_frc3464'.format(CUR_YEAR), '{}tstupdaterfuture_frc2168'.format(CUR_YEAR), '{}tstupdaterfuture_frc3461'.format(CUR_YEAR), '{}tstupdaterfuture_frc1991'.format(CUR_YEAR), '{}tstupdaterfuture_frc3467'.format(CUR_YEAR), '{}tstupdaterfuture_frc2067'.format(CUR_YEAR), '{}tstupdaterfuture_frc230'.format(CUR_YEAR), '{}tstupdaterfuture_frc1124'.format(CUR_YEAR), '{}tstupdaterfuture_frc3104'.format(CUR_YEAR), '{}tstupdaterfuture_frc236'.format(CUR_YEAR), '{}tstupdaterfuture_frc237'.format(CUR_YEAR), '{}tstupdaterfuture_frc1511'.format(CUR_YEAR), '{}tstupdaterfuture_frc250'.format(CUR_YEAR), '{}tstupdaterfuture_frc1880'.format(CUR_YEAR), '{}tstupdaterfuture_frc558'.format(CUR_YEAR), '{}tstupdaterfuture_frc694'.format(CUR_YEAR), '{}tstupdaterfuture_frc571'.format(CUR_YEAR), '{}tstupdaterfuture_frc3634'.format(CUR_YEAR), '{}tstupdaterfuture_frc3525'.format(CUR_YEAR), '{}tstupdaterfuture_frc999'.format(CUR_YEAR), '{}tstupdaterfuture_frc181'.format(CUR_YEAR), '{}tstupdaterfuture_frc1073'.format(CUR_YEAR), '{}tstupdaterfuture_frc3146'.format(CUR_YEAR), '{}tstupdaterfuture_frc1071'.format(CUR_YEAR), '{}tstupdaterfuture_frc1740'.format(CUR_YEAR), '{}tstupdaterfuture_frc3719'.format(CUR_YEAR), '{}tstupdaterfuture_frc3718'.format(CUR_YEAR), '{}tstupdaterfuture_frc2170'.format(CUR_YEAR), '{}tstupdaterfuture_frc663'.format(CUR_YEAR), '{}tstupdaterfuture_frc4122'.format(CUR_YEAR), '{}tstupdaterfuture_frc3182'.format(CUR_YEAR), '{}tstupdaterfuture_frc839'.format(CUR_YEAR), '{}tstupdaterfuture_frc1784'.format(CUR_YEAR), '{}tstupdaterfuture_frc3654'.format(CUR_YEAR), '{}tstupdaterfuture_frc743'.format(CUR_YEAR)}),
                         set())
        self.assertEqual(set([et_key.id() for et_key in et_keys_to_delete]),
                         set())

    def test_update_past(self):
        teams, event_teams, et_keys_to_delete = EventTeamUpdater.update('{}tstupdaterpast'.format(CUR_YEAR))
        self.assertEqual(set([team.team_number for team in teams]).symmetric_difference({95, 178, 176, 1922, 173, 2785, 228, 177, 1099, 175, 1027, 3017, 1493, 118, 229, 2791, 155, 549, 195, 4134, 20, 2836, 869, 1665, 4055, 3555, 126, 1699, 1559, 3464, 2168, 3461, 1991, 3467, 2067, 230, 1124, 3104, 236, 237, 1511, 250, 1880, 558, 694, 571, 3634, 3525, 999, 181, 1073, 3146, 1071, 1740, 3719, 3718, 2170, 663, 4122, 3182, 839, 1784, 3654, 743}),
                         set())
        self.assertEqual(set([et.key_name for et in event_teams]).symmetric_difference({'{}tstupdaterpast_frc95'.format(CUR_YEAR), '{}tstupdaterpast_frc178'.format(CUR_YEAR), '{}tstupdaterpast_frc176'.format(CUR_YEAR), '{}tstupdaterpast_frc1922'.format(CUR_YEAR), '{}tstupdaterpast_frc173'.format(CUR_YEAR), '{}tstupdaterpast_frc2785'.format(CUR_YEAR), '{}tstupdaterpast_frc228'.format(CUR_YEAR), '{}tstupdaterpast_frc177'.format(CUR_YEAR), '{}tstupdaterpast_frc1099'.format(CUR_YEAR), '{}tstupdaterpast_frc175'.format(CUR_YEAR), '{}tstupdaterpast_frc1027'.format(CUR_YEAR), '{}tstupdaterpast_frc3017'.format(CUR_YEAR), '{}tstupdaterpast_frc1493'.format(CUR_YEAR), '{}tstupdaterpast_frc118'.format(CUR_YEAR), '{}tstupdaterpast_frc229'.format(CUR_YEAR), '{}tstupdaterpast_frc2791'.format(CUR_YEAR), '{}tstupdaterpast_frc155'.format(CUR_YEAR), '{}tstupdaterpast_frc549'.format(CUR_YEAR), '{}tstupdaterpast_frc195'.format(CUR_YEAR), '{}tstupdaterpast_frc4134'.format(CUR_YEAR), '{}tstupdaterpast_frc20'.format(CUR_YEAR), '{}tstupdaterpast_frc2836'.format(CUR_YEAR), '{}tstupdaterpast_frc869'.format(CUR_YEAR), '{}tstupdaterpast_frc1665'.format(CUR_YEAR), '{}tstupdaterpast_frc4055'.format(CUR_YEAR), '{}tstupdaterpast_frc3555'.format(CUR_YEAR), '{}tstupdaterpast_frc126'.format(CUR_YEAR), '{}tstupdaterpast_frc1699'.format(CUR_YEAR), '{}tstupdaterpast_frc1559'.format(CUR_YEAR), '{}tstupdaterpast_frc3464'.format(CUR_YEAR), '{}tstupdaterpast_frc2168'.format(CUR_YEAR), '{}tstupdaterpast_frc3461'.format(CUR_YEAR), '{}tstupdaterpast_frc1991'.format(CUR_YEAR), '{}tstupdaterpast_frc3467'.format(CUR_YEAR), '{}tstupdaterpast_frc2067'.format(CUR_YEAR), '{}tstupdaterpast_frc230'.format(CUR_YEAR), '{}tstupdaterpast_frc1124'.format(CUR_YEAR), '{}tstupdaterpast_frc3104'.format(CUR_YEAR), '{}tstupdaterpast_frc236'.format(CUR_YEAR), '{}tstupdaterpast_frc237'.format(CUR_YEAR), '{}tstupdaterpast_frc1511'.format(CUR_YEAR), '{}tstupdaterpast_frc250'.format(CUR_YEAR), '{}tstupdaterpast_frc1880'.format(CUR_YEAR), '{}tstupdaterpast_frc558'.format(CUR_YEAR), '{}tstupdaterpast_frc694'.format(CUR_YEAR), '{}tstupdaterpast_frc571'.format(CUR_YEAR), '{}tstupdaterpast_frc3634'.format(CUR_YEAR), '{}tstupdaterpast_frc3525'.format(CUR_YEAR), '{}tstupdaterpast_frc999'.format(CUR_YEAR), '{}tstupdaterpast_frc181'.format(CUR_YEAR), '{}tstupdaterpast_frc1073'.format(CUR_YEAR), '{}tstupdaterpast_frc3146'.format(CUR_YEAR), '{}tstupdaterpast_frc1071'.format(CUR_YEAR), '{}tstupdaterpast_frc1740'.format(CUR_YEAR), '{}tstupdaterpast_frc3719'.format(CUR_YEAR), '{}tstupdaterpast_frc3718'.format(CUR_YEAR), '{}tstupdaterpast_frc2170'.format(CUR_YEAR), '{}tstupdaterpast_frc663'.format(CUR_YEAR), '{}tstupdaterpast_frc4122'.format(CUR_YEAR), '{}tstupdaterpast_frc3182'.format(CUR_YEAR), '{}tstupdaterpast_frc839'.format(CUR_YEAR), '{}tstupdaterpast_frc1784'.format(CUR_YEAR), '{}tstupdaterpast_frc3654'.format(CUR_YEAR), '{}tstupdaterpast_frc743'.format(CUR_YEAR)}),
                         set())
        self.assertEqual(et_keys_to_delete, set())

        event_team = EventTeam(
            id="%s_%s" % ('{}tstupdaterpast'.format(CUR_YEAR), 'frc9999'),
            event=ndb.Key(Event, '{}tstupdaterpast'.format(CUR_YEAR)),
            team=ndb.Key(Team, 'frc9999'),
            year=CUR_YEAR)
        event_team.put()

        teams, event_teams, et_keys_to_delete = EventTeamUpdater.update('{}tstupdaterpast'.format(CUR_YEAR))
        self.assertEqual(set([team.team_number for team in teams]).symmetric_difference({95, 178, 176, 1922, 173, 2785, 228, 177, 1099, 175, 1027, 3017, 1493, 118, 229, 2791, 155, 549, 195, 4134, 20, 2836, 869, 1665, 4055, 3555, 126, 1699, 1559, 3464, 2168, 3461, 1991, 3467, 2067, 230, 1124, 3104, 236, 237, 1511, 250, 1880, 558, 694, 571, 3634, 3525, 999, 181, 1073, 3146, 1071, 1740, 3719, 3718, 2170, 663, 4122, 3182, 839, 1784, 3654, 743}),
                         set())
        self.assertEqual(set([et.key_name for et in event_teams]).symmetric_difference({'{}tstupdaterpast_frc95'.format(CUR_YEAR), '{}tstupdaterpast_frc178'.format(CUR_YEAR), '{}tstupdaterpast_frc176'.format(CUR_YEAR), '{}tstupdaterpast_frc1922'.format(CUR_YEAR), '{}tstupdaterpast_frc173'.format(CUR_YEAR), '{}tstupdaterpast_frc2785'.format(CUR_YEAR), '{}tstupdaterpast_frc228'.format(CUR_YEAR), '{}tstupdaterpast_frc177'.format(CUR_YEAR), '{}tstupdaterpast_frc1099'.format(CUR_YEAR), '{}tstupdaterpast_frc175'.format(CUR_YEAR), '{}tstupdaterpast_frc1027'.format(CUR_YEAR), '{}tstupdaterpast_frc3017'.format(CUR_YEAR), '{}tstupdaterpast_frc1493'.format(CUR_YEAR), '{}tstupdaterpast_frc118'.format(CUR_YEAR), '{}tstupdaterpast_frc229'.format(CUR_YEAR), '{}tstupdaterpast_frc2791'.format(CUR_YEAR), '{}tstupdaterpast_frc155'.format(CUR_YEAR), '{}tstupdaterpast_frc549'.format(CUR_YEAR), '{}tstupdaterpast_frc195'.format(CUR_YEAR), '{}tstupdaterpast_frc4134'.format(CUR_YEAR), '{}tstupdaterpast_frc20'.format(CUR_YEAR), '{}tstupdaterpast_frc2836'.format(CUR_YEAR), '{}tstupdaterpast_frc869'.format(CUR_YEAR), '{}tstupdaterpast_frc1665'.format(CUR_YEAR), '{}tstupdaterpast_frc4055'.format(CUR_YEAR), '{}tstupdaterpast_frc3555'.format(CUR_YEAR), '{}tstupdaterpast_frc126'.format(CUR_YEAR), '{}tstupdaterpast_frc1699'.format(CUR_YEAR), '{}tstupdaterpast_frc1559'.format(CUR_YEAR), '{}tstupdaterpast_frc3464'.format(CUR_YEAR), '{}tstupdaterpast_frc2168'.format(CUR_YEAR), '{}tstupdaterpast_frc3461'.format(CUR_YEAR), '{}tstupdaterpast_frc1991'.format(CUR_YEAR), '{}tstupdaterpast_frc3467'.format(CUR_YEAR), '{}tstupdaterpast_frc2067'.format(CUR_YEAR), '{}tstupdaterpast_frc230'.format(CUR_YEAR), '{}tstupdaterpast_frc1124'.format(CUR_YEAR), '{}tstupdaterpast_frc3104'.format(CUR_YEAR), '{}tstupdaterpast_frc236'.format(CUR_YEAR), '{}tstupdaterpast_frc237'.format(CUR_YEAR), '{}tstupdaterpast_frc1511'.format(CUR_YEAR), '{}tstupdaterpast_frc250'.format(CUR_YEAR), '{}tstupdaterpast_frc1880'.format(CUR_YEAR), '{}tstupdaterpast_frc558'.format(CUR_YEAR), '{}tstupdaterpast_frc694'.format(CUR_YEAR), '{}tstupdaterpast_frc571'.format(CUR_YEAR), '{}tstupdaterpast_frc3634'.format(CUR_YEAR), '{}tstupdaterpast_frc3525'.format(CUR_YEAR), '{}tstupdaterpast_frc999'.format(CUR_YEAR), '{}tstupdaterpast_frc181'.format(CUR_YEAR), '{}tstupdaterpast_frc1073'.format(CUR_YEAR), '{}tstupdaterpast_frc3146'.format(CUR_YEAR), '{}tstupdaterpast_frc1071'.format(CUR_YEAR), '{}tstupdaterpast_frc1740'.format(CUR_YEAR), '{}tstupdaterpast_frc3719'.format(CUR_YEAR), '{}tstupdaterpast_frc3718'.format(CUR_YEAR), '{}tstupdaterpast_frc2170'.format(CUR_YEAR), '{}tstupdaterpast_frc663'.format(CUR_YEAR), '{}tstupdaterpast_frc4122'.format(CUR_YEAR), '{}tstupdaterpast_frc3182'.format(CUR_YEAR), '{}tstupdaterpast_frc839'.format(CUR_YEAR), '{}tstupdaterpast_frc1784'.format(CUR_YEAR), '{}tstupdaterpast_frc3654'.format(CUR_YEAR), '{}tstupdaterpast_frc743'.format(CUR_YEAR)}),
                         set())
        self.assertEqual(set([et_key.id() for et_key in et_keys_to_delete]).symmetric_difference({'{}tstupdaterpast_frc9999'.format(CUR_YEAR)}),
                         set())

    def test_update_pastyear(self):
        teams, event_teams, et_keys_to_delete = EventTeamUpdater.update('{}tstupdaterpastyear'.format(CUR_YEAR - 1))
        self.assertEqual(set([team.team_number for team in teams]).symmetric_difference({95, 178, 176, 1922, 173, 2785, 228, 177, 1099, 175, 1027, 3017, 1493, 118, 229, 2791, 155, 549, 195, 4134, 20, 2836, 869, 1665, 4055, 3555, 126, 1699, 1559, 3464, 2168, 3461, 1991, 3467, 2067, 230, 1124, 3104, 236, 237, 1511, 250, 1880, 558, 694, 571, 3634, 3525, 999, 181, 1073, 3146, 1071, 1740, 3719, 3718, 2170, 663, 4122, 3182, 839, 1784, 3654, 743}),
                         set())
        self.assertEqual(set([et.key_name for et in event_teams]).symmetric_difference({'{}tstupdaterpastyear_frc95'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc178'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc176'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1922'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc173'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc2785'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc228'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc177'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1099'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc175'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1027'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3017'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1493'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc118'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc229'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc2791'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc155'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc549'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc195'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc4134'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc20'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc2836'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc869'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1665'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc4055'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3555'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc126'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1699'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1559'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3464'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc2168'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3461'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1991'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3467'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc2067'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc230'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1124'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3104'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc236'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc237'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1511'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc250'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1880'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc558'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc694'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc571'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3634'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3525'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc999'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc181'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1073'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3146'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1071'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1740'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3719'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3718'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc2170'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc663'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc4122'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3182'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc839'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1784'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3654'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc743'.format(CUR_YEAR - 1)}),
                         set())
        self.assertEqual(et_keys_to_delete, set())

        event_team = EventTeam(
            id="%s_%s" % ('{}tstupdaterpastyear'.format(CUR_YEAR - 1), 'frc9999'),
            event=ndb.Key(Event, '{}tstupdaterpastyear'.format(CUR_YEAR - 1)),
            team=ndb.Key(Team, 'frc9999'),
            year=CUR_YEAR - 1)
        event_team.put()

        teams, event_teams, et_keys_to_delete = EventTeamUpdater.update('{}tstupdaterpastyear'.format(CUR_YEAR - 1))
        self.assertEqual(set([team.team_number for team in teams]).symmetric_difference({95, 178, 176, 1922, 173, 2785, 228, 177, 1099, 175, 1027, 3017, 1493, 118, 229, 2791, 155, 549, 195, 4134, 20, 2836, 869, 1665, 4055, 3555, 126, 1699, 1559, 3464, 2168, 3461, 1991, 3467, 2067, 230, 1124, 3104, 236, 237, 1511, 250, 1880, 558, 694, 571, 3634, 3525, 999, 181, 1073, 3146, 1071, 1740, 3719, 3718, 2170, 663, 4122, 3182, 839, 1784, 3654, 743}),
                         set())
        self.assertEqual(set([et.key_name for et in event_teams]).symmetric_difference({'{}tstupdaterpastyear_frc95'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc178'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc176'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1922'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc173'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc2785'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc228'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc177'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1099'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc175'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1027'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3017'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1493'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc118'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc229'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc2791'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc155'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc549'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc195'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc4134'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc20'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc2836'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc869'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1665'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc4055'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3555'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc126'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1699'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1559'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3464'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc2168'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3461'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1991'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3467'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc2067'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc230'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1124'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3104'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc236'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc237'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1511'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc250'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1880'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc558'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc694'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc571'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3634'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3525'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc999'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc181'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1073'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3146'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1071'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1740'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3719'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3718'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc2170'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc663'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc4122'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3182'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc839'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc1784'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc3654'.format(CUR_YEAR - 1), '{}tstupdaterpastyear_frc743'.format(CUR_YEAR - 1)}),
                         set())
        self.assertEqual(et_keys_to_delete, set())
