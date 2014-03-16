import unittest2

from google.appengine.ext import testbed

from models.match import Match


class TestMatchManipulator(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()

    def test_youtube_videos_formatted(self):
        data = {
            '5m6s': '306',
            '1m02s': '62',
            '10s': '10',
            '2m': '120'
        }
        for old_ts, seconds in data.items():
            match = Match(
                youtube_videos=['TqY324xLU4s#t=' + old_ts]
            )

            self.assertListEqual(match.youtube_videos_formatted, ['TqY324xLU4s?start=' + seconds])

    def tearDown(self):
        self.testbed.deactivate()
