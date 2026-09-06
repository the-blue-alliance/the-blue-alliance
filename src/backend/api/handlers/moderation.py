import datetime
import json
import logging
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from flask import g, jsonify, make_response, request, Response
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.api.handlers.decorators import require_moderation_permission
from backend.common.consts.account_permission import SUGGESTION_PERMISSIONS
from backend.common.consts.auth_type import WRITE_TYPE_NAMES
from backend.common.consts.event_type import EventType
from backend.common.consts.media_type import IMAGE_TYPES
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.consts.suggestion_type import SuggestionType, TYPE_NAMES
from backend.common.datafeeds.datafeed_youtube import YoutubeVideoDetailsDatafeed
from backend.common.helpers.outgoing_notification_helper import (
    OutgoingNotificationHelper,
)
from backend.common.helpers.suggestion_fetcher import SuggestionFetcher
from backend.common.memcache import MemcacheClient
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.media import Media
from backend.common.models.suggestion import Suggestion
from backend.common.models.user import User
from backend.common.queries.event_query import EventListQuery
from backend.common.sitevars.google_api_secret import GoogleApiSecret
from backend.common.sitevars.slack_hook_urls import SlackHookUrls
from backend.common.suggestions.suggestion_reviewer import (
    REQUIRED_REVIEW_PERMISSIONS,
    SuggestionReviewer,
    SuggestionReviewResult,
)

MAX_SUGGESTIONS_PER_PAGE = 100
MAX_REJECT_BATCH = 500

# HTTP status for each review outcome (accept/reject endpoints return the
# outcome per suggestion; single-suggestion endpoints map it to the response
# status)
_OUTCOME_STATUS_CODES = {
    SuggestionReviewResult.ACCEPTED: 200,
    SuggestionReviewResult.REJECTED: 200,
    SuggestionReviewResult.NOT_FOUND: 404,
    SuggestionReviewResult.ALREADY_REVIEWED: 409,
    SuggestionReviewResult.INVALID: 400,
    SuggestionReviewResult.FORBIDDEN: 403,
}


@require_moderation_permission(SUGGESTION_PERMISSIONS)
def moderation_queue() -> Response:
    """Pending suggestion counts per type, filtered to what the caller can review."""
    user: User = g.moderation_user

    count_futures = {}
    for suggestion_type in SuggestionType:
        if SuggestionReviewer.user_can_review(user, suggestion_type):
            count_futures[suggestion_type] = SuggestionFetcher.count_async(
                SuggestionState.REVIEW_PENDING, suggestion_type.value
            )

    return jsonify(
        {
            "counts": {
                suggestion_type.value: future.get_result()
                for suggestion_type, future in count_futures.items()
            },
            "type_names": {
                suggestion_type.value: TYPE_NAMES[suggestion_type]
                for suggestion_type in count_futures.keys()
            },
        }
    )


@require_moderation_permission(SUGGESTION_PERMISSIONS)
def moderation_suggestion_list(suggestion_type: str) -> Response:
    """Pending suggestions of one type, decorated with review metadata."""
    user: User = g.moderation_user

    try:
        stype = SuggestionType(suggestion_type)
    except ValueError:
        return make_response(
            jsonify({"Error": f"Unknown suggestion type {suggestion_type}"}), 404
        )

    if not SuggestionReviewer.user_can_review(user, stype):
        return make_response(
            jsonify(
                {
                    "Error": f"Reviewing {suggestion_type} suggestions requires the "
                    f"{REQUIRED_REVIEW_PERMISSIONS[stype].name} permission"
                }
            ),
            403,
        )

    limit = max(
        1,
        min(request.args.get("limit", default=50, type=int), MAX_SUGGESTIONS_PER_PAGE),
    )
    total_future = SuggestionFetcher.count_async(
        SuggestionState.REVIEW_PENDING, stype.value
    )
    suggestions = (
        Suggestion.query()
        .filter(Suggestion.review_state == SuggestionState.REVIEW_PENDING)
        .filter(Suggestion.target_model == stype.value)
        .fetch(limit=limit)
    )

    # Group images first, matching the web review UI
    if stype in (SuggestionType.MEDIA, SuggestionType.EVENT_MEDIA):
        suggestions = sorted(
            suggestions,
            key=lambda x: 0 if x.contents["media_type_enum"] in IMAGE_TYPES else 1,
        )

    author_keys = list({s.author for s in suggestions})
    authors = ndb.get_multi(author_keys)
    authors_by_key = {none_throws(a.key): a for a in authors if a is not None}
    review_counts = _author_review_counts(author_keys)

    serialized = [
        _serialize_suggestion(
            s, authors_by_key.get(s.author), review_counts.get(s.author)
        )
        for s in suggestions
    ]
    _add_type_specific_metadata(stype, suggestions, serialized)

    return jsonify({"suggestions": serialized, "total": total_future.get_result()})


