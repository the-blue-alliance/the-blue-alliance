import unittest2
from google.appengine.ext import ndb
from google.appengine.ext import testbed

from consts.media_type import MediaType
from helpers.media_helper import MediaParser
from helpers.suggestions.suggestion_creator import SuggestionCreator
from models.account import Account
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

    def tearDown(self):
        self.testbed.deactivate()

    def testCreateSuggestion(self):
        status = SuggestionCreator.createTeamMediaSuggestion(
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

    def testCreateSuggestionWithUrlParams(self):
        status = SuggestionCreator.createTeamMediaSuggestion(
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

    def testCleanUrl(self):
        status = SuggestionCreator.createTeamMediaSuggestion(
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

    def testDuplicateSuggestion(self):
        suggestion_id = Suggestion.render_media_key_name('2016', 'team', 'frc1124', 'imgur', 'ruRAxDm')
        Suggestion(
            id=suggestion_id,
            author=self.account.key,
            review_state=Suggestion.REVIEW_PENDING,
            target_key="2012cmp",
            target_model="event").put()

        status = SuggestionCreator.createTeamMediaSuggestion(
            self.account.key,
            "http://imgur.com/ruRAxDm",
            "frc1124",
            "2016")
        self.assertEqual(status, 'suggestion_exists')

    def testMediaExists(self):
        media_id = Media.render_key_name(MediaType.IMGUR, 'ruRAxDm')
        Media.get_or_insert(
            media_id,
            media_type_enum=MediaType.IMGUR,
            foreign_key='ruRAxDm',
            references=[ndb.Key(Team, 'frc1124')]).put()
        status = SuggestionCreator.createTeamMediaSuggestion(
            self.account.key,
            "http://imgur.com/ruRAxDm",
            "frc1124",
            "2016")
        self.assertEqual(status, 'media_exists')

    def testBadUrl(self):
        status = SuggestionCreator.createTeamMediaSuggestion(
            self.account.key,
            "http://foo.com/blah",
            "frc1124",
            "2016")
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

    def tearDown(self):
        self.testbed.deactivate()

    def testCreateSuggestion(self):
        status, _ = SuggestionCreator.createOffseasonEventSuggestion(
            self.account.key,
            "Test Event",
            "2016-5-1",
            "2016-5-2",
            "http://foo.bar.com",
            "123 Fake Street, New York, NY")
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
        self.assertEqual(suggestion.contents['address'], '123 Fake Street, New York, NY')

    def testMissingParameters(self):
        status, failures = SuggestionCreator.createOffseasonEventSuggestion(
            self.account.key,
            "",
            "2016-5-1",
            "2016-5-2",
            "http://foo.bar.com",
            "123 Fake Street, New York, NY")
        self.assertEqual(status, 'validation_failure')
        self.assertTrue('name' in failures)

        status, failures = SuggestionCreator.createOffseasonEventSuggestion(
            self.account.key,
            "Test Event",
            "",
            "2016-5-2",
            "http://foo.bar.com",
            "123 Fake Street, New York, NY")
        self.assertEqual(status, 'validation_failure')
        self.assertTrue('start_date' in failures)

        status, failures = SuggestionCreator.createOffseasonEventSuggestion(
            self.account.key,
            "Test Event",
            "2016-5-1",
            "",
            "http://foo.bar.com",
            "123 Fake Street, New York, NY")
        self.assertEqual(status, 'validation_failure')
        self.assertTrue('end_date' in failures)

        status, failures = SuggestionCreator.createOffseasonEventSuggestion(
            self.account.key,
            "Test Event",
            "2016-5-1",
            "2016-5-2",
            "",
            "123 Fake Street, New York, NY")
        self.assertEqual(status, 'validation_failure')
        self.assertTrue('website' in failures)

        status, failures = SuggestionCreator.createOffseasonEventSuggestion(
            self.account.key,
            "Test Event",
            "2016-5-1",
            "2016-5-2",
            "http://foo.bar.com",
            "")
        self.assertEqual(status, 'validation_failure')
        self.assertTrue('venue_address' in failures)

    def testOutOfOrderDates(self):
        status, failures = SuggestionCreator.createOffseasonEventSuggestion(
            self.account.key,
            "Test Event",
            "2016-5-4",
            "2016-5-2",
            "http://foo.bar.com",
            "123 Fake Street, New York, NY")
        self.assertEqual(status, 'validation_failure')
        self.assertTrue('end_date' in failures)

    def testMalformedDates(self):
        status, failures = SuggestionCreator.createOffseasonEventSuggestion(
            self.account.key,
            "Test Event",
            "meow",
            "2016-5-2",
            "http://foo.bar.com",
            "123 Fake Street, New York, NY")
        self.assertEqual(status, 'validation_failure')
        self.assertTrue('start_date' in failures)

        status, failures = SuggestionCreator.createOffseasonEventSuggestion(
            self.account.key,
            "Test Event",
            "2016-5-1",
            "moo",
            "http://foo.bar.com",
            "123 Fake Street, New York, NY")
        self.assertEqual(status, 'validation_failure')
        self.assertTrue('end_date' in failures)
