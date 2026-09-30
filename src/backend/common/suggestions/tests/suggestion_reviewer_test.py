import datetime

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.consts.suggestion_type import SuggestionType
from backend.common.models.account import Account
from backend.common.models.audit_log_entry import AuditLogEntry
from backend.common.models.media import Media
from backend.common.models.suggestion import Suggestion
from backend.common.models.team import Team
from backend.common.models.team_admin_access import TeamAdminAccess
from backend.common.models.user import User
from backend.common.suggestions.suggestion_creator import SuggestionCreator
from backend.common.suggestions.suggestion_reviewer import (
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
