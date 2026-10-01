import datetime
import json
from typing import Any, cast, Dict, Optional
from unittest.mock import patch

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.auth_type import AuthType
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.media_type import MediaType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.consts.suggestion_type import SuggestionType
from backend.common.consts.webcast_type import WebcastType
from backend.common.manipulators.media_manipulator import MediaManipulator
from backend.common.models.account import Account
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.audit_log_entry import AuditLogEntry
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.media import Media
from backend.common.models.suggestion import Suggestion
from backend.common.models.suggestion_dict import SuggestionDict
from backend.common.models.team import Team
from backend.common.models.team_admin_access import TeamAdminAccess
from backend.common.models.user import User
from backend.common.suggestions.suggestion_creator import SuggestionCreator
from backend.common.suggestions.suggestion_reviewer import (
    ReviewOutcome,
    SuggestionReviewer,
    SuggestionReviewResult,
    TEAM_ADMIN_REVIEWABLE_TYPES,
)
from backend.common.suggestions.tests.conftest import make_user


def _grant_team_admin(user: User, team_number: int, expired: bool = False) -> None:
    TeamAdminAccess(
        id=f"access_{team_number}",
        team_number=team_number,
        year=2026,
        expiration=datetime.datetime.now()
        + datetime.timedelta(days=-1 if expired else 1),
        account=user.account_key,
    ).put()


def _pending_suggestion(target_model: str, target_key: str) -> Suggestion:
    return Suggestion(
        author=ndb.Key(Account, "author"),
        target_model=target_model,
        target_key=target_key,
        review_state=SuggestionState.REVIEW_PENDING,
    )


def _create_media_suggestion(team_key: str = "frc1124") -> str:
    Team(id=team_key, team_number=int(team_key[3:])).put()
    status, suggestion = SuggestionCreator.createTeamMediaSuggestion(
        ndb.Key(Account, "author"),
        "http://imgur.com/foobar",
        team_key,
        "2024",
    ).get_result()
    assert status == "success"
    return str(none_throws(none_throws(suggestion).key).id())


def test_team_admin_reviewable_types_are_team_targeted() -> None:
    assert TEAM_ADMIN_REVIEWABLE_TYPES == {
        SuggestionType.MEDIA,
        SuggestionType.SOCIAL_MEDIA,
        SuggestionType.ROBOT,
    }


def test_global_permission_can_review_without_delegation(ndb_stub) -> None:
    user = make_user([AccountPermission.REVIEW_MEDIA])
    suggestion = _pending_suggestion("media", "frc254")
    assert SuggestionReviewer.user_can_review_suggestion(user, suggestion)


def test_admin_can_review_without_delegation(ndb_stub) -> None:
    user = make_user([], is_admin=True)
    suggestion = _pending_suggestion("media", "frc254")
    assert SuggestionReviewer.user_can_review_suggestion(user, suggestion)


def test_no_permission_no_delegation_cannot_review(ndb_stub) -> None:
    user = make_user([])
    suggestion = _pending_suggestion("media", "frc254")
    assert not SuggestionReviewer.user_can_review_suggestion(user, suggestion)


def test_delegated_team_admin_can_review_own_team(ndb_stub) -> None:
    user = make_user([])
    _grant_team_admin(user, 254)
    for target_model in ("media", "social-media", "robot"):
        suggestion = _pending_suggestion(target_model, "frc254")
        # Looked up from TeamAdminAccess when the caller passes nothing
        assert SuggestionReviewer.user_can_review_suggestion(
            user, suggestion
        ), target_model


def test_delegated_team_keys_ignores_expired_access(ndb_stub) -> None:
    user = make_user([])
    _grant_team_admin(user, 254, expired=True)
    assert SuggestionReviewer.delegated_team_keys(user) == set()
    suggestion = _pending_suggestion("media", "frc254")
    assert not SuggestionReviewer.user_can_review_suggestion(user, suggestion)


def test_precomputed_delegation_is_honored_without_a_lookup(ndb_stub) -> None:
    user = make_user([])
    suggestion = _pending_suggestion("media", "frc254")
    assert SuggestionReviewer.user_can_review_suggestion(
        user, suggestion, delegated_team_keys={"frc254"}
    )
    assert not SuggestionReviewer.user_can_review_suggestion(
        user, suggestion, delegated_team_keys=set()
    )


