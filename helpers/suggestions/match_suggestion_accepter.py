from helpers.match_manipulator import MatchManipulator
from models.match import Match

class MatchSuggestionAccepter(object):
    """
    Handle accepting Match suggestions.
    """
    
    @classmethod
    def acceptSuggestions(self, suggestions):
        matches = map(lambda match_future: match_future.get_result(),
            [Match.get_by_id_async(suggestion.target_key) for suggestion in suggestions])

        pairs = zip(matches, suggestions)

        for match, suggestion in pairs:
            self._acceptSuggestion(match, suggestion)

        matches, suggestions = zip(*pairs)
        
        matches = MatchManipulator.createOrUpdate(list(matches))

        return matches

    @classmethod
    def _acceptSuggestion(self, match, suggestion):
        if "youtube_videos" in suggestion.contents:
            match = self._mergeYouTubeVideos(match, suggestion.contents["youtube_videos"])

        return match

    @classmethod
    def _mergeYouTubeVideos(self, match, youtube_videos):
        for youtube_video in youtube_videos:
            if youtube_video not in match.youtube_videos:
                match.youtube_videos.append(youtube_video)
                match.dirty = True # This is so hacky. -gregmarra 20130601

        return match
