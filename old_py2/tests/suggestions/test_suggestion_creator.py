import unittest2

from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.auth_type import AuthType
from consts.event_type import EventType
from consts.media_type import MediaType
from helpers.media_helper import MediaParser
from helpers.suggestions.suggestion_creator import SuggestionCreator
from models.account import Account
from models.event import Event
from models.match import Match
from models.media import Media
from models.suggestion import Suggestion
from models.team import Team


class TestTeamMediaSuggestionCreator(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.account = Account.get_or_insert(
            "123",
            email="user@example.com",
            registered=True)
        self.account.put()

        self.account_banned = Account.get_or_insert(
            "456",
            email="user@example.com",
            registered=True,
            shadow_banned=True,
        )
        self.account_banned.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_create_suggestion(self):
        status, _ = SuggestionCreator.createTeamMediaSuggestion(
            self.account.key,
            "http://imgur.com/ruRAxDm",
            "frc1124",
            "2016")
        self.assertEqual(status, 'success')

        # Ensure the Suggestion gets created
        suggestion_id = Suggestion.render_media_key_name('2016', 'team', 'frc1124', 'imgur', 'ruRAxDm')
        suggestion = Suggestion.get_by_id(suggestion_id)
        expected_dict = MediaParser.partial_media_dict_from_url("http://imgur.com/ruRAxDm")
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_PENDING)
        self.assertEqual(suggestion.author, self.account.key)
        self.assertEqual(suggestion.target_model, 'media')
        self.assertDictContainsSubset(expected_dict, suggestion.contents)

    def test_create_suggestion_banned(self):
        status, _ = SuggestionCreator.createTeamMediaSuggestion(
            self.account_banned.key,
            "http://imgur.com/ruRAxDm",
            "frc1124",
            "2016")
        self.assertEqual(status, 'success')

        # Ensure the Suggestion gets created
        suggestion_id = Suggestion.render_media_key_name('2016', 'team', 'frc1124', 'imgur', 'ruRAxDm')
        suggestion = Suggestion.get_by_id(suggestion_id)
        expected_dict = MediaParser.partial_media_dict_from_url("http://imgur.com/ruRAxDm")
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_AUTOREJECTED)
        self.assertEqual(suggestion.author, self.account_banned.key)
        self.assertEqual(suggestion.target_model, 'media')
        self.assertDictContainsSubset(expected_dict, suggestion.contents)

    def test_create_suggestion_with_url_params(self):
        status, _ = SuggestionCreator.createTeamMediaSuggestion(
            self.account.key,
            "https://www.youtube.com/watch?v=VP992UKFbko",
            "frc1124",
            "2016")
        self.assertEqual(status, 'success')

        # Ensure the Suggestion gets created
        suggestion_id = Suggestion.render_media_key_name('2016', 'team', 'frc1124', 'youtube', 'VP992UKFbko')
        suggestion = Suggestion.get_by_id(suggestion_id)
        expected_dict = MediaParser.partial_media_dict_from_url("https://www.youtube.com/watch?v=VP992UKFbko")
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_PENDING)
        self.assertEqual(suggestion.author, self.account.key)
        self.assertEqual(suggestion.target_model, 'media')
        self.assertDictContainsSubset(expected_dict, suggestion.contents)

    def test_clean_url(self):
        status, _ = SuggestionCreator.createTeamMediaSuggestion(
            self.account.key,
            " http://imgur.com/ruRAxDm?foo=bar#meow ",
            "frc1124",
            "2016")
        self.assertEqual(status, 'success')

        # Ensure the Suggestion gets created
        suggestion_id = Suggestion.render_media_key_name('2016', 'team', 'frc1124', 'imgur', 'ruRAxDm')
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_PENDING)
        self.assertEqual(suggestion.author, self.account.key)
        self.assertEqual(suggestion.target_model, 'media')

    def test_duplicate_suggestion(self):
        suggestion_id = Suggestion.render_media_key_name('2016', 'team', 'frc1124', 'imgur', 'ruRAxDm')
        Suggestion(
            id=suggestion_id,
            author=self.account.key,
            review_state=Suggestion.REVIEW_PENDING,
            target_key="2012cmp",
            target_model="event").put()

        status, _ = SuggestionCreator.createTeamMediaSuggestion(
            self.account.key,
            "http://imgur.com/ruRAxDm",
            "frc1124",
            "2016")
        self.assertEqual(status, 'suggestion_exists')

    def test_media_exists(self):
        media_id = Media.render_key_name(MediaType.IMGUR, 'ruRAxDm')
        Media.get_or_insert(
            media_id,
            media_type_enum=MediaType.IMGUR,
            foreign_key='ruRAxDm',
            references=[ndb.Key(Team, 'frc1124')]).put()
        status, _ = SuggestionCreator.createTeamMediaSuggestion(
            self.account.key,
            "http://imgur.com/ruRAxDm",
            "frc1124",
            "2016")
        self.assertEqual(status, 'media_exists')

    def test_bad_url(self):
        status, _ = SuggestionCreator.createTeamMediaSuggestion(
            self.account.key,
            "http://foo.com/blah",
            "frc1124",
            "2016")
        self.assertEqual(status, 'bad_url')


