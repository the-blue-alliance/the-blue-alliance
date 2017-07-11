import unittest2

from helpers.youtube_video_helper import YouTubeVideoHelper


class TestYouTubeVideoHelper(unittest2.TestCase):
    def test_parse_id_from_url(self):
        # Standard HTTP
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('http://www.youtube.com/watch?v=1v8_2dW7Kik'), '1v8_2dW7Kik')
        # Standard HTTPS
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://www.youtube.com/watch?v=1v8_2dW7Kik'), '1v8_2dW7Kik')

        # Short link HTTP
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('http://youtu.be/1v8_2dW7Kik'), '1v8_2dW7Kik')
        # Short link HTTPS
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://youtu.be/1v8_2dW7Kik'), '1v8_2dW7Kik')

        # Standard with start time
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://www.youtube.com/watch?v=1v8_2dW7Kik&t=21'), '1v8_2dW7Kik?t=21')
        # Short link with start time
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://youtu.be/1v8_2dW7Kik?t=21'), '1v8_2dW7Kik?t=21')

        # Many URL params
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://www.youtube.com/watch?v=1v8_2dW7Kik&feature=youtu.be'), '1v8_2dW7Kik')
        # Short link many URL params
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://youtu.be/1v8_2dW7Kik?feature=youtu.be'), '1v8_2dW7Kik')

        # Many URL params with start time
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://www.youtube.com/watch?v=1v8_2dW7Kik&feature=youtu.be&t=11850'), '1v8_2dW7Kik?t=11850')
        # Short link many URL params with start time
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://youtu.be/1v8_2dW7Kik?feature=youtu.be&t=11850'), '1v8_2dW7Kik?t=11850')

        # Bunch of inconsistent (partially outdated) formats
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://www.youtube.com/watch?v=1v8_2dW7Kik#t=11850'), '1v8_2dW7Kik?t=11850')
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://www.youtube.com/watch?v=1v8_2dW7Kik#t=1h'), '1v8_2dW7Kik?t=3600')
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://www.youtube.com/watch?v=1v8_2dW7Kik#t=1h1m'), '1v8_2dW7Kik?t=3660')
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://www.youtube.com/watch?v=1v8_2dW7Kik#t=3h17m30s'), '1v8_2dW7Kik?t=11850')
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://www.youtube.com/watch?v=1v8_2dW7Kik#t=1m'), '1v8_2dW7Kik?t=60')
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://www.youtube.com/watch?v=1v8_2dW7Kik#t=1m1s'), '1v8_2dW7Kik?t=61')
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://www.youtube.com/watch?v=1v8_2dW7Kik#t=1s'), '1v8_2dW7Kik?t=1')

        # Bunch of inconsistent (partially outdated) formats with short links
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://youtu.be/1v8_2dW7Kik#t=11850'), '1v8_2dW7Kik?t=11850')
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://youtu.be/1v8_2dW7Kik#t=1h'), '1v8_2dW7Kik?t=3600')
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://youtu.be/1v8_2dW7Kik#t=1h1m'), '1v8_2dW7Kik?t=3660')
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://youtu.be/1v8_2dW7Kik#t=3h17m30s'), '1v8_2dW7Kik?t=11850')
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://youtu.be/1v8_2dW7Kik#t=1m'), '1v8_2dW7Kik?t=60')
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://youtu.be/1v8_2dW7Kik#t=1m1s'), '1v8_2dW7Kik?t=61')
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://youtu.be/1v8_2dW7Kik#t=1s'), '1v8_2dW7Kik?t=1')

        # Not sure where this comes from, but it can happen
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://youtu.be/1v8_2dW7Kik?t=3h17m30s'), '1v8_2dW7Kik?t=11850')
        self.assertEqual(YouTubeVideoHelper.parse_id_from_url('https://www.youtube.com/watch?v=1v8_2dW7Kik&t=3h17m30s'), '1v8_2dW7Kik?t=11850')
