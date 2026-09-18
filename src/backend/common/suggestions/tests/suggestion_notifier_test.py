from typing import Optional

import pytest
from google.appengine.ext import ndb

from backend.common.consts.auth_type import AuthType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.account import Account
from backend.common.models.event import Event
from backend.common.models.suggestion import Suggestion
from backend.common.sitevars.slack_hook_urls import SlackHookUrls
from backend.common.suggestions.suggestion_notifier import SuggestionNotifier


def _apiwrite_suggestion(
    author: Account,
    event_key: Optional[str] = "2026cc",
    suggestion_id: int = 1,
    reviewer_id: Optional[str] = "reviewer_uid",
) -> str:
    suggestion = Suggestion(
        id=suggestion_id,
        author=author.key,
        target_model="api_auth_access",
        target_key=event_key,
        review_state=SuggestionState.REVIEW_ACCEPTED,
        # The review records who made the call; the Slack line reads it back
        reviewer=ndb.Key(Account, reviewer_id) if reviewer_id else None,
    )
    suggestion.contents = {
        "event_key": event_key or "",
        "affiliation": "Team 254",
        "auth_types": [AuthType.MATCH_VIDEO],
    }
    suggestion.put()
    return str(suggestion.key.id())


def _offseason_suggestion(author: Account) -> str:
    suggestion = Suggestion(
        id=2,
        author=author.key,
        target_model="offseason-event",
        review_state=SuggestionState.REVIEW_ACCEPTED,
    )
    suggestion.contents = {"name": "Chezy Champs"}
    suggestion.put()
    return str(suggestion.key.id())


# ---------------------------------------------------------------------------
# Enqueue: the public methods hand off to the notifications queue
# ---------------------------------------------------------------------------


def test_apiwrite_reviewed_enqueues_email_and_slack_separately(
    author: Account,
    reviewer: Account,
    event: Event,
    taskqueue_stub,
    run_deferred_tasks,
    sent_result_emails,
    sent_slack_alerts,
) -> None:
    suggestion_key = _apiwrite_suggestion(author)

    SuggestionNotifier.apiwrite_reviewed(
        suggestion_key, accepted=True, user_message="Enjoy!", auth_id="authid123"
    )

    tasks = taskqueue_stub.get_filtered_tasks(queue_names="notifications")
    assert len(tasks) == 2
    assert all(t.url == "/_ah/queue/deferred_encoded" for t in tasks)
    assert taskqueue_stub.get_filtered_tasks(queue_names="default") == []
    # Nothing sends on the request path
    assert sent_result_emails == [] and sent_slack_alerts == []

    assert run_deferred_tasks() == 2
    assert [to for to, _, _ in sent_result_emails] == ["author@example.com"]
    assert len(sent_slack_alerts) == 1


def test_slack_failure_does_not_block_the_email(
    author: Account,
    reviewer: Account,
    event: Event,
    taskqueue_stub,
    run_deferred_tasks,
    sent_result_emails,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.common.helpers.outgoing_notification_helper import (
        OutgoingNotificationHelper,
    )

    monkeypatch.setattr(
        SlackHookUrls, "url_for", staticmethod(lambda channel: "http://hook")
    )

    def slack_down(*args, **kwargs):
        raise RuntimeError("Slack is down")

    monkeypatch.setattr(OutgoingNotificationHelper, "send_slack_alert", slack_down)
    suggestion_key = _apiwrite_suggestion(author)

    SuggestionNotifier.apiwrite_reviewed(
        suggestion_key, accepted=True, user_message=None
    )

    # The email task is independent of the Slack task; run whichever comes
    # first and keep going past the failure
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="notifications")
    assert len(tasks) == 2
    failures = 0
    for task in tasks:
        from backend.common.helpers.deferred import run_from_task

        try:
            run_from_task(task)
        except RuntimeError:
            failures += 1
    assert failures == 1
    assert len(sent_result_emails) == 1


def test_admin_alerts_run_as_deferred_tasks(
    author: Account, taskqueue_stub, run_deferred_tasks, sent_admin_alerts
) -> None:
    SuggestionNotifier.apiwrite_requested(author.key, "2026cc")
    SuggestionNotifier.offseason_event_suggested("Chezy Champs")

    assert sent_admin_alerts == []
    assert run_deferred_tasks() == 2
    assert [subject for subject, _ in sent_admin_alerts] == [
        "Trusted API Key Request for 2026cc",
        "New Offseason Event Suggestion: Chezy Champs",
    ]