class TestEventMediaSuggestionCreator(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.account = Account.get_or_insert(
            "123",
            email="user@example.com",
            registered=True)
        self.account.put()

        self.account_banned = Account.get_or_insert(
            "456",
            email="user@example.com",
            registered=True,
            shadow_banned=True,
        )
        self.account_banned.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_create_suggestion(self):
        status, _ = SuggestionCreator.createEventMediaSuggestion(
            self.account.key,
            "https://www.youtube.com/watch?v=H-54KMwMKY0",
            "2016nyny")
        self.assertEqual(status, 'success')

        # Ensure the Suggestion gets created
        suggestion_id = Suggestion.render_media_key_name('2016', 'event', '2016nyny', 'youtube', 'H-54KMwMKY0')
        suggestion = Suggestion.get_by_id(suggestion_id)
        expected_dict = MediaParser.partial_media_dict_from_url("https://www.youtube.com/watch?v=H-54KMwMKY0")
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_PENDING)
        self.assertEqual(suggestion.author, self.account.key)
        self.assertEqual(suggestion.target_model, 'event_media')
        self.assertDictContainsSubset(expected_dict, suggestion.contents)

    def test_create_suggestion_banned(self):
        status, _ = SuggestionCreator.createEventMediaSuggestion(
            self.account_banned.key,
            "https://www.youtube.com/watch?v=H-54KMwMKY0",
            "2016nyny")
        self.assertEqual(status, 'success')

        # Ensure the Suggestion gets created
        suggestion_id = Suggestion.render_media_key_name('2016', 'event', '2016nyny', 'youtube', 'H-54KMwMKY0')
        suggestion = Suggestion.get_by_id(suggestion_id)
        expected_dict = MediaParser.partial_media_dict_from_url("https://www.youtube.com/watch?v=H-54KMwMKY0")
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_AUTOREJECTED)
        self.assertEqual(suggestion.author, self.account_banned.key)
        self.assertEqual(suggestion.target_model, 'event_media')
        self.assertDictContainsSubset(expected_dict, suggestion.contents)

    def test_create_non_video_suggestion(self):
        status, _ = SuggestionCreator.createEventMediaSuggestion(
            self.account.key,
            "http://imgur.com/ruRAxDm",
            "2016nyny")
        self.assertEqual(status, 'bad_url')

    def test_duplicate_suggestion(self):
        suggestion_id = Suggestion.render_media_key_name('2016', 'event', '2016nyny', 'youtube', 'H-54KMwMKY0')
        Suggestion(
            id=suggestion_id,
            author=self.account.key,
            review_state=Suggestion.REVIEW_PENDING,
            target_key="2016nyny",
            target_model="event_media").put()

        status, _ = SuggestionCreator.createEventMediaSuggestion(
            self.account.key,
            "https://www.youtube.com/watch?v=H-54KMwMKY0",
            "2016nyny")
        self.assertEqual(status, 'suggestion_exists')

    def test_media_exists(self):
        media_id = Media.render_key_name(MediaType.YOUTUBE_VIDEO, 'H-54KMwMKY0')
        Media.get_or_insert(
            media_id,
            media_type_enum=MediaType.YOUTUBE_VIDEO,
            foreign_key='H-54KMwMKY0',
            references=[ndb.Key(Event, '2016nyny')]).put()
        status, _ = SuggestionCreator.createEventMediaSuggestion(
            self.account.key,
            "https://www.youtube.com/watch?v=H-54KMwMKY0",
            "2016nyny")
        self.assertEqual(status, 'media_exists')

    def test_create_bad_url(self):
        status, _ = SuggestionCreator.createEventMediaSuggestion(
            self.account.key,
            "http://foobar.com/ruRAxDm",
            "2016nyny")
        self.assertEqual(status, 'bad_url')


