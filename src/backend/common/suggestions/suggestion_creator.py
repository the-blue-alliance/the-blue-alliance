import enum
import logging
from datetime import datetime
from typing import cast, Dict, List, Optional, Tuple

from google.cloud import ndb

from backend.common.consts.auth_type import AuthType, WRITE_TYPE_NAMES
from backend.common.consts.event_type import SEASON_EVENT_TYPES
from backend.common.consts.media_type import MediaType, ROBOT_TYPES, SLUG_NAMES
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.helpers.webcast_helper import WebcastParser
from backend.common.helpers.website_helper import WebsiteHelper
from backend.common.models.account import Account
from backend.common.models.event import Event
from backend.common.models.keys import EventKey, MatchKey, TeamKey
from backend.common.models.match import Match
from backend.common.models.media import Media
from backend.common.models.suggestion import Suggestion
from backend.common.models.suggestion_dict import SuggestionDict
from backend.common.suggestions.media_parser import MediaParser


@enum.unique
class SuggestionCreationStatus(str, enum.Enum):
    SUCCESS = "success"
    SUGGESTION_EXISTS = "suggestion_exists"
    BAD_URL = "bad_url"
    MEDIA_EXISTS = "media_exists"
    INVALID_DATE = "invalid_date"
    BAD_EVENT = "bad_event"
    BAD_MATCH = "bad_match"
    WEBCAST_EXISTS = "webcast_exists"
    VIDEO_EXISTS = "video_exists"
    VALIDATION_FAILURE = "validation_failure"
    NO_AFFILIATION = "no_affiliation"


