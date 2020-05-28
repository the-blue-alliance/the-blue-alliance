import logging
from datetime import datetime

from google.appengine.ext import ndb

from consts.auth_type import AuthType
from consts.event_type import EventType
from consts.media_type import MediaType
from helpers.website_helper import WebsiteHelper
from helpers.media_helper import MediaParser
from helpers.webcast_helper import WebcastParser

from models.account import Account
from models.event import Event
from models.match import Match
from models.media import Media
from models.suggestion import Suggestion


class SuggestionCreator(object):
    @classmethod
    def createTeamMediaSuggestion(cls, author_account_key, media_url, team_key, year_str, private_details_json=None, is_social=False, default_preferred=False):
        """Create a Team Media Suggestion. Returns status (success, suggestion_exists, media_exists, bad_url)"""

        media_dict = MediaParser.partial_media_dict_from_url(media_url)
        if media_dict is not None:
            if media_dict.get("is_social", False) != is_social:
                return 'bad_url', None

            existing_media = Media.get_by_id(Media.render_key_name(media_dict['media_type_enum'], media_dict['foreign_key']))
            if existing_media is None or team_key not in [reference.id() for reference in existing_media.references]:
                foreign_type = Media.SLUG_NAMES[media_dict['media_type_enum']]
                suggestion_id = Suggestion.render_media_key_name(year_str, 'team', team_key, foreign_type, media_dict['foreign_key'])
                suggestion = Suggestion.get_by_id(suggestion_id)
                if not suggestion or suggestion.review_state != Suggestion.REVIEW_PENDING:
                    media_dict['year'] = int(year_str) if year_str else None
                    media_dict['reference_type'] = 'team'
                    media_dict['reference_key'] = team_key
                    media_dict['default_preferred'] = default_preferred
                    if private_details_json is not None:
                        media_dict['private_details_json'] = private_details_json

                    target_model = "media"
                    if media_dict.get("is_social", False):
                        target_model = "social-media"

                    if media_dict.get('media_type', '') in MediaType.robot_types:
                        target_model = "robot"

                    if Event.validate_key_name(team_key):
                        target_model = 'event_media'
                        media_dict['reference_type'] = 'event'

                    suggestion = Suggestion(
                        id=suggestion_id,
                        author=author_account_key,
                        target_model=target_model,
                        target_key=team_key,
                        )
                    suggestion.contents = media_dict
                    suggestion.put()
                    return 'success', suggestion
                else:
                    return 'suggestion_exists', None
            else:
                return 'media_exists', None
        else:
            return 'bad_url', None

    @classmethod
    def createEventMediaSuggestion(cls, author_account_key, media_url, event_key, private_details_json=None):
        """Create an Event Media Suggestion. Returns status (success, suggestion_exists, media_exists, bad_url)"""

        media_dict = MediaParser.partial_media_dict_from_url(media_url)
        if media_dict is not None:
            if media_dict['media_type_enum'] != MediaType.YOUTUBE_VIDEO:
                return 'bad_url', None

            existing_media = Media.get_by_id(Media.render_key_name(media_dict['media_type_enum'], media_dict['foreign_key']))
            if existing_media is None or event_key not in [reference.id() for reference in existing_media.references]:
                foreign_type = Media.SLUG_NAMES[media_dict['media_type_enum']]
                suggestion_id = Suggestion.render_media_key_name(event_key[:4], 'event', event_key, foreign_type, media_dict['foreign_key'])
                suggestion = Suggestion.get_by_id(suggestion_id)
                if not suggestion or suggestion.review_state != Suggestion.REVIEW_PENDING:
                    media_dict['year'] = event_key[:4]
                    media_dict['reference_type'] = 'event'
                    media_dict['reference_key'] = event_key
                    target_model = 'event_media'
                    if private_details_json is not None:
                        media_dict['private_details_json'] = private_details_json

                    suggestion = Suggestion(
                        id=suggestion_id,
                        author=author_account_key,
                        target_model=target_model,
                        )
                    suggestion.contents = media_dict
                    suggestion.put()
                    return 'success', suggestion
                else:
                    return 'suggestion_exists', None
            else:
                return 'media_exists', None
        else:
            return 'bad_url', None

    @classmethod
    def createEventWebcastSuggestion(cls, author_account_key, webcast_url, webcast_date, event_key):
        """Create a Event Webcast Suggestion. Returns status string"""

        webcast_url = WebsiteHelper.format_url(webcast_url)

        webcast_date = webcast_date.strip()
        if webcast_date:
            try:
                datetime.strptime(webcast_date, "%Y-%m-%d")
            except ValueError:
                return 'invalid_date'
        else:
            webcast_date = None

        try:
            webcast_dict = WebcastParser.webcast_dict_from_url(webcast_url)
        except Exception, e:
            logging.exception(e)
            webcast_dict = None

        if webcast_dict is not None:
            # Check if webcast already exists in event
            event = Event.get_by_id(event_key)
            if not event:
                return 'bad_event'
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
                    suggestion.contents = {"webcast_dict": webcast_dict, "webcast_url": webcast_url, "webcast_date": webcast_date}
                    suggestion.put()
                    return 'success'
                else:
                    return 'suggestion_exists'
        else:  # Can't parse URL -- could be an obscure webcast. Save URL and let a human deal with it.
            contents = {"webcast_url": webcast_url, "webcast_date": webcast_date}

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
        if youtube_id:
            match = Match.get_by_id(match_key)
            if not match:
                return 'bad_match'
            if youtube_id not in match.youtube_videos:
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
    def createDummyOffseasonSuggestions(cls, events_to_suggest):
        """
        Create an offseason suggestion from a made up bot.
        Used to link offseasons with official data sync
        """
        keys_to_check = map(
            lambda event: ndb.Key(Suggestion, 'offseason_with_data_{}'.format(event.key_name)),
            events_to_suggest,
        )
        keys_found = ndb.get_multi(keys_to_check)
        logging.info("Fetched {} suggestion keys from ndb".format(len(keys_found)))

        # Make sure we have a dummy account to link these suggestions with
        account = Account.get_or_insert(
            'tba-bot-account',
            email='contact@thebluealliance.com',
            nickname='TBA-Bot',
            registered=True,
            permissions=[],
        )

        for event, suggestion, key in zip(events_to_suggest, keys_found, keys_to_check):
            if suggestion:
                # We've already created a suggestion for this event
                logging.info("Skipping creating a suggestion for {}".format(event.key_name))
                continue
            logging.info("Creating suggestion for {}".format(event.key_name))
            status, failures = cls.createOffseasonEventSuggestion(
                author_account_key=account.key,
                name=event.name,
                start_date=event.start_date.strftime("%Y-%m-%d"),
                end_date=event.end_date.strftime("%Y-%m-%d"),
                website=event.website,
                venue_name=event.venue,
                address=event.venue_address,
                city=event.city,
                state=event.state_prov,
                country=event.country,
                first_code=event.event_short.upper(),
                suggestion_id=key.id(),
            )
            if status != 'success':
                logging.warning("Failed to create suggestion: {}".format(failures))

    @classmethod
    def createOffseasonEventSuggestion(cls, author_account_key, name, start_date, end_date, website, venue_name, address, city, state, country, first_code=None, suggestion_id=None):
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
        if not venue_name:
            failures['venue_name'] = "Missing venue name"
        if not city:
            failures['venue_city'] = "Missing city"
        if not state:
            failures['venue_state'] = "Missing state"
        if not country:
            failures['venue_country'] = "Missing country"

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

        if failures and not suggestion_id:
            # Be more lenient with auto-added suggestions
            return 'validation_failure', failures

        # Note that we don't typically specify an explicit key for event suggestions
        # We don't trust users to input correct event keys (that's for the moderator to do)
        suggestion = Suggestion(id=suggestion_id) if suggestion_id else Suggestion()
        suggestion.author=author_account_key
        suggestion.target_model="offseason-event"
        suggestion.contents = {
            'name': name,
            'start_date': start_date,
            'end_date': end_date,
            'website': website,
            'venue_name': venue_name,
            'address': address,
            'city': city,
            'state': state,
            'country': country,
            'first_code': first_code,
        }
        suggestion.put()
        return 'success', None

    @classmethod
    def createApiWriteSuggestion(cls, author_account_key, event_key, affiliation, auth_types):
        """
        Create a suggestion for auth keys request.
        Returns status (success, no_affiliation, bad_event)
        """
        if not affiliation:
            return 'no_affiliation'

        if event_key:
            event = Event.get_by_id(event_key)
            if event:
                suggestion = Suggestion(
                    author=author_account_key,
                    target_model="api_auth_access",
                    target_key=event_key,
                )
                auth_types = [int(type) for type in auth_types]
                clean_auth_types = filter(lambda a: a in AuthType.write_type_names.keys(), auth_types)

                # If we're requesting keys for an official event, filter out everything but videos
                # Admin can still override this at review time, but it's unlikely
                if event.event_type_enum in EventType.SEASON_EVENT_TYPES:
                    clean_auth_types = filter(lambda a: a == AuthType.MATCH_VIDEO, clean_auth_types)

                suggestion.contents = {
                    'event_key': event_key,
                    'affiliation': affiliation,
                    'auth_types': clean_auth_types,
                }
                suggestion.put()
                return 'success'
            else:
                return 'bad_event'
        else:
            return 'bad_event'