@require_moderation_permission(SUGGESTION_PERMISSIONS)
def moderation_suggestion_accept(suggestion_key: str) -> Response:
    """Accept a single pending suggestion, with optional type-specific overrides."""
    user: User = g.moderation_user
    overrides = request.get_json(silent=True) or {}
    if not isinstance(overrides, dict):
        return make_response(
            jsonify({"Error": "Request body must be a JSON object"}), 400
        )

    outcome = SuggestionReviewer.accept_suggestion(
        suggestion_key, user, overrides=overrides, endpoint=request.endpoint or ""
    )
    if outcome.result == SuggestionReviewResult.ACCEPTED:
        _send_apiwrite_review_alert(
            suggestion_key,
            user,
            verdict="accepted",
            user_message=overrides.get("user_message"),
            auth_id=outcome.created_target_key,
        )
    response: Dict[str, Any] = {
        "result": outcome.result.value,
        "suggestion_key": outcome.suggestion_key,
    }
    if outcome.created_target_key:
        response["created_target_key"] = outcome.created_target_key
    if outcome.message:
        response["message"] = outcome.message
    return make_response(jsonify(response), _OUTCOME_STATUS_CODES[outcome.result])


@require_moderation_permission(SUGGESTION_PERMISSIONS)
def moderation_suggestions_reject() -> Response:
    """Reject a batch of pending suggestions."""
    user: User = g.moderation_user
    body = request.get_json(silent=True) or {}
    suggestion_keys = body.get("suggestion_keys")
    if not isinstance(suggestion_keys, list) or not all(
        isinstance(k, str) for k in suggestion_keys
    ):
        return make_response(
            jsonify({"Error": "Request body must include suggestion_keys: [str]"}),
            400,
        )
    if len(suggestion_keys) > MAX_REJECT_BATCH:
        return make_response(
            jsonify({"Error": f"At most {MAX_REJECT_BATCH} suggestions per request"}),
            400,
        )

    outcomes = SuggestionReviewer.reject_suggestions(
        suggestion_keys, user, endpoint=request.endpoint or ""
    )
    for outcome in outcomes:
        if outcome.result == SuggestionReviewResult.REJECTED:
            _send_apiwrite_review_alert(
                outcome.suggestion_key,
                user,
                verdict="rejected",
                user_message=body.get("user_message"),
            )
    return jsonify(
        {
            "results": [
                {
                    "result": outcome.result.value,
                    "suggestion_key": outcome.suggestion_key,
                    **({"message": outcome.message} if outcome.message else {}),
                }
                for outcome in outcomes
            ]
        }
    )


def _get_suggestion_for_alert(suggestion_key: str) -> Optional[Suggestion]:
    try:
        return Suggestion.get_by_id(int(suggestion_key))
    except ValueError:
        return Suggestion.get_by_id(suggestion_key)


def _send_apiwrite_review_alert(
    suggestion_key: str,
    user: User,
    verdict: str,
    user_message: Optional[str],
    auth_id: Optional[str] = None,
) -> None:
    """
    Admin alert for reviewed Trusted API key requests, carrying forward the
    web review controller's (never-ported) admin email as a Slack alert on
    the existing suggestion-nag channel. Only apiwrite suggestions alert.
    """
    suggestion = _get_suggestion_for_alert(suggestion_key)
    if suggestion is None or suggestion.target_model != "api_auth_access":
        return
    channel_url = SlackHookUrls.url_for("suggestion-nag")
    if not channel_url:
        return

    event_key = suggestion.contents.get("event_key")
    # The default message mirrors the prefilled textarea on the review forms
    message = user_message or "Thanks for helping make TBA better!"
    body = (
        f"*Trusted API Key Request for {event_key}*\n"
        f"{user.display_name} ({user.email}) has {verdict} the request "
        f"with the following message:\n{message}"
    )
    if auth_id:
        body += (
            "\n<https://www.thebluealliance.com/admin/api_auth/edit/"
            f"{auth_id}|View the key>"
        )
    OutgoingNotificationHelper.send_slack_alert(channel_url, body)


AUTHOR_REVIEW_COUNT_CACHE_SECONDS = 60 * 60