def test_enqueue_failure_never_raises(
    author: Account, taskqueue_stub, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(*args, **kwargs):
        raise RuntimeError("task queue is down")

    monkeypatch.setattr(
        "backend.common.suggestions.suggestion_notifier.defer_safe", boom
    )

    # The review or submission that triggered these has already happened
    SuggestionNotifier.apiwrite_requested(author.key, "2026cc")
    SuggestionNotifier.offseason_event_suggested("x")
    SuggestionNotifier.apiwrite_reviewed("1", True, None)
    SuggestionNotifier.offseason_event_accepted("2", "2026cc")


# ---------------------------------------------------------------------------
# Deliver: what actually gets sent
# ---------------------------------------------------------------------------


def test_apiwrite_requested_alerts_admins(author: Account, sent_admin_alerts) -> None:
    SuggestionNotifier._deliver_apiwrite_requested("author_uid", "2026cc")

    assert len(sent_admin_alerts) == 1
    subject, body = sent_admin_alerts[0]
    assert subject == "Trusted API Key Request for 2026cc"
    assert "Alice Author (author@example.com)" in body
    assert "https://www.thebluealliance.com/event/2026cc" in body
    assert "https://beta.thebluealliance.com/suggest/review/api_auth_access" in body


def test_apiwrite_requested_degrades_without_names(ndb_stub, sent_admin_alerts) -> None:
    Account(id="anon_uid", email="anon@example.com", registered=True).put()

    SuggestionNotifier._deliver_apiwrite_requested("anon_uid", "2026cc")
    SuggestionNotifier._deliver_apiwrite_requested("missing_uid", "2026cc")

    assert "account anon_uid (anon@example.com) has made" in sent_admin_alerts[0][1]
    assert "account missing_uid has made" in sent_admin_alerts[1][1]
    assert "None" not in sent_admin_alerts[0][1] + sent_admin_alerts[1][1]


def test_offseason_event_suggested_alerts_admins(sent_admin_alerts) -> None:
    SuggestionNotifier._deliver_offseason_event_suggested("Chezy Champs")

    assert len(sent_admin_alerts) == 1
    subject, body = sent_admin_alerts[0]
    assert subject == "New Offseason Event Suggestion: Chezy Champs"
    assert "Chezy Champs" in body
    assert "https://beta.thebluealliance.com/suggest/review/offseason-event" in body


def test_apiwrite_accepted_email(
    author: Account, event: Event, sent_result_emails
) -> None:
    suggestion_key = _apiwrite_suggestion(author)

    SuggestionNotifier._deliver_apiwrite_verdict_email(
        suggestion_key, True, "Enjoy the keys!"
    )

    assert len(sent_result_emails) == 1
    to, subject, body = sent_result_emails[0]
    assert to == "author@example.com"
    assert subject == "The Blue Alliance Auth Tokens for 2026cc"
    assert body.startswith("Hi Alice Author,")
    assert "accepted your request" in body
    assert "2026 Chezy Champs" in body
    assert "https://www.thebluealliance.com/account" in body
    assert "Enjoy the keys!" in body
    assert "contact@thebluealliance.com" in body


def test_apiwrite_rejected_email_carries_the_reason(
    author: Account, event: Event, sent_result_emails
) -> None:
    suggestion_key = _apiwrite_suggestion(author)

    SuggestionNotifier._deliver_apiwrite_verdict_email(
        suggestion_key, False, "Please ask your mentor."
    )

    to, subject, body = sent_result_emails[0]
    assert to == "author@example.com"
    assert subject == "The Blue Alliance Auth Tokens for 2026cc"
    assert "regretfully declined" in body
    assert "Please ask your mentor." in body
    assert "/account" not in body


def test_apiwrite_email_without_message(
    author: Account, event: Event, sent_result_emails
) -> None:
    suggestion_key = _apiwrite_suggestion(author)

    SuggestionNotifier._deliver_apiwrite_verdict_email(suggestion_key, True, None)

    _, _, body = sent_result_emails[0]
    assert "None" not in body
    assert "accepted your request" in body


def test_apiwrite_email_skips_when_author_has_no_email(
    ndb_stub, event: Event, sent_result_emails
) -> None:
    account = Account(id="no_email", registered=True)
    account.put()
    suggestion_key = _apiwrite_suggestion(account)

    SuggestionNotifier._deliver_apiwrite_verdict_email(suggestion_key, True, None)

    assert sent_result_emails == []


def test_apiwrite_email_skips_when_event_missing(
    author: Account, sent_result_emails
) -> None:
    suggestion_key = _apiwrite_suggestion(author, event_key="2026nope")

    SuggestionNotifier._deliver_apiwrite_verdict_email(suggestion_key, True, None)

    assert sent_result_emails == []


def test_apiwrite_email_skips_when_no_event_named(
    author: Account, sent_result_emails, sent_slack_alerts
) -> None:
    # A hand-edited suggestion with no event: degrade, don't crash the task
    suggestion_key = _apiwrite_suggestion(author, event_key=None)

    SuggestionNotifier._deliver_apiwrite_verdict_email(suggestion_key, True, None)
    SuggestionNotifier._deliver_apiwrite_verdict_slack(suggestion_key, True, None, None)

    assert sent_result_emails == []
    assert sent_slack_alerts == []


def test_apiwrite_notifications_ignore_other_suggestion_types(
    author: Account, event: Event, sent_result_emails, sent_slack_alerts
) -> None:
    Suggestion(
        id="media_1",
        author=author.key,
        target_model="media",
        target_key="frc254",
        review_state=SuggestionState.REVIEW_PENDING,
    ).put()

    for key in ("media_1", "does-not-exist"):
        SuggestionNotifier._deliver_apiwrite_verdict_email(key, True, None)
        SuggestionNotifier._deliver_apiwrite_verdict_slack(key, True, None, None)

    assert sent_result_emails == []
    assert sent_slack_alerts == []


def test_apiwrite_slack_alert_names_reviewer_message_and_key(
    author: Account, reviewer: Account, event: Event, sent_slack_alerts
) -> None:
    suggestion_key = _apiwrite_suggestion(author)

    SuggestionNotifier._deliver_apiwrite_verdict_slack(
        suggestion_key, True, "Enjoy the keys!", "authid123"
    )

    assert len(sent_slack_alerts) == 1
    url, body = sent_slack_alerts[0]
    assert url == "http://hook"
    assert "*Trusted API Key Request for 2026cc*" in body
    assert "Mod Erator (mod@tba.com) has accepted the request" in body
    assert "with the following message:\nEnjoy the keys!" in body
    assert "/admin/api_auth/edit/authid123|View the key" in body


def test_apiwrite_slack_alert_for_rejection(
    author: Account, reviewer: Account, event: Event, sent_slack_alerts
) -> None:
    suggestion_key = _apiwrite_suggestion(author)

    SuggestionNotifier._deliver_apiwrite_verdict_slack(
        suggestion_key, False, "Please ask your mentor.", None
    )

    _, body = sent_slack_alerts[0]
    assert "has rejected the request with the following message:\nPlease ask" in body
    assert "View the key" not in body


def test_apiwrite_slack_alert_without_message_or_reviewer(
    author: Account, event: Event, sent_slack_alerts
) -> None:
    suggestion_key = _apiwrite_suggestion(author, reviewer_id=None)

    SuggestionNotifier._deliver_apiwrite_verdict_slack(suggestion_key, True, None, None)

    _, body = sent_slack_alerts[0]
    assert body.split("\n")[1] == "account unknown has accepted the request"


def test_apiwrite_slack_alert_skipped_without_a_hook(
    author: Account, reviewer: Account, event: Event, monkeypatch: pytest.MonkeyPatch
) -> None:
    from backend.common.helpers.outgoing_notification_helper import (
        OutgoingNotificationHelper,
    )

    monkeypatch.setattr(SlackHookUrls, "url_for", staticmethod(lambda channel: None))
    monkeypatch.setattr(
        OutgoingNotificationHelper,
        "send_slack_alert",
        classmethod(lambda cls, *a, **k: pytest.fail("unexpected Slack post")),
    )
    suggestion_key = _apiwrite_suggestion(author)

    SuggestionNotifier._deliver_apiwrite_verdict_slack(
        suggestion_key, True, None, "authid123"
    )


def test_offseason_event_accepted_emails_suggester(
    author: Account, event: Event, sent_result_emails
) -> None:
    suggestion_key = _offseason_suggestion(author)

    SuggestionNotifier._deliver_offseason_event_accepted(suggestion_key, "2026cc")

    assert len(sent_result_emails) == 1
    to, subject, body = sent_result_emails[0]
    assert to == "author@example.com"
    assert subject == "[TBA] Offseason Event Suggestion: Chezy Champs"
    assert body.startswith("Hi Alice Author,")
    assert "https://www.thebluealliance.com/event/2026cc" in body
    assert "https://www.thebluealliance.com/request/apiwrite" in body


def test_offseason_event_accepted_skips_when_event_missing(
    author: Account, sent_result_emails
) -> None:
    suggestion_key = _offseason_suggestion(author)

    SuggestionNotifier._deliver_offseason_event_accepted(suggestion_key, "2026nope")
    SuggestionNotifier._deliver_offseason_event_accepted("999", "2026cc")

    assert sent_result_emails == []


def test_display_name_falls_back_to_nickname(ndb_stub) -> None:
    assert (
        SuggestionNotifier._display_name(
            Account(id="a", nickname="nick", email="a@example.com")
        )
        == "nick"
    )
    assert (
        SuggestionNotifier._display_name(Account(id="a", email="a@example.com"))
        == "there"
    )
