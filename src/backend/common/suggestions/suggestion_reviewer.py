import datetime
import enum
import json
import random
import string
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.auth_type import AuthType, WRITE_TYPE_NAMES
from backend.common.consts.event_type import EventType
from backend.common.consts.media_type import IMAGE_TYPES
from backend.common.consts.string_enum import StrEnum
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.consts.suggestion_type import SuggestionType
from backend.common.consts.webcast_type import WebcastType
from backend.common.helpers.event_webcast_adder import EventWebcastAdder
from backend.common.helpers.match_suggestion_accepter import MatchSuggestionAccepter
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.manipulators.media_manipulator import MediaManipulator
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.audit_log_entry import AuditLogEntry
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.media import Media
from backend.common.models.suggestion import Suggestion
from backend.common.models.user import User
from backend.common.models.webcast import Webcast
from backend.common.suggestions.media_creator import MediaCreator

# The AccountPermission required to review each type of suggestion. This
# mirrors the REQUIRED_PERMISSIONS on the web review controllers in
# backend/web/handlers/suggestions/.
REQUIRED_REVIEW_PERMISSIONS: Dict[SuggestionType, AccountPermission] = {
    SuggestionType.EVENT: AccountPermission.REVIEW_MEDIA,
    SuggestionType.MATCH: AccountPermission.REVIEW_MEDIA,
    SuggestionType.MEDIA: AccountPermission.REVIEW_MEDIA,
    SuggestionType.SOCIAL_MEDIA: AccountPermission.REVIEW_MEDIA,
    SuggestionType.OFFSEASON_EVENT: AccountPermission.REVIEW_OFFSEASON_EVENTS,
    SuggestionType.API_AUTH_ACCESS: AccountPermission.REVIEW_APIWRITE,
    SuggestionType.ROBOT: AccountPermission.REVIEW_DESIGNS,
    SuggestionType.EVENT_MEDIA: AccountPermission.REVIEW_EVENT_MEDIA,
}

# The NDB model kind name for the entity targeted by each suggestion type,
# used when writing AuditLogEntry records. This mirrors _audit_target_kind on
# the web review controllers. None means the target key is only known after
# the model is created (offseason events).
AUDIT_TARGET_KINDS: Dict[SuggestionType, Optional[str]] = {
    SuggestionType.EVENT: "Event",
    SuggestionType.MATCH: "Match",
    SuggestionType.MEDIA: "Team",
    SuggestionType.SOCIAL_MEDIA: "Team",
    SuggestionType.OFFSEASON_EVENT: None,
    SuggestionType.API_AUTH_ACCESS: "Event",
    SuggestionType.ROBOT: "Team",
    SuggestionType.EVENT_MEDIA: "Team",
}


