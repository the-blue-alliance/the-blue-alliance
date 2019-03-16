import unittest2

from tbans.consts.subscriber_error import SubscriberError
from tbans.models.subscriptions.subscriber import Subscriber


class TestSubscriber(unittest2.TestCase):

    def test_token_type(self):
        with self.assertRaises(ValueError):
            Subscriber(token=1, result={})

    def test_token_none(self):
        with self.assertRaises(ValueError):
            Subscriber(token=None, result={})

    def test_token_empty(self):
        with self.assertRaises(ValueError):
            Subscriber(token='', result={})

    def test_result_type(self):
        with self.assertRaises(TypeError):
            Subscriber(token='abc', result=1)

    def test_result_none(self):
        with self.assertRaises(TypeError):
            Subscriber(token='abc', result=None)

    def test_init(self):
        subscriber = Subscriber(token='abc', result={})
        self.assertEqual(subscriber.token, 'abc')
        self.assertEqual(subscriber.error, None)

    def test_error(self):
        subscriber = Subscriber(token='abc', result={'error': 'TOO_MANY_TOPICS'})
        self.assertEqual(subscriber.token, 'abc')
        self.assertEqual(subscriber.error, SubscriberError.TOO_MANY_TOPICS)