def test_delegated_team_admin_cannot_review_other_team(ndb_stub) -> None:
    user = make_user([])
    _grant_team_admin(user, 254)
    suggestion = _pending_suggestion("media", "frc1678")
    assert not SuggestionReviewer.user_can_review_suggestion(user, suggestion)


def test_delegated_team_admin_cannot_review_non_team_types(ndb_stub) -> None:
    # Even if a suggestion's target key happens to match, delegation only
    # covers the team-targeted suggestion types
    user = make_user([])
    _grant_team_admin(user, 254)
    for target_model in ("match", "event", "event_media", "offseason-event"):
        suggestion = _pending_suggestion(target_model, "frc254")
        assert not SuggestionReviewer.user_can_review_suggestion(
            user, suggestion
        ), target_model


def test_delegated_team_admin_cannot_review_suggestion_without_target(
    ndb_stub,
) -> None:
    user = make_user([])
    _grant_team_admin(user, 254)
    suggestion = _pending_suggestion("media", None)  # pyre-ignore[6]
    assert not SuggestionReviewer.user_can_review_suggestion(user, suggestion)


def test_accept_with_delegation(ndb_stub, taskqueue_stub) -> None:
    user = make_user([])
    _grant_team_admin(user, 1124)
    suggestion_id = _create_media_suggestion("frc1124")

    outcome = SuggestionReviewer.accept_suggestion(
        suggestion_id,
        user,
        overrides={"set_preferred": True},
        endpoint="team_admin.team_mod_review",
    )

    assert outcome.result == SuggestionReviewResult.ACCEPTED
    suggestion = none_throws(Suggestion.get_by_id(suggestion_id))
    assert suggestion.review_state == SuggestionState.REVIEW_ACCEPTED
    assert suggestion.reviewer == user.account_key
    medias = Media.query().fetch()
    assert len(medias) == 1
    assert ndb.Key(Team, "frc1124") in medias[0].preferred_references
    audit_entries = AuditLogEntry.query().fetch()
    assert len(audit_entries) == 1
    assert audit_entries[0].endpoint == "team_admin.team_mod_review"
    # The target is the team; the entry must still say which suggestion
    assert audit_entries[0].url_args == {"suggestion_key": suggestion_id}


def test_accept_forbidden_for_other_team(ndb_stub, taskqueue_stub) -> None:
    user = make_user([])
    _grant_team_admin(user, 254)
    suggestion_id = _create_media_suggestion("frc1124")

    outcome = SuggestionReviewer.accept_suggestion(suggestion_id, user)

    assert outcome.result == SuggestionReviewResult.FORBIDDEN
    suggestion = none_throws(Suggestion.get_by_id(suggestion_id))
    assert suggestion.review_state == SuggestionState.REVIEW_PENDING
    assert Media.query().count() == 0


def test_reject_with_delegation(ndb_stub, taskqueue_stub) -> None:
    user = make_user([])
    _grant_team_admin(user, 1124)
    suggestion_id = _create_media_suggestion("frc1124")

    outcomes = SuggestionReviewer.reject_suggestions([suggestion_id], user)

    assert [o.result for o in outcomes] == [SuggestionReviewResult.REJECTED]
    suggestion = none_throws(Suggestion.get_by_id(suggestion_id))
    assert suggestion.review_state == SuggestionState.REVIEW_REJECTED
    assert Media.query().count() == 0
    audit_entries = AuditLogEntry.query().fetch()
    assert len(audit_entries) == 1
    assert audit_entries[0].url_args == {"suggestion_key": suggestion_id}


def test_reject_forbidden_for_other_team(ndb_stub, taskqueue_stub) -> None:
    user = make_user([])
    _grant_team_admin(user, 254)
    suggestion_id = _create_media_suggestion("frc1124")

    outcomes = SuggestionReviewer.reject_suggestions([suggestion_id], user)

    assert [o.result for o in outcomes] == [SuggestionReviewResult.FORBIDDEN]
    suggestion = none_throws(Suggestion.get_by_id(suggestion_id))
    assert suggestion.review_state == SuggestionState.REVIEW_PENDING


