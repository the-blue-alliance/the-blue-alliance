import re

from pyre_extensions import safe_json

from backend.common.datafeed_parsers.exceptions import ParserInputException
from backend.common.models.keys import EventKey, MatchKey
from backend.common.models.match import Match

YOUTUBE_VIDEO_ID_PATTERN = re.compile(r"^[0-9A-Za-z\-_]{11}$")


class JSONMatchVideoParser:
    """
    Take a dict of match partial -> youtube video ID

    Returns a dict of match key -> youtube ID
    """

    @staticmethod
    def parse[
        T: (str, bytes)
    ](event_key: EventKey, videos_json: T) -> dict[MatchKey, str]:  # fmt: skip
        video_dict = safe_json.loads(videos_json, dict[str, str])
        bad_match_ids = [
            match_partial
            for match_partial in video_dict
            if not Match.validate_key_name(f"{event_key}_{match_partial}")
        ]
        if bad_match_ids:
            raise ParserInputException(f"Invalid match IDs provided: {bad_match_ids}")

        bad_video_ids = [
            video_id
            for video_id in video_dict.values()
            if not YOUTUBE_VIDEO_ID_PATTERN.match(video_id)
        ]
        if bad_video_ids:
            raise ParserInputException(
                f"Invalid YouTube video IDs provided: {bad_video_ids}"
            )

        return {
            f"{event_key}_{match_partial}": video_id
            for match_partial, video_id in video_dict.items()
        }
