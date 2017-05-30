from helpers.match_manipulator import MatchManipulator
from models.match import Match


class MatchSuggestionAccepter(object):
    """
    Handle accepting Match suggestions.
    """

    @classmethod
    def accept_suggestion(self, match, suggestion):
        if "youtube_videos" in suggestion.contents:
            match = self._merge_youtube_videos(match, suggestion.contents["youtube_videos"])

        return MatchManipulator.createOrUpdate(match)

    @classmethod
    def _merge_youtube_videos(self, match, youtube_videos):
        for youtube_video in youtube_videos:
            if youtube_video not in match.youtube_videos:
                match.youtube_videos.append(youtube_video)

        return match