def test_offseason_first_code_is_stripped_and_uppercased(
    ndb_stub, taskqueue_stub
) -> None:
    user = make_user([AccountPermission.REVIEW_OFFSEASON_EVENTS])
    suggestion = Suggestion(
        id=77,
        author=ndb.Key(Account, "author"),
        target_model="offseason-event",
        review_state=SuggestionState.REVIEW_PENDING,
    )
    suggestion.contents = {
        "name": "Indiana Robotics Invitational",
        "start_date": "2026-07-16",
        "end_date": "2026-07-18",
    }
    suggestion.put()

    outcome = SuggestionReviewer.accept_suggestion(
        "77", user, overrides={"event_short": "iri", "first_code": " iri "}
    )

    assert outcome.result == SuggestionReviewResult.ACCEPTED
    from backend.common.models.event import Event

    event = none_throws(Event.get_by_id("2026iri"))
    assert event.first_code == "IRI"
    assert event.official is True


def test_offseason_blank_first_code_is_unofficial(ndb_stub, taskqueue_stub) -> None:
    user = make_user([AccountPermission.REVIEW_OFFSEASON_EVENTS])
    suggestion = Suggestion(
        id=78,
        author=ndb.Key(Account, "author"),
        target_model="offseason-event",
        review_state=SuggestionState.REVIEW_PENDING,
    )
    suggestion.contents = {
        "name": "Local Offseason",
        "start_date": "2026-07-16",
        "end_date": "2026-07-18",
    }
    suggestion.put()

    outcome = SuggestionReviewer.accept_suggestion(
        "78", user, overrides={"event_short": "local", "first_code": "   "}
    )

    assert outcome.result == SuggestionReviewResult.ACCEPTED
    from backend.common.models.event import Event

    event = none_throws(Event.get_by_id("2026local"))
    assert event.first_code is None
    assert event.official is False


def test_offseason_cleared_first_code_makes_event_unofficial(
    ndb_stub, taskqueue_stub
) -> None:
    # The suggester supplied a code; the reviewer cleared the field
    user = make_user([AccountPermission.REVIEW_OFFSEASON_EVENTS])
    suggestion = Suggestion(
        id=79,
        author=ndb.Key(Account, "author"),
        target_model="offseason-event",
        review_state=SuggestionState.REVIEW_PENDING,
    )
    suggestion.contents = {
        "name": "Not Actually Official",
        "start_date": "2026-07-16",
        "end_date": "2026-07-18",
        "first_code": "IRI",
    }
    suggestion.put()

    outcome = SuggestionReviewer.accept_suggestion(
        "79", user, overrides={"event_short": "nao", "first_code": ""}
    )

    assert outcome.result == SuggestionReviewResult.ACCEPTED
    from backend.common.models.event import Event

    event = none_throws(Event.get_by_id("2026nao"))
    assert event.first_code is None
    assert event.official is False


def test_offseason_untouched_first_code_keeps_suggested_code(
    ndb_stub, taskqueue_stub
) -> None:
    user = make_user([AccountPermission.REVIEW_OFFSEASON_EVENTS])
    suggestion = Suggestion(
        id=80,
        author=ndb.Key(Account, "author"),
        target_model="offseason-event",
        review_state=SuggestionState.REVIEW_PENDING,
    )
    suggestion.contents = {
        "name": "Indiana Robotics Invitational",
        "start_date": "2026-07-16",
        "end_date": "2026-07-18",
        "first_code": "iri",
    }
    suggestion.put()

    outcome = SuggestionReviewer.accept_suggestion(
        "80", user, overrides={"event_short": "iri"}
    )

    assert outcome.result == SuggestionReviewResult.ACCEPTED
    from backend.common.models.event import Event

    event = none_throws(Event.get_by_id("2026iri"))
    assert event.first_code == "IRI"
    assert event.official is True


