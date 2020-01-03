import json
import unittest2

from datafeeds.parser_base import ParserInputException
from datafeeds.parsers.json.json_zebra_motion_parser import JSONZebraMotionParser
from google.appengine.ext import testbed


class TestJSONZebraMotionParser(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.data = {
            "times": [0.0, 0.5, 1.0, 1.5],
            "red": [
                {
                    "team_key": "frc254",
                    "xs": [None, 1.2, 1.3, 1.4],
                    "ys": [None, 0.1, 0.1, 0.1],
                },
                {
                    "team_key": "frc971",
                    "xs": [1.1, 1.2, 1.3, 1.4],
                    "ys": [0.1, 0.1, 0.1, 0.1],
                },
                {
                    "team_key": "frc604",
                    "xs": [1.1, 1.2, 1.3, 1.4],
                    "ys": [0.1, 0.1, 0.1, 0.1],
                },
            ],
            "blue": [
                {
                    "team_key": "frc1",
                    "xs": [None, 1.2, 1.3, 1.4],
                    "ys": [None, 0.1, 0.1, 0.1],
                },
                {
                    "team_key": "frc2",
                    "xs": [1.1, 1.2, 1.3, 1.4],
                    "ys": [0.1, 0.1, 0.1, 0.1],
                },
                {
                    "team_key": "frc3",
                    "xs": [1.1, 1.2, None, 1.4],
                    "ys": [0.1, 0.1, None, 0.1],
                },
            ],
        }

    def tearDown(self):
        self.testbed.deactivate()

    def testParser(self):
        parsed = JSONZebraMotionParser.parse(json.dumps(self.data))
        self.assertEqual(parsed, self.data)

    def testMissingTimes(self):
        del self.data['times']
        with self.assertRaises(ParserInputException):
            JSONZebraMotionParser.parse(json.dumps(self.data))

    def testEmptyTimes(self):
        self.data['times'] = []
        with self.assertRaises(ParserInputException):
            JSONZebraMotionParser.parse(json.dumps(self.data))

    def testNullTimes(self):
        self.data['times'][0] = None
        with self.assertRaises(ParserInputException):
            JSONZebraMotionParser.parse(json.dumps(self.data))

    def testIntTimes(self):
        self.data['times'][0] = 0
        with self.assertRaises(ParserInputException):
            JSONZebraMotionParser.parse(json.dumps(self.data))

    def testMissingTeamKey(self):
        del self.data['red'][0]['team_key']
        with self.assertRaises(ParserInputException):
            JSONZebraMotionParser.parse(json.dumps(self.data))

    def testMalformattedTeamKey(self):
        self.data['red'][0]['team_key'] = '254'
        with self.assertRaises(ParserInputException):
            JSONZebraMotionParser.parse(json.dumps(self.data))

    def testMissingCoords(self):
        del self.data['red'][0]['xs']
        with self.assertRaises(ParserInputException):
            JSONZebraMotionParser.parse(json.dumps(self.data))

    def testIntCoords(self):
        self.data['red'][0]['xs'][0] = 0
        with self.assertRaises(ParserInputException):
            JSONZebraMotionParser.parse(json.dumps(self.data))

    def testMismatchedNullCoords(self):
        self.data['red'][0]['xs'][1] = None
        with self.assertRaises(ParserInputException):
            JSONZebraMotionParser.parse(json.dumps(self.data))
