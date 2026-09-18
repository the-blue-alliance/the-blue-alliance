from typing import List
from unittest.mock import Mock

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
from backend.common.models.user import User
from backend.common.suggestions.suggestion_creator import SuggestionCreator
from backend.common.suggestions.suggestion_reviewer import (
    SuggestionReviewer,
    SuggestionReviewResult,
    TEAM_ADMIN_REVIEWABLE_TYPES,
)


def _make_user(permissions: List[AccountPermission], is_admin: bool = False) -> User:
    account_key = Account(id="reviewer_uid", email="reviewer@tba.com").put()
    user = Mock(spec=User)
    user.is_admin = is_admin
    user.permissions = permissions
    user.account_key = account_key
    return user


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
    user = _make_user([AccountPermission.REVIEW_MEDIA])
    suggestion = _pending_suggestion("media", "frc254")
    assert SuggestionReviewer.user_can_review_suggestion(user, suggestion)


def test_admin_can_review_without_delegation(ndb_stub) -> None:
    user = _make_user([], is_admin=True)
    suggestion = _pending_suggestion("media", "frc254")
    assert SuggestionReviewer.user_can_review_suggestion(user, suggestion)


def test_no_permission_no_delegation_cannot_review(ndb_stub) -> None:
    user = _make_user([])
    suggestion = _pending_suggestion("media", "frc254")
    assert not SuggestionReviewer.user_can_review_suggestion(user, suggestion)


def test_delegated_team_admin_can_review_own_team(ndb_stub) -> None:
    user = _make_user([])
    for target_model in ("media", "social-media", "robot"):
        suggestion = _pending_suggestion(target_model, "frc254")
        assert SuggestionReviewer.user_can_review_suggestion(
            user, suggestion, delegated_team_keys={"frc254"}
        ), target_model


def test_delegated_team_admin_cannot_review_other_team(ndb_stub) -> None:
    user = _make_user([])
    suggestion = _pending_suggestion("media", "frc1678")
    assert not SuggestionReviewer.user_can_review_suggestion(
        user, suggestion, delegated_team_keys={"frc254"}
    )


def test_delegated_team_admin_cannot_review_non_team_types(ndb_stub) -> None:
    # Even if a suggestion's target key happens to match, delegation only
    # covers the team-targeted suggestion types
    user = _make_user([])
    for target_model in ("match", "event", "event_media", "offseason-event"):
        suggestion = _pending_suggestion(target_model, "frc254")
        assert not SuggestionReviewer.user_can_review_suggestion(
            user, suggestion, delegated_team_keys={"frc254"}
        ), target_model


def test_delegated_team_admin_cannot_review_suggestion_without_target(
    ndb_stub,
) -> None:
    user = _make_user([])
    suggestion = _pending_suggestion("media", None)  # pyre-ignore[6]
    assert not SuggestionReviewer.user_can_review_suggestion(
        user, suggestion, delegated_team_keys={"frc254"}
    )


def test_accept_with_delegation(ndb_stub, taskqueue_stub) -> None:
    user = _make_user([])
    suggestion_id = _create_media_suggestion("frc1124")

    outcome = SuggestionReviewer.accept_suggestion(
        suggestion_id,
        user,
        overrides={"set_preferred": True},
        endpoint="team_admin.team_mod_review",
        delegated_team_keys={"frc1124"},
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


def test_accept_forbidden_for_other_team(ndb_stub, taskqueue_stub) -> None:
    user = _make_user([])
    suggestion_id = _create_media_suggestion("frc1124")

    outcome = SuggestionReviewer.accept_suggestion(
        suggestion_id, user, delegated_team_keys={"frc254"}
    )

    assert outcome.result == SuggestionReviewResult.FORBIDDEN
    suggestion = none_throws(Suggestion.get_by_id(suggestion_id))
    assert suggestion.review_state == SuggestionState.REVIEW_PENDING
    assert Media.query().count() == 0


def test_reject_with_delegation(ndb_stub, taskqueue_stub) -> None:
    user = _make_user([])
    suggestion_id = _create_media_suggestion("frc1124")

    outcomes = SuggestionReviewer.reject_suggestions(
        [suggestion_id], user, delegated_team_keys={"frc1124"}
    )

    assert [o.result for o in outcomes] == [SuggestionReviewResult.REJECTED]
    suggestion = none_throws(Suggestion.get_by_id(suggestion_id))
    assert suggestion.review_state == SuggestionState.REVIEW_REJECTED
    assert Media.query().count() == 0


def test_reject_forbidden_for_other_team(ndb_stub, taskqueue_stub) -> None:
    user = _make_user([])
    suggestion_id = _create_media_suggestion("frc1124")

    outcomes = SuggestionReviewer.reject_suggestions(
        [suggestion_id], user, delegated_team_keys={"frc254"}
    )

    assert [o.result for o in outcomes] == [SuggestionReviewResult.FORBIDDEN]
    suggestion = none_throws(Suggestion.get_by_id(suggestion_id))
    assert suggestion.review_state == SuggestionState.REVIEW_PENDING
