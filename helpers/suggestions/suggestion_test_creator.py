from helpers.media_helper import MediaParser
from helpers.suggestions.suggestion_creator import SuggestionCreator
from helpers.user_bundle import UserBundle

from models.event import Event
from models.match import Match
from models.media import Media
from models.suggestion import Suggestion
from models.team import Team

class SuggestionTestCreator(object):
    YOUTUBE_ID = "dQw4w9WgXcQ"
    YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    @classmethod
    def createTeamMediaSuggestion(self):
        user_bundle = UserBundle()
        team = Team.query().fetch(1)[0]

        SuggestionCreator.createTeamMediaSuggestion(
            author_account_key=user_bundle.account.key,
            media_url=self.YOUTUBE_URL,
            team_key=team.key_name,
            year_str="2016")


    @classmethod
    def createMatchVideoSuggestion(self):
        user_bundle = UserBundle()
        match = Match.query().fetch(1)[0] #probably a cleaner way to do this

        suggestion = Suggestion(
            author=user_bundle.account.key,
            target_key=match.key_name,
            target_model="match")
        suggestion.contents = {"youtube_videos": [self.YOUTUBE_ID]}
        suggestion.put()

    @classmethod
    def createEventWebcastSuggestion(self):
        user_bundle = UserBundle()
        event = Event.query().fetch(1)[0]

        suggestion = Suggestion(
            author=user_bundle.account.key,
            target_key=event.key_name,
            target_model="event",
            )
        suggestion.contents = {"webcast_url": self.YOUTUBE_URL}
        suggestion.put()
