from helpers.match_manipulator import MatchManipulator
from models.match import Match


class MatchSuggestionAccepter(object):
    """
    Handle accepting Match suggestions.
    """

    @classmethod
    def accept_suggestions(self, suggestions):
        if (len(suggestions) < 1):
            return None

        matches = map(lambda match_future: match_future.get_result(),
                      [Match.get_by_id_async(suggestion.target_key) for suggestion in suggestions])

        pairs = zip(matches, suggestions)

        for match, suggestion in pairs:
            self._accept_suggestion(match, suggestion)

        matches, suggestions = zip(*pairs)

        matches = MatchManipulator.createOrUpdate(list(matches))

        return matches

    @classmethod
    def _accept_suggestion(self, match, suggestion):
        if "youtube_videos" in suggestion.contents:
            match = self._merge_youtube_videos(match, suggestion.contents["youtube_videos"])

        return match

    @classmethod
    def _merge_youtube_videos(self, match, youtube_videos):
        for youtube_video in youtube_videos:
            if youtube_video not in match.youtube_videos:
                match.youtube_videos.append(youtube_video)

        return match