def _author_review_counts(
    author_keys: List[ndb.Key],
) -> Dict[ndb.Key, Dict[str, int]]:
    """Lifetime accepted/rejected counts per author — a cheap reputation signal
    so reviewers can tell trusted suggesters from brand-new accounts.

    Counts are datastore count queries over each author's full suggestion
    history, so they're memcached for an hour; hour-stale reputation is fine.
    """
    if not author_keys:
        return {}
    cache = MemcacheClient.get()
    cache_keys = {
        author_key: f"moderation_author_review_counts:{author_key.id()}".encode()
        for author_key in author_keys
    }
    cached = cache.get_multi(list(cache_keys.values()))

    counts: Dict[ndb.Key, Dict[str, int]] = {}
    count_futures = {}
    for author_key, cache_key in cache_keys.items():
        hit = cached.get(cache_key)
        if isinstance(hit, dict):
            counts[author_key] = hit
        else:
            count_futures[author_key] = (
                Suggestion.query(
                    Suggestion.author == author_key,
                    Suggestion.review_state == SuggestionState.REVIEW_ACCEPTED,
                ).count_async(),
                Suggestion.query(
                    Suggestion.author == author_key,
                    Suggestion.review_state == SuggestionState.REVIEW_REJECTED,
                ).count_async(),
            )

    to_cache = {}
    for author_key, (accepted_future, rejected_future) in count_futures.items():
        value = {
            "accepted_count": accepted_future.get_result(),
            "rejected_count": rejected_future.get_result(),
        }
        counts[author_key] = value
        to_cache[cache_keys[author_key]] = value
    if to_cache:
        cache.set_multi(to_cache, time=AUTHOR_REVIEW_COUNT_CACHE_SECONDS)
    return counts