class TestOffseasonEventSuggestionCreator(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.account = Account.get_or_insert(
            "123",
            email="user@example.com",
            registered=True)
        self.account.put()

        self.account_banned = Account.get_or_insert(
            "456",
            email="user@example.com",
            registered=True,
            shadow_banned=True,
        )
        self.account_banned.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_create_suggestion(self):
        status, _ = SuggestionCreator.createOffseasonEventSuggestion(
            self.account.key,
            "Test Event",
            "2016-5-1",
            "2016-5-2",
            "http://foo.bar.com",
            "The Venue",
            "123 Fake Street",
            "New York", "NY", "USA")
        self.assertEqual(status, 'success')

        # Ensure the Suggestion gets created
        suggestions = Suggestion.query().fetch()
        self.assertIsNotNone(suggestions)
        self.assertEqual(len(suggestions), 1)

        suggestion = suggestions[0]
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.contents['name'], "Test Event")
        self.assertEqual(suggestion.contents['start_date'], '2016-5-1')
        self.assertEqual(suggestion.contents['end_date'], '2016-5-2')
        self.assertEqual(suggestion.contents['website'], 'http://foo.bar.com')
        self.assertEqual(suggestion.contents['address'], '123 Fake Street')
        self.assertEqual(suggestion.contents['city'], 'New York')
        self.assertEqual(suggestion.contents['state'], 'NY')
        self.assertEqual(suggestion.contents['country'], 'USA')
        self.assertEqual(suggestion.contents['venue_name'], 'The Venue')

    def test_create_suggestion_banned(self):
        status, _ = SuggestionCreator.createOffseasonEventSuggestion(
            self.account_banned.key,
            "Test Event",
            "2016-5-1",
            "2016-5-2",
            "http://foo.bar.com",
            "The Venue",
            "123 Fake Street",
            "New York", "NY", "USA")
        self.assertEqual(status, 'success')

        # Ensure the Suggestion gets created
        suggestions = Suggestion.query().fetch()
        self.assertIsNotNone(suggestions)
        self.assertEqual(len(suggestions), 1)

        suggestion = suggestions[0]
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.contents['name'], "Test Event")
        self.assertEqual(suggestion.contents['start_date'], '2016-5-1')
        self.assertEqual(suggestion.contents['end_date'], '2016-5-2')
        self.assertEqual(suggestion.contents['website'], 'http://foo.bar.com')
        self.assertEqual(suggestion.contents['address'], '123 Fake Street')
        self.assertEqual(suggestion.contents['city'], 'New York')
        self.assertEqual(suggestion.contents['state'], 'NY')
        self.assertEqual(suggestion.contents['country'], 'USA')
        self.assertEqual(suggestion.contents['venue_name'], 'The Venue')
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_AUTOREJECTED)

    def test_missing_params(self):
        status, failures = SuggestionCreator.createOffseasonEventSuggestion(
            self.account.key,
            "",
            "2016-5-1",
            "2016-5-2",
            "http://foo.bar.com",
            "The Venue",
            "123 Fake Street", "New York", "NY", "USA")
        self.assertEqual(status, 'validation_failure')
        self.assertTrue('name' in failures)

        status, failures = SuggestionCreator.createOffseasonEventSuggestion(
            self.account.key,
            "Test Event",
            "",
            "2016-5-2",
            "http://foo.bar.com",
            "The Venue",
            "123 Fake Street", "New York", "NY", "USA")
        self.assertEqual(status, 'validation_failure')
        self.assertTrue('start_date' in failures)

        status, failures = SuggestionCreator.createOffseasonEventSuggestion(
            self.account.key,
            "Test Event",
            "2016-5-1",
            "",
            "http://foo.bar.com",
            "The Venue",
            "123 Fake Street", "New York", "NY", "USA")
        self.assertEqual(status, 'validation_failure')
        self.assertTrue('end_date' in failures)

        status, failures = SuggestionCreator.createOffseasonEventSuggestion(
            self.account.key,
            "Test Event",
            "2016-5-1",
            "2016-5-2",
            "",
            "The Venue",
            "123 Fake Street", "New York", "NY", "USA")
        self.assertEqual(status, 'validation_failure')
        self.assertTrue('website' in failures)

        status, failures = SuggestionCreator.createOffseasonEventSuggestion(
            self.account.key,
            "Test Event",
            "2016-5-1",
            "2016-5-2",
            "http://foo.bar.com",
            "The Venue",
            "", "New York", "NY", "USA")
        self.assertEqual(status, 'validation_failure')
        self.assertTrue('venue_address' in failures)

        status, failures = SuggestionCreator.createOffseasonEventSuggestion(
            self.account.key,
            "Test Event",
            "2016-5-1",
            "2016-5-2",
            "http://foo.bar.com",
            "",
            "123 Fake Street", "", "", "")
        self.assertEqual(status, 'validation_failure')
        self.assertTrue('venue_name' in failures)
        self.assertTrue('venue_city' in failures)
        self.assertTrue('venue_state' in failures)
        self.assertTrue('venue_country' in failures)

    def test_out_of_order_dates(self):
        status, failures = SuggestionCreator.createOffseasonEventSuggestion(
            self.account.key,
            "Test Event",
            "2016-5-4",
            "2016-5-2",
            "http://foo.bar.com",
            "The Venue",
            "123 Fake Street", "New York", "NY", "USA")
        self.assertEqual(status, 'validation_failure')
        self.assertTrue('end_date' in failures)

    def test_malformed_dates(self):
        status, failures = SuggestionCreator.createOffseasonEventSuggestion(
            self.account.key,
            "Test Event",
            "meow",
            "2016-5-2",
            "http://foo.bar.com",
            "The Venue",
            "123 Fake Street", "New York", "NY", "USA")
        self.assertEqual(status, 'validation_failure')
        self.assertTrue('start_date' in failures)

        status, failures = SuggestionCreator.createOffseasonEventSuggestion(
            self.account.key,
            "Test Event",
            "2016-5-1",
            "moo",
            "http://foo.bar.com",
            "The Venue",
            "123 Fake Street", "New York", "NY", "USA")
        self.assertEqual(status, 'validation_failure')
        self.assertTrue('end_date' in failures)


