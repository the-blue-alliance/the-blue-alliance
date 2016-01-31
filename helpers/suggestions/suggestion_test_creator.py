from helpers.media_helper import MediaParser
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

        media_dict = MediaParser.partial_media_dict_from_url(self.YOUTUBE_URL)
        if media_dict is not None:
            existing_media = Media.get_by_id(Media.render_key_name(media_dict['media_type_enum'], media_dict['foreign_key']))
            if existing_media is None or team_key not in [reference.id() for reference in existing_media.references]:
                media_dict['year'] = 2016
                media_dict['reference_type'] = 'team'
                media_dict['reference_key'] = team.key_name

                suggestion = Suggestion(
                    author=user_bundle.account.key,
                    target_model="media",
                    )
                suggestion.contents = media_dict
                suggestion.put()

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
