from typing import List
from backend.common.helpers.match_helper import TOrganizedMatches
from backend.common.consts import comp_level
from backend.common.models.match import Match


class PlaylistHelper(object):
    @classmethod
    def generate_playlist_link(
        cls,
        title: str,
        matches_organized: TOrganizedMatches,
        allow_levels: List[comp_level.CompLevel],
    ) -> str:
        video_ids = []
        playlist = ""
        for level in allow_levels:
            matches = matches_organized[level]
            for match in matches:
                video_ids += [video.split("?")[0] for video in match.youtube_videos]
        if video_ids:
            playlist = "https://www.youtube.com/watch_videos?video_ids={}&title={}"
            playlist = playlist.format(",".join(video_ids), title)

        return playlist