class TestApiWriteSuggestionCreator(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.account = Account.get_or_insert(
            "123",
            email="user@example.com",
            registered=True)
        self.account.put()

        self.account_banned = Account.get_or_insert(
            "456",
            email="user@example.com",
            registered=True,
            shadow_banned=True,
        )
        self.account_banned.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_create_suggestion(self):
        event = Event(id="2016test", name="Test Event", event_short="Test Event", year=2016, event_type_enum=EventType.OFFSEASON)
        event.put()

        status = SuggestionCreator.createApiWriteSuggestion(
            self.account.key,
            "2016test",
            "Event Organizer",
            [1, 2, 3])
        self.assertEqual(status, 'success')

        # Ensure the Suggestion gets created
        suggestions = Suggestion.query().fetch()
        self.assertIsNotNone(suggestions)
        self.assertEqual(len(suggestions), 1)

        suggestion = suggestions[0]
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.contents['event_key'], "2016test")
        self.assertEqual(suggestion.contents['affiliation'], "Event Organizer")
        self.assertListEqual(suggestion.contents['auth_types'], [1, 2, 3])

    def test_create_suggestion_banned(self):
        event = Event(id="2016test", name="Test Event", event_short="Test Event", year=2016, event_type_enum=EventType.OFFSEASON)
        event.put()

        status = SuggestionCreator.createApiWriteSuggestion(
            self.account_banned.key,
            "2016test",
            "Event Organizer",
            [1, 2, 3])
        self.assertEqual(status, 'success')

        # Ensure the Suggestion gets created
        suggestions = Suggestion.query().fetch()
        self.assertIsNotNone(suggestions)
        self.assertEqual(len(suggestions), 1)

        suggestion = suggestions[0]
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.contents['event_key'], "2016test")
        self.assertEqual(suggestion.contents['affiliation'], "Event Organizer")
        self.assertListEqual(suggestion.contents['auth_types'], [1, 2, 3])
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_AUTOREJECTED)

    def test_official_event(self):
        event = Event(id="2016test", name="Test Event", event_short="Test Event", year=2016, event_type_enum=EventType.REGIONAL)
        event.put()

        status = SuggestionCreator.createApiWriteSuggestion(
            self.account.key,
            "2016test",
            "Event Organizer",
            [AuthType.MATCH_VIDEO, AuthType.EVENT_MATCHES, AuthType.EVENT_ALLIANCES])
        self.assertEqual(status, 'success')

        # Ensure the Suggestion gets created with only MATCH_VIDEO permission
        suggestions = Suggestion.query().fetch()
        self.assertIsNotNone(suggestions)
        self.assertEqual(len(suggestions), 1)

        suggestion = suggestions[0]
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.contents['event_key'], "2016test")
        self.assertEqual(suggestion.contents['affiliation'], "Event Organizer")
        self.assertListEqual(suggestion.contents['auth_types'], [AuthType.MATCH_VIDEO])

    def test_no_event(self):
        status = SuggestionCreator.createApiWriteSuggestion(
            self.account.key,
            "2016test",
            "Event Organizer",
            [1, 2, 3])
        self.assertEqual(status, 'bad_event')

    def test_no_role(self):
        event = Event(id="2016test", name="Test Event", event_short="Test Event", year=2016, event_type_enum=EventType.OFFSEASON)
        event.put()
        status = SuggestionCreator.createApiWriteSuggestion(
            self.account.key,
            "2016test",
            "",
            [1, 2, 3])
        self.assertEqual(status, 'no_affiliation')

    def test_undefined_auth_type(self):
        event = Event(id="2016test", name="Test Event", event_short="Test Event", year=2016, event_type_enum=EventType.OFFSEASON)
        event.put()

        status = SuggestionCreator.createApiWriteSuggestion(
            self.account.key,
            "2016test",
            "Event Organizer",
            [1, 2, -1, -2])  # -1 and -2 should be filtered out
        self.assertEqual(status, 'success')

        # Ensure the Suggestion gets created
        suggestions = Suggestion.query().fetch()
        self.assertIsNotNone(suggestions)
        self.assertEqual(len(suggestions), 1)

        suggestion = suggestions[0]
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.contents['event_key'], "2016test")
        self.assertEqual(suggestion.contents['affiliation'], "Event Organizer")
        self.assertListEqual(suggestion.contents['auth_types'], [1, 2])