def test_offseason_event_type_defaults_from_the_suggestion(
    ndb_stub, taskqueue_stub
) -> None:
    from backend.common.consts.event_type import EventType
    from backend.common.models.event import Event

    user = make_user([AccountPermission.REVIEW_OFFSEASON_EVENTS])
    suggestion = Suggestion(
        id=81,
        author=ndb.Key(Account, "author"),
        target_model="offseason-event",
        review_state=SuggestionState.REVIEW_PENDING,
    )
    # A January event: the suggestion creator already marked it preseason
    suggestion.contents = {
        "name": "Week Zero",
        "start_date": "2026-01-10",
        "end_date": "2026-01-10",
        "event_type": EventType.PRESEASON,
    }
    suggestion.put()

    outcome = SuggestionReviewer.accept_suggestion(
        "81", user, overrides={"event_short": "wz"}
    )
    assert outcome.result == SuggestionReviewResult.ACCEPTED
    assert none_throws(Event.get_by_id("2026wz")).event_type_enum == EventType.PRESEASON

    # An explicit override still wins
    suggestion2 = Suggestion(
        id=82,
        author=ndb.Key(Account, "author"),
        target_model="offseason-event",
        review_state=SuggestionState.REVIEW_PENDING,
    )
    suggestion2.contents = {
        "name": "Week Zero",
        "start_date": "2026-01-10",
        "end_date": "2026-01-10",
        "event_type": EventType.PRESEASON,
    }
    suggestion2.put()
    outcome = SuggestionReviewer.accept_suggestion(
        "82",
        user,
        overrides={"event_short": "wz2", "event_type_enum": int(EventType.OFFSEASON)},
    )
    assert outcome.result == SuggestionReviewResult.ACCEPTED
    assert (
        none_throws(Event.get_by_id("2026wz2")).event_type_enum == EventType.OFFSEASON
    )


def _create_offseason_suggestion(suggestion_id: int = 90) -> Suggestion:
    suggestion = Suggestion(
        id=suggestion_id,
        author=ndb.Key(Account, "author"),
        target_model="offseason-event",
        review_state=SuggestionState.REVIEW_PENDING,
    )
    suggestion.contents = {
        "name": "Local Offseason",
        "start_date": "2026-07-16",
        "end_date": "2026-07-18",
    }
    suggestion.put()
    return suggestion


def _create_webcast_suggestion(event_key: str = "2026cc") -> Suggestion:
    suggestion = Suggestion(
        id=f"webcast_{event_key}_twitch_frcgamesense_None",
        author=ndb.Key(Account, "author"),
        target_model="event",
        target_key=event_key,
        review_state=SuggestionState.REVIEW_PENDING,
    )
    suggestion.contents = {
        "webcast_dict": {"type": WebcastType.TWITCH, "channel": "frcgamesense"},
        "webcast_url": "http://twitch.tv/frcgamesense",
        "webcast_date": None,
    }
    suggestion.put()
    return suggestion


def _create_apiwrite_suggestion(event_key: str = "2026cc") -> Suggestion:
    Account(id="author", email="author@example.com", display_name="Author").put()
    suggestion = Suggestion(
        id=91,
        author=ndb.Key(Account, "author"),
        target_model="api_auth_access",
        target_key=event_key,
        review_state=SuggestionState.REVIEW_PENDING,
    )
    suggestion.contents = {
        "event_key": event_key,
        "affiliation": "Event Organizer",
        "auth_types": [AuthType.MATCH_VIDEO],
    }
    suggestion.put()
    return suggestion


def test_accept_in_transaction_not_found_after_permission_check(ndb_stub) -> None:
    # The suggestion can vanish between the permission check and the
    # transaction (another reviewer deleting it); the transaction reports it
    user = make_user([], is_admin=True)
    outcome = SuggestionReviewer._accept_in_transaction(
        ndb.Key(Suggestion, "gone"), user, {}, ""
    )
    assert outcome == ReviewOutcome(SuggestionReviewResult.NOT_FOUND, "gone")


def test_accept_with_invalid_override_payload(ndb_stub, taskqueue_stub) -> None:
    user = make_user([AccountPermission.REVIEW_MEDIA])
    suggestion_id = _create_media_suggestion("frc1124")

    outcome = SuggestionReviewer.accept_suggestion(
        suggestion_id, user, overrides={"year": "not a year"}
    )

    assert outcome.result == SuggestionReviewResult.INVALID
    assert outcome.message is not None
    assert outcome.message.startswith("Invalid accept payload:")
    suggestion = none_throws(Suggestion.get_by_id(suggestion_id))
    assert suggestion.review_state == SuggestionState.REVIEW_PENDING
    assert Media.query().count() == 0