class SuggestionCreator:
    @classmethod
    def createTeamMediaSuggestion(
        cls,
        author_account_key: ndb.Key,
        media_url: str,
        team_key: TeamKey,
        year_str: Optional[str],
        private_details_json: Optional[str] = None,
        is_social: bool = False,
        default_preferred: bool = False,
    ) -> Tuple[SuggestionCreationStatus, Optional[Suggestion]]:
        """Create a Team Media Suggestion. Returns status (success, suggestion_exists, media_exists, bad_url)"""

        year = int(year_str) if year_str else None
        media_dict = MediaParser.partial_media_dict_from_url(media_url)
        if media_dict is not None:
            if media_dict.get("is_social", False) != is_social:
                return SuggestionCreationStatus.BAD_URL, None

            existing_media = Media.get_by_id(
                Media.render_key_name(
                    media_dict["media_type_enum"], media_dict["foreign_key"]
                )
            )
            if existing_media is None or team_key not in [
                reference.id() for reference in existing_media.references
            ]:
                foreign_type = SLUG_NAMES[media_dict["media_type_enum"]]
                suggestion_id = Suggestion.render_media_key_name(
                    year, "team", team_key, foreign_type, media_dict["foreign_key"]
                )
                suggestion = Suggestion.get_by_id(suggestion_id)
                if (
                    not suggestion
                    or suggestion.review_state != SuggestionState.REVIEW_PENDING
                ):
                    media_dict["year"] = year
                    media_dict["reference_type"] = "team"
                    media_dict["reference_key"] = team_key
                    media_dict["default_preferred"] = default_preferred
                    if private_details_json is not None:
                        media_dict["private_details_json"] = private_details_json

                    target_model = "media"
                    if media_dict.get("is_social", False):
                        target_model = "social-media"

                    if media_dict.get("media_type_enum", "") in ROBOT_TYPES:
                        target_model = "robot"

                    if Event.validate_key_name(team_key):
                        target_model = "event_media"
                        media_dict["reference_type"] = "event"

                    suggestion = Suggestion(
                        id=suggestion_id,
                        author=author_account_key,
                        target_model=target_model,
                        target_key=team_key,
                    )
                    suggestion.contents = media_dict
                    suggestion.put()
                    return SuggestionCreationStatus.SUCCESS, suggestion
                else:
                    return SuggestionCreationStatus.SUGGESTION_EXISTS, None
            else:
                return SuggestionCreationStatus.MEDIA_EXISTS, None
        else:
            return SuggestionCreationStatus.BAD_URL, None

    @classmethod
    def createEventMediaSuggestion(
        cls,
        author_account_key: ndb.Key,
        media_url: str,
        event_key: EventKey,
        private_details_json: Optional[str] = None,
    ) -> Tuple[SuggestionCreationStatus, Optional[Suggestion]]:
        """Create an Event Media Suggestion. Returns status (success, suggestion_exists, media_exists, bad_url)"""

        media_dict = MediaParser.partial_media_dict_from_url(media_url)
        if media_dict is not None:
            if media_dict["media_type_enum"] != MediaType.YOUTUBE_VIDEO:
                return SuggestionCreationStatus.BAD_URL, None

            existing_media = Media.get_by_id(
                Media.render_key_name(
                    media_dict["media_type_enum"], media_dict["foreign_key"]
                )
            )
            if existing_media is None or event_key not in [
                reference.id() for reference in existing_media.references
            ]:
                foreign_type = SLUG_NAMES[media_dict["media_type_enum"]]
                suggestion_id = Suggestion.render_media_key_name(
                    int(event_key[:4]),
                    "event",
                    event_key,
                    foreign_type,
                    media_dict["foreign_key"],
                )
                suggestion = Suggestion.get_by_id(suggestion_id)
                if (
                    not suggestion
                    or suggestion.review_state != SuggestionState.REVIEW_PENDING
                ):
                    media_dict["year"] = int(event_key[:4])
                    media_dict["reference_type"] = "event"
                    media_dict["reference_key"] = event_key
                    target_model = "event_media"
                    if private_details_json is not None:
                        media_dict["private_details_json"] = private_details_json

                    suggestion = Suggestion(
                        id=suggestion_id,
                        author=author_account_key,
                        target_model=target_model,
                    )
                    suggestion.contents = media_dict
                    suggestion.put()
                    return SuggestionCreationStatus.SUCCESS, suggestion
                else:
                    return SuggestionCreationStatus.SUGGESTION_EXISTS, None
            else:
                return SuggestionCreationStatus.MEDIA_EXISTS, None
        else:
            return SuggestionCreationStatus.BAD_URL, None

    @classmethod
    def createEventWebcastSuggestion(
        cls,
        author_account_key: ndb.Key,
        webcast_url: str,
        webcast_date: str,
        event_key: EventKey,
    ) -> SuggestionCreationStatus:
        """Create a Event Webcast Suggestion. Returns status string"""

        clean_url = WebsiteHelper.format_url(webcast_url)
        if not clean_url:
            return SuggestionCreationStatus.BAD_URL

        webcast_date = webcast_date.strip()
        if webcast_date:
            try:
                datetime.strptime(webcast_date, "%Y-%m-%d")
                clean_date = webcast_date
            except ValueError:
                return SuggestionCreationStatus.INVALID_DATE
        else:
            clean_date = None

        try:
            webcast_dict = WebcastParser.webcast_dict_from_url(webcast_url)
        except Exception as e:
            logging.exception(e)
            webcast_dict = None

        if webcast_dict is not None:
            # Check if webcast already exists in event
            event = Event.get_by_id(event_key)
            if not event:
                return SuggestionCreationStatus.BAD_EVENT
            if event.webcast and webcast_dict in event.webcast:
                return SuggestionCreationStatus.WEBCAST_EXISTS
            else:
                suggestion_id = Suggestion.render_webcast_key_name(
                    event_key, webcast_dict
                )
                suggestion = Suggestion.get_by_id(suggestion_id)
                # Check if suggestion exists
                if (
                    not suggestion
                    or suggestion.review_state != SuggestionState.REVIEW_PENDING
                ):
                    suggestion = Suggestion(
                        id=suggestion_id,
                        author=author_account_key,
                        target_model="event",
                        target_key=event_key,
                    )
                    suggestion.contents = {
                        "webcast_dict": webcast_dict,
                        "webcast_url": clean_url,
                        "webcast_date": clean_date,
                    }
                    suggestion.put()
                    return SuggestionCreationStatus.SUCCESS
                else:
                    return SuggestionCreationStatus.SUGGESTION_EXISTS
        else:  # Can't parse URL -- could be an obscure webcast. Save URL and let a human deal with it.
            contents: SuggestionDict = {
                "webcast_url": webcast_url,
                "webcast_date": webcast_date,
            }

            # Check if suggestion exists
            existing_suggestions = Suggestion.query(
                Suggestion.target_model == "event", Suggestion.target_key == event_key
            ).fetch()
            for existing_suggestion in existing_suggestions:
                if cast(Suggestion, existing_suggestion).contents == contents:
                    return SuggestionCreationStatus.SUGGESTION_EXISTS

            suggestion = Suggestion(
                author=author_account_key,
                target_model="event",
                target_key=event_key,
            )
            suggestion.contents = contents
            suggestion.put()
            return SuggestionCreationStatus.SUCCESS

    @classmethod
    def createMatchVideoYouTubeSuggestion(
        cls, author_account_key: ndb.Key, youtube_id: str, match_key: MatchKey
    ) -> SuggestionCreationStatus:
        """Create a YouTube Match Video. Returns status (success, suggestion_exists, video_exists, bad_url)"""
        if youtube_id:
            match = Match.get_by_id(match_key)
            if not match:
                return SuggestionCreationStatus.BAD_MATCH
            if youtube_id not in match.youtube_videos:
                year = int(match_key[:4])
                suggestion_id = Suggestion.render_media_key_name(
                    year, "match", match_key, "youtube", youtube_id
                )
                suggestion = Suggestion.get_by_id(suggestion_id)
                if (
                    not suggestion
                    or suggestion.review_state != SuggestionState.REVIEW_PENDING
                ):
                    suggestion = Suggestion(
                        id=suggestion_id,
                        author=author_account_key,
                        target_key=match_key,
                        target_model="match",
                    )
                    suggestion.contents = {
                        "youtube_videos": [youtube_id],
                    }
                    suggestion.put()
                    return SuggestionCreationStatus.SUCCESS
                else:
                    return SuggestionCreationStatus.SUGGESTION_EXISTS
            else:
                return SuggestionCreationStatus.VIDEO_EXISTS
        else:
            return SuggestionCreationStatus.BAD_URL

    @classmethod
    def createDummyOffseasonSuggestions(cls, events_to_suggest: List[Event]) -> None:
        """
        Create an offseason suggestion from a made up bot.
        Used to link offseasons with official data sync
        """
        keys_to_check = map(
            lambda event: ndb.Key(
                Suggestion, "offseason_with_data_{}".format(event.key_name)
            ),
            events_to_suggest,
        )
        keys_found = ndb.get_multi(keys_to_check)
        logging.info("Fetched {} suggestion keys from ndb".format(len(keys_found)))

        # Make sure we have a dummy account to link these suggestions with
        account = Account.get_or_insert(
            "tba-bot-account",
            email="contact@thebluealliance.com",
            nickname="TBA-Bot",
            registered=True,
            permissions=[],
        )

        for event, suggestion, key in zip(events_to_suggest, keys_found, keys_to_check):
            if suggestion:
                # We've already created a suggestion for this event
                logging.info(
                    "Skipping creating a suggestion for {}".format(event.key_name)
                )
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
            if status != "success":
                logging.warning("Failed to create suggestion: {}".format(failures))

    @classmethod
    def createOffseasonEventSuggestion(
        cls,
        author_account_key: ndb.Key,
        name: str,
        start_date: str,
        end_date: str,
        website: str,
        venue_name: str,
        address: str,
        city: str,
        state: str,
        country: str,
        first_code: Optional[str] = None,
        suggestion_id: Optional[str] = None,
    ) -> Tuple[SuggestionCreationStatus, Optional[Dict[str, str]]]:
        """
        Create a suggestion for offseason event. Returns (status, failures):
        ('success', None)
        ('validation_failure', failures)
        """
        failures = {}
        if not name:
            failures["name"] = "Missing event name"
        if not start_date:
            failures["start_date"] = "Missing start date"
        if not end_date:
            failures["end_date"] = "Missing end date"
        if not website:
            failures["website"] = "Missing website"
        if not address:
            failures["venue_address"] = "Missing address"
        if not venue_name:
            failures["venue_name"] = "Missing venue name"
        if not city:
            failures["venue_city"] = "Missing city"
        if not state:
            failures["venue_state"] = "Missing state"
        if not country:
            failures["venue_country"] = "Missing country"

        start_datetime = None
        end_datetime = None
        if start_date:
            try:
                start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                failures["start_date"] = "Invalid start date format (year-month-date)"

        if end_date:
            try:
                end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                failures["end_date"] = "Invalid end date format (year-month-date)"

        if start_datetime and end_datetime and end_datetime < start_datetime:
            failures["end_date"] = "End date must not be before the start date"

        if failures and not suggestion_id:
            # Be more lenient with auto-added suggestions
            return SuggestionCreationStatus.VALIDATION_FAILURE, failures

        # Note that we don't typically specify an explicit key for event suggestions
        # We don't trust users to input correct event keys (that's for the moderator to do)
        suggestion = Suggestion(id=suggestion_id) if suggestion_id else Suggestion()
        suggestion.author = author_account_key
        suggestion.target_model = "offseason-event"
        suggestion.contents = {
            "name": name,
            "start_date": start_date,
            "end_date": end_date,
            "website": website,
            "venue_name": venue_name,
            "address": address,
            "city": city,
            "state": state,
            "country": country,
            "first_code": first_code,
        }
        suggestion.put()
        return SuggestionCreationStatus.SUCCESS, None

    @classmethod
    def createApiWriteSuggestion(
        cls,
        author_account_key: ndb.Key,
        event_key: EventKey,
        affiliation: str,
        auth_types: List[int],
    ) -> SuggestionCreationStatus:
        """
        Create a suggestion for auth keys request.
        Returns status (success, no_affiliation, bad_event)
        """
        if not affiliation:
            return SuggestionCreationStatus.NO_AFFILIATION

        if event_key:
            event = Event.get_by_id(event_key)
            clean_auth_types: List[AuthType] = []
            if event:
                suggestion = Suggestion(
                    author=author_account_key,
                    target_model="api_auth_access",
                    target_key=event_key,
                )
                clean_auth_types = [
                    AuthType(t) for t in auth_types if t in WRITE_TYPE_NAMES.keys()
                ]

                # If we're requesting keys for an official event, filter out everything but videos
                # Admin can still override this at review time, but it's unlikely
                if event.event_type_enum in SEASON_EVENT_TYPES:
                    clean_auth_types = list(
                        filter(lambda a: a == AuthType.MATCH_VIDEO, clean_auth_types)
                    )

                suggestion.contents = {
                    "event_key": event_key,
                    "affiliation": affiliation,
                    "auth_types": clean_auth_types,
                }
                suggestion.put()
                return SuggestionCreationStatus.SUCCESS
            else:
                return SuggestionCreationStatus.BAD_EVENT
        else:
            return SuggestionCreationStatus.BAD_EVENT
