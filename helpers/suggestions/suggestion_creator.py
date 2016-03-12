from helpers.media_helper import MediaParser
from helpers.webcast_helper import WebcastParser

from models.event import Event
from models.media import Media
from models.suggestion import Suggestion


class SuggestionCreator(object):
    @classmethod
    def createTeamMediaSuggestion(cls, author_account_key, media_url, team_key, year_str, private_details_json=None):
        """Create a Team Media Suggestion. Returns status (success, suggestion_exists, media_exists, bad_url)"""

        media_dict = MediaParser.partial_media_dict_from_url(media_url.strip())
        if media_dict is not None:
            existing_media = Media.get_by_id(Media.render_key_name(media_dict['media_type_enum'], media_dict['foreign_key']))
            if existing_media is None or team_key not in [reference.id() for reference in existing_media.references]:
                foreign_type = Media.SLUG_NAMES[media_dict['media_type_enum']]
                suggestion_id = Suggestion.render_media_key_name(year_str, 'team', team_key, foreign_type, media_dict['foreign_key'])
                suggestion = Suggestion.get_by_id(suggestion_id)
                if not suggestion or suggestion.review_state != Suggestion.REVIEW_PENDING:
                    media_dict['year'] = int(year_str)
                    media_dict['reference_type'] = 'team'
                    media_dict['reference_key'] = team_key
                    if private_details_json is not None:
                        media_dict['private_details_json'] = private_details_json

                    suggestion = Suggestion(
                        id=suggestion_id,
                        author=author_account_key,
                        target_model="media",
                        )
                    suggestion.contents = media_dict
                    suggestion.put()
                    return 'success'
                else:
                    return 'suggestion_exists'
            else:
                return 'media_exists'
        else:
            return 'bad_url'

    @classmethod
    def createEventWebcastSuggestion(cls, author_account_key, webcast_url, event_key):
        """Create a Event Webcast Suggestion. Returns status string"""

        webcast_url = webcast_url.strip()
        if not webcast_url.startswith('http://') and not webcast_url.startswith('https://'):
            webcast_url = 'http://' + webcast_url

        webcast_dict = WebcastParser.webcast_dict_from_url(webcast_url)
        if webcast_dict is not None:
            # Check if webcast already exists in event
            event = Event.get_by_id(event_key)
            if event.webcast and webcast_dict in event.webcast:
                return 'webcast_exists'
            else:
                suggestion_id = Suggestion.render_webcast_key_name(event_key, webcast_dict)
                suggestion = Suggestion.get_by_id(suggestion_id)
                # Check if suggestion exists
                if not suggestion or suggestion.review_state != Suggestion.REVIEW_PENDING:
                    suggestion = Suggestion(
                        id=suggestion_id,
                        author=author_account_key,
                        target_model="event",
                        target_key=event_key,
                        )
                    suggestion.contents = {"webcast_dict": webcast_dict, "webcast_url": webcast_url}
                    suggestion.put()
                    return 'success'
                else:
                    return 'suggestion_exists'
        else:  # Can't parse URL -- could be an obscure webcast
            suggestion = Suggestion(
                author=author_account_key,
                target_model="event",
                target_key=event_key,
                )
            suggestion.contents = {"webcast_url": webcast_url}
            suggestion.put()
            return 'success'
