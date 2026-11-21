import pytest

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.auth_type import AuthType
from backend.common.consts.media_type import MediaType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.account import Account
from backend.common.models.audit_log_entry import AuditLogEntry
from backend.common.models.event import Event
from backend.common.models.suggestion import Suggestion
from backend.common.suggestions.suggestion_notifier import SuggestionNotifier
from backend.common.suggestions.suggestion_reviewer import (
    SuggestionReviewer,
    SuggestionReviewResult,
)
from backend.common.suggestions.tests.conftest import make_user


@pytest.fixture
def notifier_calls(monkeypatch: pytest.MonkeyPatch):
    """Records (method name, args, kwargs) for every notifier enqueue."""
    calls = []
    for name in ("apiwrite_reviewed", "offseason_event_accepted"):
        monkeypatch.setattr(
            SuggestionNotifier,
            name,
            classmethod(lambda cls, *a, _name=name, **k: calls.append((_name, a, k))),
        )
    return calls


def _apiwrite_suggestion(author: Account) -> str:
    suggestion = Suggestion(
        id=11,
        author=author.key,
        target_model="api_auth_access",
        target_key="2026cc",
        review_state=SuggestionState.REVIEW_PENDING,
    )
    suggestion.contents = {
        "event_key": "2026cc",
        "affiliation": "Team 254",
        "auth_types": [AuthType.MATCH_VIDEO],
    }
    suggestion.put()
    return "11"


def _offseason_suggestion(author: Account) -> str:
    suggestion = Suggestion(
        id=12,
        author=author.key,
        target_model="offseason-event",
        review_state=SuggestionState.REVIEW_PENDING,
    )
    suggestion.contents = {
        "name": "Rumble Offseason",
        "start_date": "2026-10-03",
        "end_date": "2026-10-04",
        "website": "https://example.com",
        "venue_name": "Gym",
        "address": "1 Main St",
        "city": "Townsville",
        "state": "MA",
        "country": "USA",
    }
    suggestion.put()
    return "12"


def _media_suggestion(author: Account) -> str:
    suggestion = Suggestion(
        id="media_1",
        author=author.key,
        target_model="media",
        target_key="frc254",
        review_state=SuggestionState.REVIEW_PENDING,
    )
    suggestion.contents = {
        "year": 2026,
        "reference_type": "team",
        "reference_key": "frc254",
        "media_type_enum": MediaType.YOUTUBE_VIDEO,
        "foreign_key": "abc123",
        "details_json": "{}",
        "private_details_json": "{}",
        "is_social": False,
    }
    suggestion.put()
    return "media_1"


def test_accept_apiwrite_notifies_with_message_and_key(
    author: Account, event: Event, taskqueue_stub, notifier_calls
) -> None:
    suggestion_id = _apiwrite_suggestion(author)

    outcome = SuggestionReviewer.accept_suggestion(
        suggestion_id,
        make_user([AccountPermission.REVIEW_APIWRITE]),
        overrides={"user_message": "Enjoy!"},
    )

    assert outcome.result == SuggestionReviewResult.ACCEPTED
    assert notifier_calls == [
        (
            "apiwrite_reviewed",
            ("11",),
            {
                "accepted": True,
                "user_message": "Enjoy!",
                "auth_id": outcome.created_target_key,
            },
        )
    ]


def test_reject_apiwrite_notifies_and_audits_the_message(
    author: Account, event: Event, notifier_calls
) -> None:
    suggestion_id = _apiwrite_suggestion(author)

    outcomes = SuggestionReviewer.reject_suggestions(
        [suggestion_id],
        make_user([AccountPermission.REVIEW_APIWRITE]),
        user_message="Not for this event.",
    )

    assert [o.result for o in outcomes] == [SuggestionReviewResult.REJECTED]
    assert notifier_calls == [
        (
            "apiwrite_reviewed",
            ("11",),
            {"accepted": False, "user_message": "Not for this event.", "auth_id": None},
        )
    ]
    # What the requester was told is part of the audit trail
    entries = AuditLogEntry.query().fetch()
    assert len(entries) == 1
    assert entries[0].form_params == {"user_message": ["Not for this event."]}


def test_reject_without_message_audits_nothing_extra(
    author: Account, event: Event, notifier_calls
) -> None:
    suggestion_id = _apiwrite_suggestion(author)

    SuggestionReviewer.reject_suggestions(
        [suggestion_id], make_user([AccountPermission.REVIEW_APIWRITE])
    )

    entries = AuditLogEntry.query().fetch()
    assert entries[0].form_params == {}
    assert notifier_calls[0][2]["user_message"] is None


def test_accept_offseason_notifies_with_created_event(
    author: Account, taskqueue_stub, notifier_calls
) -> None:
    suggestion_id = _offseason_suggestion(author)

    outcome = SuggestionReviewer.accept_suggestion(
        suggestion_id,
        make_user([AccountPermission.REVIEW_OFFSEASON_EVENTS]),
        overrides={"event_short": "rumble"},
    )

    assert outcome.result == SuggestionReviewResult.ACCEPTED
    assert outcome.created_target_key == "2026rumble"
    assert notifier_calls == [("offseason_event_accepted", ("12", "2026rumble"), {})]


def test_media_review_sends_nothing(
    author: Account, taskqueue_stub, notifier_calls
) -> None:
    accepted_id = _media_suggestion(author)
    outcome = SuggestionReviewer.accept_suggestion(
        accepted_id, make_user([AccountPermission.REVIEW_MEDIA])
    )
    assert outcome.result == SuggestionReviewResult.ACCEPTED

    Suggestion(
        id="media_2",
        author=author.key,
        target_model="media",
        target_key="frc254",
        review_state=SuggestionState.REVIEW_PENDING,
    ).put()
    outcomes = SuggestionReviewer.reject_suggestions(
        ["media_2"], make_user([AccountPermission.REVIEW_MEDIA]), user_message="x"
    )
    assert [o.result for o in outcomes] == [SuggestionReviewResult.REJECTED]

    assert notifier_calls == []
    # Nobody was told anything, so the audit trail records no message
    reject_entries = [
        e
        for e in AuditLogEntry.query().fetch()
        if e.url_args.get("suggestion_key") == "media_2"
    ]
    assert len(reject_entries) == 1
    assert reject_entries[0].form_params == {}


def test_forbidden_or_already_reviewed_sends_nothing(
    author: Account, event: Event, taskqueue_stub, notifier_calls
) -> None:
    suggestion_id = _apiwrite_suggestion(author)

    forbidden = SuggestionReviewer.accept_suggestion(suggestion_id, make_user([]))
    assert forbidden.result == SuggestionReviewResult.FORBIDDEN

    suggestion = Suggestion.get_by_id(int(suggestion_id))
    assert suggestion is not None
    suggestion.review_state = SuggestionState.REVIEW_REJECTED
    suggestion.put()
    stale = SuggestionReviewer.accept_suggestion(
        suggestion_id, make_user([AccountPermission.REVIEW_APIWRITE])
    )
    assert stale.result == SuggestionReviewResult.ALREADY_REVIEWED
    stale_reject = SuggestionReviewer.reject_suggestions(
        [suggestion_id], make_user([AccountPermission.REVIEW_APIWRITE])
    )
    assert stale_reject[0].result == SuggestionReviewResult.ALREADY_REVIEWED

    assert notifier_calls == []
