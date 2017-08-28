import re
import urlparse


class YouTubeVideoHelper(object):
    @classmethod
    def parse_id_from_url(cls, youtube_url):
        """
        Attempts to parse a URL for the video ID and timestamp (if present)
        Returns None if parsing fails
        Otherwise, returns "<youtube_id>" or "<youtube_id>?t=<start_seconds>"
        """
        youtube_id = None

        # Try to parse for ID
        regex1 = re.match(r".*youtu\.be\/([a-zA-Z0-9_-]*)", youtube_url)
        if regex1 is not None:
            youtube_id = regex1.group(1)
        else:
            regex2 = re.match(r".*v=([a-zA-Z0-9_-]*)", youtube_url)
            if regex2 is not None:
                youtube_id = regex2.group(1)
            else:
                regex3 = re.match(r".*/embed/([a-zA-Z0-9_-]*)", youtube_url)
                if regex3 is not None:
                    youtube_id = regex3.group(1)

        # Try to parse for time
        if youtube_id is not None:
            parsed = urlparse.urlparse(youtube_url)
            queries = urlparse.parse_qs(parsed.query)
            if 't' in queries:
                total_seconds = cls.time_to_seconds(queries['t'][0])
                youtube_id = '{}?t={}'.format(youtube_id, total_seconds)
            elif parsed.fragment and 't=' in parsed.fragment:
                total_seconds = cls.time_to_seconds(parsed.fragment.split('t=')[1])
                youtube_id = '{}?t={}'.format(youtube_id, total_seconds)

        return youtube_id

    @classmethod
    def time_to_seconds(cls, time_str):
        """
        Format time in seconds. Turns things like "3h17m30s" to "11850"
        """
        match = re.match('((?P<hour>\d*?)h)?((?P<min>\d*?)m)?((?P<sec>\d*)s?)?', time_str).groupdict()
        hours = match['hour'] or 0
        minutes = match['min'] or 0
        seconds = match['sec'] or 0
        total_seconds = (int(hours) * 3600) + (int(minutes) * 60) + int(seconds)
        return total_seconds
