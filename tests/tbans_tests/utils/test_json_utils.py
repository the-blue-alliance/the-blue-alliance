import unittest2

from tbans.utils.json_utils import json_string_to_dict


class TestJSONUtils(unittest2.TestCase):

    def test_json_string_to_dict_list(self):
        self.assertEqual(json_string_to_dict('["a", "b", "c"]'), {})

    def test_json_string_to_dict_none(self):
        self.assertEqual(json_string_to_dict(None), {})

    def test_json_string_to_dict(self):
        self.assertEqual(json_string_to_dict('{"abc": "def"}'), {'abc': 'def'})