class TestSuggestEventWebcastCreator(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.account = Account.get_or_insert(
            "123",
            email="user@example.com",
            registered=True)
        self.account.put()

        self.account_banned = Account.get_or_insert(
            "456",
            email="user@example.com",
            registered=True,
            shadow_banned=True,
        )
        self.account_banned.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_bad_event(self):
        status = SuggestionCreator.createEventWebcastSuggestion(
            self.account.key,
            "http://twitch.tv/frcgamesense",
            "",
            "2016test")
        self.assertEqual(status, 'bad_event')

    def test_create_suggestion(self):
        event = Event(id="2016test", name="Test Event", event_short="Test Event", year=2016, event_type_enum=EventType.OFFSEASON)
        event.put()

        status = SuggestionCreator.createEventWebcastSuggestion(
            self.account.key,
            "http://twitch.tv/frcgamesense",
            "",
            "2016test")
        self.assertEqual(status, 'success')

        # Ensure the Suggestion gets created
        expected_key = "webcast_2016test_twitch_frcgamesense_None"
        suggestion = Suggestion.get_by_id(expected_key)

        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.target_key, "2016test")
        self.assertEqual(suggestion.author, self.account.key)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_PENDING)
        self.assertIsNotNone(suggestion.contents)
        self.assertEqual(suggestion.contents.get('webcast_url'), "http://twitch.tv/frcgamesense")
        self.assertIsNotNone(suggestion.contents.get('webcast_dict'))

    def test_create_suggestion_banned(self):
        event = Event(id="2016test", name="Test Event", event_short="Test Event", year=2016, event_type_enum=EventType.OFFSEASON)
        event.put()

        status = SuggestionCreator.createEventWebcastSuggestion(
            self.account_banned.key,
            "http://twitch.tv/frcgamesense",
            "",
            "2016test")
        self.assertEqual(status, 'success')

        # Ensure the Suggestion gets created
        expected_key = "webcast_2016test_twitch_frcgamesense_None"
        suggestion = Suggestion.get_by_id(expected_key)

        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.target_key, "2016test")
        self.assertEqual(suggestion.author, self.account_banned.key)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_AUTOREJECTED)
        self.assertIsNotNone(suggestion.contents)
        self.assertEqual(suggestion.contents.get('webcast_url'), "http://twitch.tv/frcgamesense")
        self.assertIsNotNone(suggestion.contents.get('webcast_dict'))

    def test_cleanup_url_without_scheme(self):
        event = Event(id="2016test", name="Test Event", event_short="Test Event", year=2016, event_type_enum=EventType.OFFSEASON)
        event.put()

        status = SuggestionCreator.createEventWebcastSuggestion(
            self.account.key,
            "twitch.tv/frcgamesense",
            "",
            "2016test")
        self.assertEqual(status, 'success')
        expected_key = "webcast_2016test_twitch_frcgamesense_None"
        suggestion = Suggestion.get_by_id(expected_key)

        self.assertIsNotNone(suggestion)
        self.assertIsNotNone(suggestion.contents)
        self.assertIsNotNone(suggestion.contents.get('webcast_dict'))
        self.assertEqual(suggestion.contents.get('webcast_url'), "http://twitch.tv/frcgamesense")

    def test_unknown_url_scheme(self):
        event = Event(id="2016test", name="Test Event", event_short="Test Event", year=2016, event_type_enum=EventType.OFFSEASON)
        event.put()

        status = SuggestionCreator.createEventWebcastSuggestion(
            self.account.key,
            "http://myweb.site/somewebcast",
            "",
            "2016test")
        self.assertEqual(status, 'success')
        suggestions = Suggestion.query().fetch()
        self.assertIsNotNone(suggestions)
        self.assertEqual(len(suggestions), 1)

        suggestion = suggestions[0]

        self.assertIsNotNone(suggestion)
        self.assertIsNotNone(suggestion.contents)
        self.assertIsNone(suggestion.contents.get('webcast_dict'))
        self.assertEqual(suggestion.contents.get('webcast_url'), "http://myweb.site/somewebcast")

    def test_webcast_already_exists(self):
        event = Event(id="2016test", name="Test Event", event_short="Test Event", year=2016,
                      event_type_enum=EventType.OFFSEASON,
                      webcast_json="[{\"type\": \"twitch\", \"channel\": \"frcgamesense\"}]")
        event.put()

        status = SuggestionCreator.createEventWebcastSuggestion(
            self.account.key,
            "http://twitch.tv/frcgamesense",
            "",
            "2016test")
        self.assertEqual(status, 'webcast_exists')

    def test_duplicate_suggestion(self):
        event = Event(id="2016test", name="Test Event", event_short="Test Event", year=2016, event_type_enum=EventType.OFFSEASON)
        event.put()

        status = SuggestionCreator.createEventWebcastSuggestion(
            self.account.key,
            "http://twitch.tv/frcgamesense",
            "",
            "2016test")
        self.assertEqual(status, 'success')
        status = SuggestionCreator.createEventWebcastSuggestion(
            self.account.key,
            "http://twitch.tv/frcgamesense",
            "",
            "2016test")
        self.assertEqual(status, 'suggestion_exists')

    def test_duplicate_unknown_suggestion_type(self):
        event = Event(id="2016test", name="Test Event", event_short="Test Event", year=2016, event_type_enum=EventType.OFFSEASON)
        event.put()

        status = SuggestionCreator.createEventWebcastSuggestion(
            self.account.key,
            "http://myweb.site/somewebcast",
            "",
            "2016test")
        self.assertEqual(status, 'success')
        status = SuggestionCreator.createEventWebcastSuggestion(
            self.account.key,
            "http://myweb.site/somewebcast",
            "",
            "2016test")
        self.assertEqual(status, 'suggestion_exists')

    def test_webcast_bad_date(self):
        event = Event(id="2016test", name="Test Event", event_short="Test Event", year=2016,
                      event_type_enum=EventType.OFFSEASON,
                      webcast_json="[{\"type\": \"twitch\", \"channel\": \"frcgamesense\"}]")
        event.put()

        status = SuggestionCreator.createEventWebcastSuggestion(
            self.account.key,
            "http://twitch.tv/frcgamesense",
            "BAD DATE",
            "2016test")
        self.assertEqual(status, 'invalid_date')

    def test_webcast_good_date(self):
        event = Event(id="2016test", name="Test Event", event_short="Test Event", year=2016, event_type_enum=EventType.OFFSEASON)
        event.put()

        status = SuggestionCreator.createEventWebcastSuggestion(
            self.account.key,
            "http://twitch.tv/frcgamesense",
            "2017-02-28",
            "2016test")

        self.assertEqual(status, 'success')
        suggestions = Suggestion.query().fetch()
        self.assertIsNotNone(suggestions)
        self.assertEqual(len(suggestions), 1)

        suggestion = suggestions[0]

        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.target_key, "2016test")
        self.assertEqual(suggestion.author, self.account.key)
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_PENDING)
        self.assertIsNotNone(suggestion.contents)
        self.assertEqual(suggestion.contents.get('webcast_url'), "http://twitch.tv/frcgamesense")
        self.assertIsNotNone(suggestion.contents.get('webcast_dict'))
        self.assertEqual(suggestion.contents.get('webcast_date'), "2017-02-28")


