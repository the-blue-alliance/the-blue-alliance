from typing import List

from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.models.match import Match
from backend.common.models.suggestion import Suggestion


class MatchSuggestionAccepter(object):
    """
    Handle accepting Match suggestions.
    """

    @classmethod
    def accept_suggestion(self, match: Match, suggestion: Suggestion):
        if "youtube_videos" in suggestion.contents:
            match = self._merge_youtube_videos(
                match, suggestion.contents["youtube_videos"]
            )

        return MatchManipulator.createOrUpdate(match)

    @classmethod
    def _merge_youtube_videos(self, match: Match, youtube_videos: List[str]) -> Match:
        for youtube_video in youtube_videos:
            if youtube_video not in match.youtube_videos:
                match.youtube_videos.append(youtube_video)

        return match
