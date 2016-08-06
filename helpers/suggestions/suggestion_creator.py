import logging
from datetime import datetime

from helpers.media_helper import MediaParser
from helpers.webcast_helper import WebcastParser

from models.event import Event
from models.match import Match
from models.media import Media
from models.suggestion import Suggestion


class SuggestionCreator(object):
    @classmethod
    def createTeamMediaSuggestion(cls, author_account_key, media_url, team_key, year_str, private_details_json=None, is_social=False):
        """Create a Team Media Suggestion. Returns status (success, suggestion_exists, media_exists, bad_url)"""

        media_dict = MediaParser.partial_media_dict_from_url(media_url)
        if media_dict is not None:
            if media_dict.get("is_social", False) != is_social:
                return 'bad_url'

            existing_media = Media.get_by_id(Media.render_key_name(media_dict['media_type_enum'], media_dict['foreign_key']))
            if existing_media is None or team_key not in [reference.id() for reference in existing_media.references]:
                foreign_type = Media.SLUG_NAMES[media_dict['media_type_enum']]
                suggestion_id = Suggestion.render_media_key_name(year_str, 'team', team_key, foreign_type, media_dict['foreign_key'])
                suggestion = Suggestion.get_by_id(suggestion_id)
                if not suggestion or suggestion.review_state != Suggestion.REVIEW_PENDING:
                    media_dict['year'] = int(year_str) if year_str else None
                    media_dict['reference_type'] = 'team'
                    media_dict['reference_key'] = team_key
                    if private_details_json is not None:
                        media_dict['private_details_json'] = private_details_json

                    target_model = "media"
                    if media_dict.get("is_social", False):
                        target_model = "social-media"

                    suggestion = Suggestion(
                        id=suggestion_id,
                        author=author_account_key,
                        target_model=target_model,
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

        try:
            webcast_dict = WebcastParser.webcast_dict_from_url(webcast_url)
        except Exception, e:
            logging.exception(e)
            webcast_dict = None

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
        else:  # Can't parse URL -- could be an obscure webcast. Save URL and let a human deal with it.
            contents = {"webcast_url": webcast_url}

            # Check if suggestion exists
            existing_suggestions = Suggestion.query(Suggestion.target_model=='event', Suggestion.target_key==event_key).fetch()
            for existing_suggestion in existing_suggestions:
                if existing_suggestion.contents == contents:
                    return 'suggestion_exists'

            suggestion = Suggestion(
                author=author_account_key,
                target_model="event",
                target_key=event_key,
                )
            suggestion.contents = contents
            suggestion.put()
            return 'success'

    @classmethod
    def createMatchVideoYouTubeSuggestion(cls, author_account_key, youtube_id, match_key):
        """Create a YouTube Match Video. Returns status (success, suggestion_exists, video_exists, bad_url)"""
        if youtube_id is not None:
            match = Match.get_by_id(match_key)
            if match and youtube_id not in match.youtube_videos:
                year = match_key[:4]
                suggestion_id = Suggestion.render_media_key_name(year, 'match', match_key, 'youtube', youtube_id)
                suggestion = Suggestion.get_by_id(suggestion_id)
                if not suggestion or suggestion.review_state != Suggestion.REVIEW_PENDING:
                    suggestion = Suggestion(
                        id=suggestion_id,
                        author=author_account_key,
                        target_key=match_key,
                        target_model="match",
                        )
                    suggestion.contents = {"youtube_videos": [youtube_id]}
                    suggestion.put()
                    return 'success'
                else:
                    return 'suggestion_exists'
            else:
                return 'video_exists'
        else:
            return 'bad_url'

    @classmethod
    def createOffseasonEventSuggestion(cls, author_account_key, name, start_date, end_date, website, address):
        """
        Create a suggestion for offseason event. Returns (status, failures):
        ('success', None)
        ('validation_failure', failures)
        """
        failures = {}
        if not name:
            failures['name'] = "Missing event name"
        if not start_date:
            failures['start_date'] = "Missing start date"
        if not end_date:
            failures['end_date'] = "Missing end date"
        if not website:
            failures['website'] = "Missing website"
        if not address:
            failures['venue_address'] = "Missing address"

        start_datetime = None
        end_datetime = None
        if start_date:
            try:
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                failures['start_date'] = "Invalid start date format (year-month-date)"

        if end_date:
            try:
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                failures['end_date'] = "Invalid end date format (year-month-date)"

        if start_datetime and end_datetime and end_datetime < start_datetime:
            failures['end_date'] = "End date must not be before the start date"

        if failures:
            return 'validation_failure', failures

        # Note that we don't specify an explicit key for event suggestions
        # We don't trust users to input correct event keys (that's for the moderator to do)
        suggestion = Suggestion(
            author=author_account_key,
            target_model="offseason-event",
        )
        suggestion.contents = {
            'name': name,
            'start_date': start_date,
            'end_date': end_date,
            'website': website,
            'address': address}
        suggestion.put()
        return 'success', None
