import unittest2

from tbans.models.notifications.payloads.payload import Payload

from tests.tbans.mocks.mock_payload import MockPayload


class TestPayload(unittest2.TestCase):

    def test_payload_dict(self):
        payload = Payload()
        with self.assertRaises(NotImplementedError):
            payload.payload_dict

    def test_set_payload_value(self):
        data = {}

        Payload._set_payload_value(data, 'one', None)
        self.assertEqual(data.get('one', 'test-default'), 'test-default')

        Payload._set_payload_value(data, 'one', 'two')
        self.assertEqual(data.get('one', 'test-default'), 'two')