@enum.unique
class SuggestionReviewResult(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NOT_FOUND = "not_found"
    ALREADY_REVIEWED = "already_reviewed"
    INVALID = "invalid"
    FORBIDDEN = "forbidden"


class ReviewOutcome(NamedTuple):
    result: SuggestionReviewResult
    suggestion_key: str
    created_target_key: Optional[str] = None
    message: Optional[str] = None


class SuggestionReviewer:
    """
    Shared accept/reject logic for Suggestions, decoupled from any request
    context so it can back both the web review controllers and the
    moderation API.

    Accepts run one at a time in an XG transaction with a REVIEW_PENDING
    re-check so that concurrent reviews of the same suggestion no-op safely.
    Type-specific reviewer inputs (year overrides, webcast fields, etc.) are
    passed as an explicit `overrides` dict; see _create_target_model for the
    keys each suggestion type understands.
    """

    @classmethod
    def user_can_review(cls, user: User, suggestion_type: SuggestionType) -> bool:
        if user.is_admin:
            return True
        required = REQUIRED_REVIEW_PERMISSIONS[suggestion_type]
        return required in (user.permissions or [])

    @classmethod
    def accept_suggestion(
        cls,
        suggestion_key: str,
        user: User,
        overrides: Optional[Dict[str, Any]] = None,
        endpoint: str = "",
    ) -> ReviewOutcome:
        """Accept a single pending Suggestion, creating its target model."""
        suggestion = cls._get_suggestion(suggestion_key)
        if suggestion is None:
            return ReviewOutcome(SuggestionReviewResult.NOT_FOUND, suggestion_key)

        suggestion_type = SuggestionType(suggestion.target_model)
        if not cls.user_can_review(user, suggestion_type):
            return ReviewOutcome(SuggestionReviewResult.FORBIDDEN, suggestion_key)

        return cls._accept_in_transaction(
            none_throws(suggestion.key), user, overrides or {}, endpoint
        )

    @classmethod
    @ndb.transactional(xg=True)
    def _accept_in_transaction(
        cls,
        suggestion_ndb_key: ndb.Key,
        user: User,
        overrides: Dict[str, Any],
        endpoint: str,
    ) -> ReviewOutcome:
        suggestion: Optional[Suggestion] = suggestion_ndb_key.get()
        suggestion_key = str(suggestion_ndb_key.id())
        if suggestion is None:
            return ReviewOutcome(SuggestionReviewResult.NOT_FOUND, suggestion_key)

        # Make sure the Suggestion hasn't been processed (by another thread)
        if suggestion.review_state != SuggestionState.REVIEW_PENDING:
            return ReviewOutcome(
                SuggestionReviewResult.ALREADY_REVIEWED, suggestion_key
            )

        try:
            created_key, error = cls._create_target_model(suggestion, overrides)
        except (KeyError, TypeError, ValueError) as e:
            return ReviewOutcome(
                SuggestionReviewResult.INVALID,
                suggestion_key,
                message=f"Invalid accept payload: {e}",
            )
        if created_key is None:
            return ReviewOutcome(
                SuggestionReviewResult.INVALID, suggestion_key, message=error
            )

        suggestion.review_state = SuggestionState.REVIEW_ACCEPTED
        suggestion.reviewer = user.account_key
        suggestion.reviewed_at = datetime.datetime.now()
        suggestion.put()

        cls._write_audit_log(suggestion, user, endpoint, overrides, created_key)
        return ReviewOutcome(
            SuggestionReviewResult.ACCEPTED,
            suggestion_key,
            created_target_key=created_key,
        )

    @classmethod
    def reject_suggestions(
        cls,
        suggestion_keys: List[str],
        user: User,
        endpoint: str = "",
    ) -> List[ReviewOutcome]:
        """
        Reject a batch of pending Suggestions. Each rejection runs in its own
        transaction; rejects create/delete no domain entities.
        """
        outcomes = []
        for suggestion_key in suggestion_keys:
            suggestion = cls._get_suggestion(suggestion_key)
            if suggestion is None:
                outcomes.append(
                    ReviewOutcome(SuggestionReviewResult.NOT_FOUND, suggestion_key)
                )
                continue

            suggestion_type = SuggestionType(suggestion.target_model)
            if not cls.user_can_review(user, suggestion_type):
                outcomes.append(
                    ReviewOutcome(SuggestionReviewResult.FORBIDDEN, suggestion_key)
                )
                continue

            outcomes.append(
                cls._reject_in_transaction(none_throws(suggestion.key), user, endpoint)
            )
        return outcomes

    @classmethod
    @ndb.transactional(xg=True)
    def _reject_in_transaction(
        cls, suggestion_ndb_key: ndb.Key, user: User, endpoint: str
    ) -> ReviewOutcome:
        suggestion: Optional[Suggestion] = suggestion_ndb_key.get()
        suggestion_key = str(suggestion_ndb_key.id())
        if suggestion is None:
            return ReviewOutcome(SuggestionReviewResult.NOT_FOUND, suggestion_key)

        if suggestion.review_state != SuggestionState.REVIEW_PENDING:
            return ReviewOutcome(
                SuggestionReviewResult.ALREADY_REVIEWED, suggestion_key
            )

        suggestion.review_state = SuggestionState.REVIEW_REJECTED
        suggestion.reviewer = user.account_key
        suggestion.reviewed_at = datetime.datetime.now()
        suggestion.put()

        cls._write_audit_log(suggestion, user, endpoint, {}, None)
        return ReviewOutcome(SuggestionReviewResult.REJECTED, suggestion_key)

    @classmethod
    def _create_target_model(
        cls, suggestion: Suggestion, overrides: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Create the domain entity for an accepted suggestion. Ported from the
        create_target_model implementations on the web review controllers.
        Returns (created_target_key, error_message).
        """
        suggestion_type = SuggestionType(suggestion.target_model)

        if suggestion_type == SuggestionType.MATCH:
            return cls._accept_match_video(suggestion, overrides)
        if suggestion_type == SuggestionType.MEDIA:
            return cls._accept_team_media(suggestion, overrides)
        if suggestion_type in (SuggestionType.SOCIAL_MEDIA, SuggestionType.ROBOT):
            media = MediaCreator.from_suggestion(suggestion)
            return str(none_throws(media.key.id())), None
        if suggestion_type == SuggestionType.EVENT_MEDIA:
            event_reference = Media.create_reference(
                suggestion.contents["reference_type"],
                suggestion.contents["reference_key"],
            )
            media = MediaCreator.create_media_model(suggestion, event_reference, [])
            media = MediaManipulator.createOrUpdate(media)
            return str(none_throws(media.key.id())), None
        if suggestion_type == SuggestionType.EVENT:
            return cls._accept_event_webcast(suggestion, overrides)
        if suggestion_type == SuggestionType.OFFSEASON_EVENT:
            return cls._accept_offseason_event(suggestion, overrides)
        if suggestion_type == SuggestionType.API_AUTH_ACCESS:
            return cls._accept_api_write(suggestion, overrides)

        return None, f"Unsupported suggestion type {suggestion_type}"

    @classmethod
    def _accept_match_video(
        cls, suggestion: Suggestion, overrides: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[str]]:
        # The reviewer may redirect the video to a different match
        target_key = overrides.get("target_match_key") or suggestion.target_key or ""
        match = Match.get_by_id(target_key)
        if not match:
            return None, f"Match {target_key} not found"
        MatchSuggestionAccepter.accept_suggestion(match, suggestion)
        return target_key, None

    @classmethod
    def _accept_team_media(
        cls, suggestion: Suggestion, overrides: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[str]]:
        # Reviewer inputs: year (int), set_preferred (bool),
        # replace_preferred_media_key (an existing Media key id to demote)
        to_replace_id: Optional[str] = overrides.get("replace_preferred_media_key")
        year = int(overrides.get("year") or none_throws(suggestion.contents["year"]))

        # Override year if necessary
        suggestion.contents["year"] = year
        suggestion.contents_json = json.dumps(suggestion.contents)
        suggestion._contents = None

        # Remove preferred reference from another Media if specified
        team_reference = Media.create_reference(
            suggestion.contents["reference_type"],
            suggestion.contents["reference_key"],
        )
        to_replace: Optional[Media] = None
        if to_replace_id:
            to_replace = Media.get_by_id(to_replace_id)
            if to_replace is None:
                return None, f"Media {to_replace_id} not found"
            if team_reference not in to_replace.preferred_references:
                # Preferred reference must have been edited earlier
                return None, f"Media {to_replace_id} is not preferred for this team"
            to_replace.preferred_references.remove(team_reference)

        # Only images can be preferred. When the reviewer doesn't say either
        # way, honor the suggester's default_preferred request.
        set_preferred = overrides.get("set_preferred")
        if set_preferred is None:
            set_preferred = bool(suggestion.contents.get("default_preferred"))
        media_type_enum = suggestion.contents["media_type_enum"]
        preferred_references = []
        if media_type_enum in IMAGE_TYPES and (set_preferred or to_replace_id):
            preferred_references = [team_reference]

        media = MediaCreator.create_media_model(
            suggestion, team_reference, preferred_references
        )

        if to_replace:
            MediaManipulator.createOrUpdate(to_replace, auto_union=False)
        media = MediaManipulator.createOrUpdate(media)
        return str(none_throws(media.key.id())), None

    @classmethod
    def _accept_event_webcast(
        cls, suggestion: Suggestion, overrides: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[str]]:
        # Reviewer inputs: webcast_type, webcast_channel, webcast_file,
        # webcast_date. Defaults come from the parsed webcast_dict when the
        # suggested URL was cleanly parseable.
        webcast_dict = suggestion.contents.get("webcast_dict") or {}
        webcast_type = overrides.get("webcast_type") or webcast_dict.get("type")
        webcast_channel = overrides.get("webcast_channel") or webcast_dict.get(
            "channel"
        )
        if not webcast_type or not webcast_channel:
            return None, "webcast_type and webcast_channel are required"
        try:
            webcast = Webcast(
                type=WebcastType(webcast_type),
                channel=webcast_channel,
            )
        except ValueError:
            return None, f"Invalid webcast_type {webcast_type}"

        webcast_file = overrides.get("webcast_file") or webcast_dict.get("file")
        if webcast_file:
            webcast["file"] = webcast_file
        webcast_date = overrides.get("webcast_date") or suggestion.contents.get(
            "webcast_date"
        )
        if webcast_date:
            webcast["date"] = webcast_date

        event_key = overrides.get("event_key") or suggestion.target_key or ""
        event = Event.get_by_id(event_key)
        if not event:
            return None, f"Event {event_key} not found"

        EventWebcastAdder.add_webcast(event, webcast)
        return event_key, None

    @classmethod
    def _accept_offseason_event(
        cls, suggestion: Suggestion, overrides: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[str]]:
        # Reviewer inputs: event_short (required), plus optional overrides of
        # every event field. Everything else defaults from the suggestion.
        contents = suggestion.contents
        event_short = (overrides.get("event_short") or "").lower()
        if not event_short:
            return None, "event_short is required to accept an offseason event"

        start_date_str = overrides.get("start_date") or contents.get("start_date")
        end_date_str = overrides.get("end_date") or contents.get("end_date")
        start_date = (
            datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
            if start_date_str
            else None
        )
        end_date = (
            datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
            if end_date_str
            else None
        )
        # Dateless events violate the APIv3 contract (start_date/end_date are
        # non-nullable) and break strict API clients, so refuse to create one
        if start_date is None or end_date is None:
            return (
                None,
                "start_date and end_date are required to accept an offseason event",
            )

        year = int(overrides.get("year") or start_date.year)
        event_key = f"{year}{event_short}"
        if not Event.validate_key_name(event_key):
            return None, f"Bad event key {event_key}"
        if Event.get_by_id(event_key):
            return None, f"Event {event_key} already exists"

        first_code = overrides.get("first_code") or contents.get("first_code")
        if first_code:
            first_code = first_code.upper()
        event_type_enum = EventType(
            int(overrides.get("event_type_enum", EventType.OFFSEASON))
        )

        event = Event(
            id=event_key,
            end_date=end_date,
            event_short=event_short,
            event_type_enum=event_type_enum,
            district_key=None,
            venue=overrides.get("venue") or contents.get("venue_name"),
            venue_address=overrides.get("venue_address") or contents.get("address"),
            city=overrides.get("city") or contents.get("city"),
            state_prov=overrides.get("state") or contents.get("state"),
            country=overrides.get("country") or contents.get("country"),
            name=overrides.get("name") or contents.get("name"),
            short_name=overrides.get("short_name"),
            start_date=start_date,
            website=overrides.get("website") or contents.get("website"),
            year=year,
            first_code=first_code,
            official=(first_code is not None and first_code != ""),
        )
        EventManipulator.createOrUpdate(event)
        return event_key, None

    @classmethod
    def _accept_api_write(
        cls, suggestion: Suggestion, overrides: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[str]]:
        # Reviewer inputs: auth_types (list of AuthType ints; defaults to the
        # requested types), expiration_days (int; -1 = no expiration; defaults
        # to 7 while event end + 7 days is still in the future)
        event_key = suggestion.contents["event_key"]
        event = Event.get_by_id(event_key)
        if not event:
            return None, f"Event {event_key} not found"
        author = none_throws(suggestion.author.get())

        requested_auth_types = suggestion.contents.get("auth_types", [])
        auth_types = overrides.get("auth_types")
        if auth_types is None:
            auth_types = requested_auth_types
        clean_auth_types = [
            AuthType(int(t)) for t in auth_types if int(t) in WRITE_TYPE_NAMES.keys()
        ]

        raw_expiration_days = overrides.get("expiration_days")
        if raw_expiration_days is None:
            # end_date is midnight starting the last event day, so +8 days is
            # the end of "event end + 7 days"
            if (
                event.end_date
                and event.end_date + datetime.timedelta(days=8)
                > datetime.datetime.now()
            ):
                raw_expiration_days = 7
            else:
                raw_expiration_days = -1
        expiration_days = int(raw_expiration_days)
        if expiration_days != -1:
            expiration_event_end = event.end_date + datetime.timedelta(
                days=expiration_days + 1
            )
            expiration_now = datetime.datetime.now() + datetime.timedelta(
                days=expiration_days
            )
            expiration = max(expiration_event_end, expiration_now)
        else:
            expiration = None

        auth_id = "".join(
            random.choice(
                string.ascii_lowercase + string.ascii_uppercase + string.digits
            )
            for _ in range(16)
        )
        auth = ApiAuthAccess(
            id=auth_id,
            description="{} @ {}".format(author.display_name, event_key),
            secret="".join(
                random.choice(
                    string.ascii_lowercase + string.ascii_uppercase + string.digits
                )
                for _ in range(64)
            ),
            event_list=[ndb.Key(Event, event_key)],
            auth_types_enum=clean_auth_types,
            owner=suggestion.author,
            expiration=expiration,
        )
        auth.put()
        return auth_id, None

    @classmethod
    def _get_suggestion(cls, suggestion_key: str) -> Optional[Suggestion]:
        suggestion = Suggestion.get_by_id(suggestion_key)
        if suggestion is None and suggestion_key.isdigit():
            # Some suggestion types (offseason events, apiwrite) have
            # auto-allocated integer IDs
            suggestion = Suggestion.get_by_id(int(suggestion_key))
        return suggestion

    @classmethod
    def _write_audit_log(
        cls,
        suggestion: Suggestion,
        user: User,
        endpoint: str,
        overrides: Dict[str, Any],
        created_key: Optional[str],
    ) -> None:
        suggestion_type = SuggestionType(suggestion.target_model)
        kind = AUDIT_TARGET_KINDS[suggestion_type]
        if kind is not None and suggestion.target_key:
            target_key = ndb.Key(kind, suggestion.target_key)
        elif suggestion_type == SuggestionType.OFFSEASON_EVENT and created_key:
            # The event only exists once the suggestion is accepted
            target_key = ndb.Key(Event, created_key)
        else:
            return
        AuditLogEntry(
            account=user.account_key,
            endpoint=endpoint,
            target_key=target_key,
            url_args={},
            form_params={
                str(k): [str(v)] for k, v in overrides.items() if v is not None
            },
        ).put()
