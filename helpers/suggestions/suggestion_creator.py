from helpers.media_helper import MediaParser

from models.media import Media
from models.suggestion import Suggestion


class SuggestionCreator(object):
    @classmethod
    def createTeamMediaSuggestion(cls, author_account_key, media_url, team_key, year_str):
        """Create a Team Media Suggestion. Returns status (success, exists, bad_url)"""

        media_dict = MediaParser.partial_media_dict_from_url(media_url)
        if media_dict is not None:
            existing_media = Media.get_by_id(Media.render_key_name(media_dict['media_type_enum'], media_dict['foreign_key']))
            if existing_media is None or team_key not in [reference.id() for reference in existing_media.references]:
                suggestion_id = Suggestion.render_key_name(year_str, 'team', team_key)
                suggestion = Suggestion.get_by_id(suggestion_id)
                if not suggestion or suggestion.review_state != Suggestion.REVIEW_PENDING:
                    media_dict['year'] = int(year_str)
                    media_dict['reference_type'] = 'team'
                    media_dict['reference_key'] = team_key

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