def test_reject_already_reviewed(ndb_stub, taskqueue_stub) -> None:
    user = make_user([AccountPermission.REVIEW_MEDIA])
    suggestion_id = _create_media_suggestion("frc1124")
    suggestion = none_throws(Suggestion.get_by_id(suggestion_id))
    suggestion.review_state = SuggestionState.REVIEW_ACCEPTED
    suggestion.put()

    outcomes = SuggestionReviewer.reject_suggestions([suggestion_id], user)

    assert outcomes == [
        ReviewOutcome(SuggestionReviewResult.ALREADY_REVIEWED, suggestion_id)
    ]
    assert none_throws(Suggestion.get_by_id(suggestion_id)).review_state == (
        SuggestionState.REVIEW_ACCEPTED
    )
    assert AuditLogEntry.query().count() == 0


def test_create_target_model_refuses_unknown_type(ndb_stub) -> None:
    # Every SuggestionType is handled today; a type added to the enum without
    # an accept path must be refused rather than silently accepted
    suggestion = _pending_suggestion("media", "frc254")
    with patch(
        "backend.common.suggestions.suggestion_reviewer.SuggestionType"
    ) as mock_type:
        mock_type.return_value = "newfangled"
        created_key, error = SuggestionReviewer._create_target_model(suggestion, {})
    assert created_key is None
    assert error == "Unsupported suggestion type newfangled"


def test_accept_media_replacing_missing_preferred_media(
    ndb_stub, taskqueue_stub
) -> None:
    user = make_user([AccountPermission.REVIEW_MEDIA])
    suggestion_id = _create_media_suggestion("frc1124")

    outcome = SuggestionReviewer.accept_suggestion(
        suggestion_id,
        user,
        overrides={"set_preferred": True, "replace_preferred_media_key": "imgur_nope"},
    )

    assert outcome.result == SuggestionReviewResult.INVALID
    assert outcome.message == "Media imgur_nope not found"
    assert Media.query().count() == 0


def test_accept_media_replacing_media_not_preferred_for_team(
    ndb_stub, taskqueue_stub
) -> None:
    user = make_user([AccountPermission.REVIEW_MEDIA])
    suggestion_id = _create_media_suggestion("frc1124")
    MediaManipulator.createOrUpdate(
        Media(
            id="imgur_other",
            foreign_key="other",
            media_type_enum=MediaType.IMGUR,
            year=2024,
            references=[ndb.Key(Team, "frc1124")],
            preferred_references=[ndb.Key(Team, "frc254")],
        )
    )

    outcome = SuggestionReviewer.accept_suggestion(
        suggestion_id,
        user,
        overrides={
            "set_preferred": True,
            "replace_preferred_media_key": "imgur_other",
        },
    )

    assert outcome.result == SuggestionReviewResult.INVALID
    assert outcome.message == "Media imgur_other is not preferred for this team"
    other = none_throws(Media.get_by_id("imgur_other"))
    assert other.preferred_references == [ndb.Key(Team, "frc254")]


def test_accept_webcast_invalid_type(ndb_stub, taskqueue_stub, event) -> None:
    user = make_user([AccountPermission.REVIEW_MEDIA])
    suggestion = _create_webcast_suggestion(event.key_name)

    outcome = SuggestionReviewer.accept_suggestion(
        str(none_throws(suggestion.key).id()),
        user,
        overrides={"webcast_type": "carrier_pigeon"},
    )

    assert outcome.result == SuggestionReviewResult.INVALID
    assert outcome.message == "Invalid webcast_type carrier_pigeon"
    assert not none_throws(Event.get_by_id(event.key_name)).webcast


def test_accept_webcast_with_file_and_date(ndb_stub, taskqueue_stub, event) -> None:
    user = make_user([AccountPermission.REVIEW_MEDIA])
    suggestion = _create_webcast_suggestion(event.key_name)

    with patch(
        "backend.common.suggestions.suggestion_reviewer.EventWebcastAdder.add_webcast"
    ) as mock_add_webcast:
        outcome = SuggestionReviewer.accept_suggestion(
            str(none_throws(suggestion.key).id()),
            user,
            overrides={
                "webcast_type": "youtube",
                "webcast_channel": "abc123",
                "webcast_file": "stream.m3u8",
                "webcast_date": "2026-09-26",
            },
        )

    assert outcome.result == SuggestionReviewResult.ACCEPTED
    assert outcome.created_target_key == event.key_name
    mock_add_webcast.assert_called_once()
    added_event, webcast = mock_add_webcast.call_args[0]
    assert added_event.key_name == event.key_name
    assert webcast == {
        "type": WebcastType.YOUTUBE,
        "channel": "abc123",
        "file": "stream.m3u8",
        "date": "2026-09-26",
    }


