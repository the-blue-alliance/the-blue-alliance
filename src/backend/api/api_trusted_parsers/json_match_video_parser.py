from typing import AnyStr, Dict

from pyre_extensions import safe_json

from backend.common.datafeed_parsers.exceptions import ParserInputException
from backend.common.models.keys import EventKey, MatchKey
from backend.common.models.match import Match


class JSONMatchVideoParser:
    """
    Take a dict of match partial -> youtube video ID

    Returns a dict of match key -> youtube ID
    """

    @staticmethod
    def parse(event_key: EventKey, videos_json: AnyStr) -> Dict[MatchKey, str]:
        video_dict = safe_json.loads(videos_json, Dict[str, str])
        bad_match_ids = list(
            filter(
                lambda match_partial: not Match.validate_key_name(
                    f"{event_key}_{match_partial}"
                ),
                video_dict.keys(),
            )
        )
        if bad_match_ids:
            raise ParserInputException(f"Invalid match IDs provided: {bad_match_ids}")

        return {
            f"{event_key}_{match_partial}": video_id
            for match_partial, video_id in video_dict.items()
        }
