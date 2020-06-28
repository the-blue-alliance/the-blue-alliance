from typing import List, Optional

from backend.common.models.keys import EventKey, MatchKey


class TBAVideo(object):
    """
    Same interface as the retired TBAVideo class.
    """

    TBA_NET_VID_PATTERN = "http://videos.thebluealliance.net/%s/%s.%s"

    THUMBNAIL_FILETYPES = ["jpg", "jpeg"]
    STREAMABLE_FILETYPES = ["mp4", "flv"]
    DOWNLOADABLE_FILETYPES = ["mp4", "mov", "avi", "wmv", "flv"]

    event_key: EventKey
    match_key: MatchKey

    # A list of filetypes where videos exist
    match_tba_videos: List[str]

    def __init__(
        self, event_key: EventKey, match_key: MatchKey, match_tba_videos: List[str]
    ):
        self.event_key = event_key
        self.match_key = match_key
        self.match_tba_videos = match_tba_videos

    @property
    def thumbnail_path(self) -> Optional[str]:
        return self._best_path_of(self.THUMBNAIL_FILETYPES)

    @property
    def streamable_path(self) -> Optional[str]:
        return self._best_path_of(self.STREAMABLE_FILETYPES)

    @property
    def downloadable_path(self) -> Optional[str]:
        return self._best_path_of(self.DOWNLOADABLE_FILETYPES)

    def _best_path_of(self, consider_filetypes: List[str]) -> Optional[str]:
        for filetype in consider_filetypes:
            if filetype in self.match_tba_videos:
                return self.TBA_NET_VID_PATTERN % (
                    self.event_key,
                    self.match_key,
                    filetype,
                )
        return None