def test_accept_webcast_for_missing_event(ndb_stub, taskqueue_stub) -> None:
    user = make_user([AccountPermission.REVIEW_MEDIA])
    suggestion = _create_webcast_suggestion("2026gone")

    outcome = SuggestionReviewer.accept_suggestion(
        str(none_throws(suggestion.key).id()), user
    )

    assert outcome.result == SuggestionReviewResult.INVALID
    assert outcome.message == "Event 2026gone not found"


def test_accept_offseason_bad_event_key(ndb_stub, taskqueue_stub) -> None:
    user = make_user([AccountPermission.REVIEW_OFFSEASON_EVENTS])
    suggestion = _create_offseason_suggestion()

    outcome = SuggestionReviewer.accept_suggestion(
        str(none_throws(suggestion.key).id()),
        user,
        overrides={"event_short": "not a key"},
    )

    assert outcome.result == SuggestionReviewResult.INVALID
    assert outcome.message == "Bad event key 2026not a key"
    assert Event.query().count() == 0


def test_accept_offseason_event_already_exists(ndb_stub, taskqueue_stub, event) -> None:
    user = make_user([AccountPermission.REVIEW_OFFSEASON_EVENTS])
    suggestion = _create_offseason_suggestion()

    outcome = SuggestionReviewer.accept_suggestion(
        str(none_throws(suggestion.key).id()),
        user,
        overrides={"event_short": event.event_short},
    )

    assert outcome.result == SuggestionReviewResult.INVALID
    assert outcome.message == f"Event {event.key_name} already exists"
    assert none_throws(Event.get_by_id(event.key_name)).name == event.name


def test_reject_offseason_writes_no_audit_entry(ndb_stub, taskqueue_stub) -> None:
    # An offseason event has no target until it is accepted, so there is
    # nothing for the audit log to point at on a rejection
    user = make_user([AccountPermission.REVIEW_OFFSEASON_EVENTS])
    suggestion = _create_offseason_suggestion()

    outcomes = SuggestionReviewer.reject_suggestions(
        [str(none_throws(suggestion.key).id())], user
    )

    assert [o.result for o in outcomes] == [SuggestionReviewResult.REJECTED]
    assert none_throws(Suggestion.get_by_id(90)).review_state == (
        SuggestionState.REVIEW_REJECTED
    )
    assert AuditLogEntry.query().count() == 0


def test_accept_api_write_for_missing_event(ndb_stub, taskqueue_stub) -> None:
    user = make_user([AccountPermission.REVIEW_APIWRITE])
    suggestion = _create_apiwrite_suggestion("2026gone")

    outcome = SuggestionReviewer.accept_suggestion(
        str(none_throws(suggestion.key).id()), user
    )

    assert outcome.result == SuggestionReviewResult.INVALID
    assert outcome.message == "Event 2026gone not found"
    assert ApiAuthAccess.query().count() == 0


def test_accept_api_write_never_expiring(ndb_stub, taskqueue_stub, event) -> None:
    user = make_user([AccountPermission.REVIEW_APIWRITE])
    suggestion = _create_apiwrite_suggestion(event.key_name)

    outcome = SuggestionReviewer.accept_suggestion(
        str(none_throws(suggestion.key).id()),
        user,
        overrides={"expiration_days": -1},
    )

    assert outcome.result == SuggestionReviewResult.ACCEPTED
    auth = none_throws(ApiAuthAccess.get_by_id(none_throws(outcome.created_target_key)))
    assert auth.expiration is None
    assert auth.event_list == [ndb.Key(Event, event.key_name)]
    assert auth.auth_types_enum == [AuthType.MATCH_VIDEO]


def test_reject_in_transaction_not_found_after_permission_check(ndb_stub) -> None:
    user = make_user([], is_admin=True)
    outcome = SuggestionReviewer._reject_in_transaction(
        ndb.Key(Suggestion, "gone"), user, ""
    )
    assert outcome == ReviewOutcome(SuggestionReviewResult.NOT_FOUND, "gone")