class TestSuggestMatchVideoYouTube(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()  # Prevent data from leaking between tests

        self.account = Account.get_or_insert(
            "123",
            email="user@example.com",
            registered=True)
        self.account.put()

        self.account_banned = Account.get_or_insert(
            "456",
            email="user@example.com",
            registered=True,
            shadow_banned=True,
        )
        self.account_banned.put()

        event = Event(id="2016test", name="Test Event", event_short="Test Event", year=2016, event_type_enum=EventType.OFFSEASON)
        event.put()
        self.match = Match(id="2016test_f1m1", event=ndb.Key(Event, "2016test"), year=2016, comp_level="f", set_number=1, match_number=1, alliances_json='')
        self.match.put()

    def tearDown(self):
        self.testbed.deactivate()

    def test_bad_match(self):
        status = SuggestionCreator.createMatchVideoYouTubeSuggestion(self.account.key, "37F5tbrFqJQ", "2016necmp_f1m2")
        self.assertEqual(status, 'bad_match')

    def test_create_suggestion(self):
        status = SuggestionCreator.createMatchVideoYouTubeSuggestion(self.account.key, "37F5tbrFqJQ", "2016test_f1m1")
        self.assertEqual(status, 'success')

        suggestion_id = "media_2016_match_2016test_f1m1_youtube_37F5tbrFqJQ"
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)

        self.assertEqual(suggestion.author, self.account.key)
        self.assertEqual(suggestion.target_key, '2016test_f1m1')
        self.assertEqual(suggestion.target_model, 'match')
        self.assertIsNotNone(suggestion.contents)
        self.assertIsNotNone(suggestion.contents.get('youtube_videos'))
        self.assertEqual(len(suggestion.contents.get('youtube_videos')), 1)
        self.assertEqual(suggestion.contents.get('youtube_videos')[0], "37F5tbrFqJQ")

    def test_create_suggestion_banned(self):
        status = SuggestionCreator.createMatchVideoYouTubeSuggestion(self.account_banned.key, "37F5tbrFqJQ", "2016test_f1m1")
        self.assertEqual(status, 'success')

        suggestion_id = "media_2016_match_2016test_f1m1_youtube_37F5tbrFqJQ"
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)

        self.assertEqual(suggestion.author, self.account_banned.key)
        self.assertEqual(suggestion.target_key, '2016test_f1m1')
        self.assertEqual(suggestion.target_model, 'match')
        self.assertIsNotNone(suggestion.contents)
        self.assertIsNotNone(suggestion.contents.get('youtube_videos'))
        self.assertEqual(len(suggestion.contents.get('youtube_videos')), 1)
        self.assertEqual(suggestion.contents.get('youtube_videos')[0], "37F5tbrFqJQ")
        self.assertEqual(suggestion.review_state, Suggestion.REVIEW_AUTOREJECTED)

    def test_existing_video(self):
        self.match.youtube_videos = ["37F5tbrFqJQ"]
        self.match.put()

        status = SuggestionCreator.createMatchVideoYouTubeSuggestion(self.account.key, "37F5tbrFqJQ", "2016test_f1m1")
        self.assertEqual(status, 'video_exists')

    def test_existing_suggestion(self):
        status = SuggestionCreator.createMatchVideoYouTubeSuggestion(self.account.key, "37F5tbrFqJQ", "2016test_f1m1")
        self.assertEqual(status, 'success')

        status = SuggestionCreator.createMatchVideoYouTubeSuggestion(self.account.key, "37F5tbrFqJQ", "2016test_f1m1")
        self.assertEqual(status, 'suggestion_exists')

    def test_bad_youtube_key(self):
        status = SuggestionCreator.createMatchVideoYouTubeSuggestion(self.account.key, "", "2016test_f1m1")
        self.assertEqual(status, 'bad_url')