def _serialize_suggestion(
    suggestion: Suggestion,
    author: Optional[Any],
    author_review_counts: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    serialized: Dict[str, Any] = {
        "key": str(none_throws(suggestion.key.id())),
        "target_model": suggestion.target_model,
        "target_key": suggestion.target_key,
        "created": suggestion.created.isoformat() if suggestion.created else None,
        "contents": suggestion.contents,
        "author": (
            {
                "nickname": author.nickname,
                "email": author.email,
                **(author_review_counts or {}),
            }
            if author
            else None
        ),
    }

    # Parsed details + thumbnail for image suggestions, matching the web UI
    details_json = suggestion.contents.get("details_json")
    if details_json:
        try:
            details = json.loads(details_json)
        except ValueError:
            details = None
        if isinstance(details, dict):
            if "image_partial" in details:
                details["thumbnail"] = details["image_partial"].replace("_l", "_m")
            serialized["details"] = details

    # A preview of the Media that would be created, for media-backed types
    if "media_type_enum" in suggestion.contents:
        serialized["candidate_media"] = _serialize_candidate_media(suggestion)

    return serialized


def _serialize_candidate_media(suggestion: Suggestion) -> Dict[str, Any]:
    media = suggestion.candidate_media
    serialized = {
        "key": media.key_name,
        "media_type_enum": media.media_type_enum,
        "type_name": media.type_name,
        "slug_name": media.slug_name,
        "foreign_key": media.foreign_key,
        "is_image": media.is_image,
        # view_image_url is an absolute URL; Media.external_link is just the
        # bare foreign key and would render as a broken relative link.
        # view_image_url doesn't cover videos, so link YouTube directly.
        "external_link": media.view_image_url
        or (media.youtube_url_link if media.slug_name == "youtube" else None),
    }
    if media.is_image:
        serialized["view_image_url"] = media.view_image_url
        serialized["image_direct_url"] = media.image_direct_url_med
    if suggestion.contents.get("is_social"):
        serialized["social_profile_url"] = media.social_profile_url
    return serialized


def _add_type_specific_metadata(
    stype: SuggestionType,
    suggestions: List[Suggestion],
    serialized: List[Dict[str, Any]],
) -> None:
    """Decorate serialized suggestions with the context the web review UIs show."""
    if stype in (
        SuggestionType.MEDIA,
        SuggestionType.SOCIAL_MEDIA,
        SuggestionType.ROBOT,
        SuggestionType.EVENT_MEDIA,
    ):
        _add_reference_metadata(stype, suggestions, serialized)
    elif stype == SuggestionType.MATCH:
        _add_match_metadata(suggestions, serialized)
    elif stype == SuggestionType.EVENT:
        _add_webcast_metadata(suggestions, serialized)
    elif stype == SuggestionType.OFFSEASON_EVENT:
        _add_offseason_metadata(suggestions, serialized)
    elif stype == SuggestionType.API_AUTH_ACCESS:
        _add_apiwrite_metadata(suggestions, serialized)


def _serialize_reference(reference: Optional[Any]) -> Optional[Dict[str, Any]]:
    if reference is None:
        return None
    if isinstance(reference, Event):
        return {
            "type": "event",
            "key": reference.key_name,
            "name": reference.name,
            "year": reference.year,
            "start_date": (
                reference.start_date.date().isoformat()
                if reference.start_date
                else None
            ),
            "end_date": (
                reference.end_date.date().isoformat() if reference.end_date else None
            ),
        }
    return {
        "type": "team",
        "key": reference.key_name,
        "team_number": reference.team_number,
        "nickname": reference.nickname,
    }


def _add_reference_metadata(
    stype: SuggestionType,
    suggestions: List[Suggestion],
    serialized: List[Dict[str, Any]],
) -> None:
    """The referenced Team/Event, plus existing preferred images for team media."""
    reference_keys = [
        Media.create_reference(
            s.contents["reference_type"], s.contents["reference_key"]
        )
        for s in suggestions
    ]
    reference_futures = ndb.get_multi_async(reference_keys)

    existing_preferred_futures = None
    if stype == SuggestionType.MEDIA:
        existing_preferred_futures = [
            Media.query(
                Media.media_type_enum.IN(IMAGE_TYPES),  # pyre-ignore[16]
                Media.references == reference,
                Media.preferred_references == reference,
                Media.year == suggestion.contents["year"],
            ).fetch_async()
            for reference, suggestion in zip(reference_keys, suggestions)
        ]

    for i, future in enumerate(reference_futures):
        serialized[i]["reference"] = _serialize_reference(future.get_result())

    if existing_preferred_futures is not None:
        for i, future in enumerate(existing_preferred_futures):
            existing = future.get_result()
            serialized[i]["existing_preferred"] = [
                {
                    "key": media.key_name,
                    "foreign_key": media.foreign_key,
                    "media_type_enum": media.media_type_enum,
                    "view_image_url": media.view_image_url,
                    "image_direct_url": media.image_direct_url_med,
                }
                for media in existing
            ]
            serialized[i]["max_preferred"] = Media.MAX_PREFERRED


def _uses_official_webcast_unit(event: Optional[Event]) -> bool:
    if event and event.event_district_key:
        district = District.get_by_id(event.event_district_key)
        if district:
            return bool(district.uses_official_webcast_unit)
    return False


def _clean_youtube_id(raw_video_id: str) -> str:
    """Strip timestamp/query suffixes ("abc123?t=42") down to the bare video id."""
    return re.split(r"[?&#]", raw_video_id)[0]


def _fetch_youtube_video_details(video_ids: List[str]) -> Dict[str, Any]:
    """Title/duration for videos, batched 50 per API call (the API's cap).

    Assistive metadata only: returns {} when no YouTube API key is
    configured (dev environments) and never fails the queue on API errors.
    """
    if not video_ids or not GoogleApiSecret.secret_key():
        return {}
    details: Dict[str, Any] = {}
    try:
        for start in range(0, len(video_ids), 50):
            chunk = video_ids[start : start + 50]
            result = YoutubeVideoDetailsDatafeed(chunk).fetch_async().get_result()
            if result:
                details.update(result)
    except Exception:
        logging.warning("Failed to fetch YouTube video details", exc_info=True)
    return details


def _add_match_metadata(
    suggestions: List[Suggestion], serialized: List[Dict[str, Any]]
) -> None:
    """The match's event, official-webcast-unit warning flag, and YouTube
    title/duration so clients can flag suspicious video suggestions."""
    event_futures = [
        Event.get_by_id_async(none_throws(s.target_key).split("_")[0])
        for s in suggestions
    ]

    raw_video_ids = []
    for suggestion in suggestions:
        videos = suggestion.contents.get("youtube_videos") or []
        raw_video_ids.append(videos[0] if videos and isinstance(videos[0], str) else "")
    video_details = _fetch_youtube_video_details(
        sorted({_clean_youtube_id(raw) for raw in raw_video_ids if raw})
    )

    for i, future in enumerate(event_futures):
        event = future.get_result()
        serialized[i]["event"] = _serialize_reference(event)
        serialized[i]["uses_official_webcast_unit"] = _uses_official_webcast_unit(event)
        serialized[i]["has_first_official_webcast"] = (
            event.has_first_official_webcast if event else False
        )
        details = (
            video_details.get(_clean_youtube_id(raw_video_ids[i]))
            if raw_video_ids[i]
            else None
        )
        if details:
            serialized[i]["video_title"] = details.get("title")
            serialized[i]["video_duration_seconds"] = details.get("duration_seconds")


def _add_webcast_metadata(
    suggestions: List[Suggestion], serialized: List[Dict[str, Any]]
) -> None:
    """The event, existing webcasts (to catch duplicates), and warning flags."""
    event_futures = [
        Event.get_by_id_async(none_throws(s.target_key)) for s in suggestions
    ]
    for i, future in enumerate(event_futures):
        event = future.get_result()
        serialized[i]["event"] = _serialize_reference(event)
        serialized[i]["uses_official_webcast_unit"] = _uses_official_webcast_unit(event)
        serialized[i]["existing_webcasts"] = (
            list(event.webcast) if event and event.webcast else []
        )


def _normalized_event_name(name: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", name.lower()).split())


def _find_similar_events(
    name: str, events: List[Event], limit: int = 5
) -> List[Dict[str, str]]:
    """
    Offseason events whose name or short name resembles the suggested name.
    Comparison is case/punctuation-insensitive; containment (either direction)
    counts as a strong match. Results are strongest-match first.
    """
    normalized = _normalized_event_name(name)
    if not normalized:
        return []
    scored = []
    for event in events:
        best = 0.0
        for candidate in (event.name, event.short_name):
            if not candidate:
                continue
            normalized_candidate = _normalized_event_name(candidate)
            if not normalized_candidate:
                continue
            score = SequenceMatcher(a=normalized, b=normalized_candidate).ratio()
            if normalized in normalized_candidate or normalized_candidate in normalized:
                score = max(score, 0.9)
            best = max(best, score)
        if best > 0.5:
            scored.append((best, event))
    scored.sort(key=lambda pair: -pair[0])
    return [{"key": e.key_name, "name": e.name} for _, e in scored[:limit]]


def _suggested_event_year(suggestion: Suggestion) -> int:
    """The year of the suggested event's start date, falling back to today's."""
    start_date = suggestion.contents.get("start_date") or ""
    try:
        return datetime.datetime.strptime(start_date, "%Y-%m-%d").year
    except ValueError:
        return datetime.datetime.now().year


def _add_offseason_metadata(
    suggestions: List[Suggestion], serialized: List[Dict[str, Any]]
) -> None:
    """Similar-named offseason events in the suggested year and the year before."""
    years = {
        y
        for suggestion in suggestions
        for base_year in [_suggested_event_year(suggestion)]
        for y in (base_year, base_year - 1)
    }
    event_futures = {year: EventListQuery(year).fetch_async() for year in years}
    offseason_events_by_year = {
        year: [
            e for e in future.get_result() if e.event_type_enum == EventType.OFFSEASON
        ]
        for year, future in event_futures.items()
    }

    for i, suggestion in enumerate(suggestions):
        name = suggestion.contents.get("name") or ""
        year = _suggested_event_year(suggestion)
        serialized[i]["similar_events"] = _find_similar_events(
            name, offseason_events_by_year[year]
        )
        serialized[i]["similar_events_last_year"] = _find_similar_events(
            name, offseason_events_by_year[year - 1]
        )


def _add_apiwrite_metadata(
    suggestions: List[Suggestion], serialized: List[Dict[str, Any]]
) -> None:
    """The event, requested auth types by name, and existing keys for the event."""
    for i, suggestion in enumerate(suggestions):
        event_key = suggestion.contents["event_key"]
        serialized[i]["event"] = _serialize_reference(Event.get_by_id(event_key))
        serialized[i]["requested_auth_types"] = [
            {"type": int(t), "name": WRITE_TYPE_NAMES[t]}
            for t in suggestion.contents.get("auth_types", [])
            if t in WRITE_TYPE_NAMES
        ]

        existing_keys = ApiAuthAccess.query(
            ApiAuthAccess.event_list == ndb.Key(Event, event_key)
        ).fetch()
        existing_owners = ndb.get_multi(
            [key.owner for key in existing_keys if key.owner]
        )
        owners_by_key = {
            none_throws(o.key): o for o in existing_owners if o is not None
        }
        serialized[i]["existing_auth"] = [
            {
                "owner_email": (
                    owners_by_key[key.owner].email
                    if key.owner and key.owner in owners_by_key
                    else None
                ),
                "auth_types": [
                    {"type": int(t), "name": WRITE_TYPE_NAMES[t]}
                    for t in key.auth_types_enum
                    if t in WRITE_TYPE_NAMES
                ],
            }
            for key in existing_keys
        ]