def test_accept_already_reviewed(ndb_stub, taskqueue_stub) -> None:
    user = make_user([AccountPermission.REVIEW_MEDIA])
    suggestion_id = _create_media_suggestion("frc1124")
    suggestion = none_throws(Suggestion.get_by_id(suggestion_id))
    suggestion.review_state = SuggestionState.REVIEW_REJECTED
    suggestion.put()

    outcome = SuggestionReviewer.accept_suggestion(suggestion_id, user)

    assert outcome == ReviewOutcome(
        SuggestionReviewResult.ALREADY_REVIEWED, suggestion_id
    )
    assert Media.query().count() == 0


def _put_suggestion(
    target_model: str,
    contents: Dict[str, Any],
    target_key: Optional[str] = None,
    suggestion_id: str = "sugg",
) -> str:
    suggestion = Suggestion(
        id=suggestion_id,
        author=ndb.Key(Account, "author"),
        target_model=target_model,
        target_key=target_key,
        review_state=SuggestionState.REVIEW_PENDING,
    )
    suggestion.contents = cast(SuggestionDict, contents)
    suggestion.put()
    return suggestion_id


def test_accept_missing_suggestion(ndb_stub) -> None:
    user = make_user([], is_admin=True)
    outcome = SuggestionReviewer.accept_suggestion("nope", user)
    assert outcome == ReviewOutcome(SuggestionReviewResult.NOT_FOUND, "nope")


def test_reject_missing_suggestion(ndb_stub) -> None:
    user = make_user([], is_admin=True)
    outcomes = SuggestionReviewer.reject_suggestions(["nope"], user)
    assert outcomes == [ReviewOutcome(SuggestionReviewResult.NOT_FOUND, "nope")]


def test_accept_match_video(ndb_stub, taskqueue_stub) -> None:
    user = make_user([], is_admin=True)
    Match(
        id="2026cc_qm1",
        event=ndb.Key(Event, "2026cc"),
        year=2026,
        comp_level=CompLevel.QM,
        set_number=1,
        match_number=1,
        alliances_json=json.dumps(
            {
                "red": {"score": -1, "teams": ["frc1", "frc2", "frc3"]},
                "blue": {"score": -1, "teams": ["frc4", "frc5", "frc6"]},
            }
        ),
    ).put()
    suggestion_id = _put_suggestion(
        "match", {"youtube_videos": ["abc123"]}, target_key="2026cc_qm1"
    )

    outcome = SuggestionReviewer.accept_suggestion(suggestion_id, user)

    assert outcome.result == SuggestionReviewResult.ACCEPTED
    assert outcome.created_target_key == "2026cc_qm1"
    match = none_throws(Match.get_by_id("2026cc_qm1"))
    assert match.youtube_videos == ["abc123"]


def test_accept_match_video_redirected_to_missing_match(
    ndb_stub, taskqueue_stub
) -> None:
    user = make_user([], is_admin=True)
    suggestion_id = _put_suggestion(
        "match", {"youtube_videos": ["abc123"]}, target_key="2026cc_qm1"
    )

    outcome = SuggestionReviewer.accept_suggestion(
        suggestion_id, user, overrides={"target_match_key": "2026cc_qm9"}
    )

    assert outcome.result == SuggestionReviewResult.INVALID
    assert outcome.message == "Match 2026cc_qm9 not found"


def test_accept_social_media(ndb_stub, taskqueue_stub) -> None:
    user = make_user([], is_admin=True)
    suggestion_id = _put_suggestion(
        "social-media",
        {
            "reference_type": "team",
            "reference_key": "frc254",
            "media_type_enum": MediaType.TWITTER_PROFILE,
            "foreign_key": "team254",
            "is_social": True,
        },
        target_key="frc254",
    )

    outcome = SuggestionReviewer.accept_suggestion(suggestion_id, user)

    assert outcome.result == SuggestionReviewResult.ACCEPTED
    media = none_throws(Media.get_by_id(none_throws(outcome.created_target_key)))
    assert media.foreign_key == "team254"
    assert media.year is None
    assert media.references == [ndb.Key(Team, "frc254")]
    assert media.preferred_references == []


