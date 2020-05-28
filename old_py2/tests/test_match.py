import unittest2

from google.appengine.ext import testbed

from models.match import Match


class TestMatch(unittest2.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()

    def tearDown(self):
        self.testbed.deactivate()

    def test_youtube_videos_formatted(self):
        # Test timestamp conversion
        data = {
            '5m6s': '306',
            '1m02s': '62',
            '10s': '10',
            '2m': '120',
            '12345': '12345',
            '5h': '18000',
            '1h2m3s': '3723',
        }
        for old_ts, seconds in data.items():
            match = Match(
                youtube_videos=['TqY324xLU4s#t=' + old_ts]
            )

            self.assertListEqual(match.youtube_videos_formatted, ['TqY324xLU4s?start=' + seconds])

            match = Match(
                youtube_videos=['TqY324xLU4s?t=' + old_ts]
            )

            self.assertListEqual(match.youtube_videos_formatted, ['TqY324xLU4s?start=' + seconds])

        # Test that nothing is changed if there is no timestamp
        match = Match(
            youtube_videos=['TqY324xLU4s']
        )
        self.assertListEqual(match.youtube_videos_formatted, ['TqY324xLU4s'])