def test_accept_robot_cad(ndb_stub, taskqueue_stub) -> None:
    user = make_user([], is_admin=True)
    suggestion_id = _put_suggestion(
        "robot",
        {
            "reference_type": "team",
            "reference_key": "frc254",
            "media_type_enum": MediaType.GRABCAD,
            "foreign_key": "2026-robot",
            "year": "2026",
            "details_json": '{"model_name": "Robot"}',
        },
        target_key="frc254",
    )

    outcome = SuggestionReviewer.accept_suggestion(suggestion_id, user)

    assert outcome.result == SuggestionReviewResult.ACCEPTED
    media = none_throws(Media.get_by_id(none_throws(outcome.created_target_key)))
    assert media.year == 2026
    assert media.details_json == '{"model_name": "Robot"}'


def test_accept_event_media(ndb_stub, taskqueue_stub, event) -> None:
    user = make_user([], is_admin=True)
    suggestion_id = _put_suggestion(
        "event_media",
        {
            "reference_type": "event",
            "reference_key": event.key_name,
            "media_type_enum": MediaType.YOUTUBE_VIDEO,
            "foreign_key": "abc123",
            "year": 2026,
        },
        target_key=event.key_name,
    )

    outcome = SuggestionReviewer.accept_suggestion(suggestion_id, user)

    assert outcome.result == SuggestionReviewResult.ACCEPTED
    media = none_throws(Media.get_by_id(none_throws(outcome.created_target_key)))
    assert media.references == [ndb.Key(Event, event.key_name)]
    assert media.preferred_references == []


def test_accept_media_replacing_preferred_media(ndb_stub, taskqueue_stub) -> None:
    user = make_user([AccountPermission.REVIEW_MEDIA])
    suggestion_id = _create_media_suggestion("frc1124")
    MediaManipulator.createOrUpdate(
        Media(
            id="imgur_other",
            foreign_key="other",
            media_type_enum=MediaType.IMGUR,
            year=2024,
            references=[ndb.Key(Team, "frc1124")],
            preferred_references=[ndb.Key(Team, "frc1124")],
        )
    )

    outcome = SuggestionReviewer.accept_suggestion(
        suggestion_id,
        user,
        overrides={
            "set_preferred": True,
            "replace_preferred_media_key": "imgur_other",
        },
    )

    assert outcome.result == SuggestionReviewResult.ACCEPTED
    other = none_throws(Media.get_by_id("imgur_other"))
    assert other.preferred_references == []
    new_media = none_throws(Media.get_by_id(none_throws(outcome.created_target_key)))
    assert new_media.preferred_references == [ndb.Key(Team, "frc1124")]


def test_accept_webcast_without_channel(ndb_stub, taskqueue_stub, event) -> None:
    user = make_user([AccountPermission.REVIEW_MEDIA])
    suggestion_id = _put_suggestion(
        "event",
        {"webcast_url": "http://example.com/stream", "webcast_dict": None},
        target_key=event.key_name,
    )

    outcome = SuggestionReviewer.accept_suggestion(suggestion_id, user)

    assert outcome.result == SuggestionReviewResult.INVALID
    assert outcome.message == "webcast_type and webcast_channel are required"


def test_accept_offseason_without_event_short(ndb_stub, taskqueue_stub) -> None:
    user = make_user([AccountPermission.REVIEW_OFFSEASON_EVENTS])
    suggestion = _create_offseason_suggestion()

    outcome = SuggestionReviewer.accept_suggestion(
        str(none_throws(suggestion.key).id()), user
    )

    assert outcome.result == SuggestionReviewResult.INVALID
    assert outcome.message == "event_short is required to accept an offseason event"


def test_accept_offseason_without_dates(ndb_stub, taskqueue_stub) -> None:
    user = make_user([AccountPermission.REVIEW_OFFSEASON_EVENTS])
    suggestion = _create_offseason_suggestion()
    suggestion.contents = {"name": "Local Offseason"}
    suggestion.put()

    outcome = SuggestionReviewer.accept_suggestion(
        str(none_throws(suggestion.key).id()),
        user,
        overrides={"event_short": "LOCAL"},
    )

    assert outcome.result == SuggestionReviewResult.INVALID
    assert outcome.message == (
        "start_date and end_date are required to accept an offseason event"
    )
    assert Event.query().count() == 0
