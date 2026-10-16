import re
from pathlib import Path
from typing import List, Optional, Tuple

import pytest
from google.appengine.ext import ndb

from backend.common.consts.auth_type import AuthType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.account import Account
from backend.common.models.event import Event
from backend.common.models.suggestion import Suggestion
from backend.common.sitevars.slack_hook_urls import SlackHookUrls
from backend.common.suggestions.suggestion_notifier import (
    PWA_DEFAULT_USER_MESSAGE,
    SuggestionNotifier,
    USER_EMAIL_FOOTER,
)


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
        "[TBA] Needs review: 2026cc API write keys",
        '[TBA] Needs review: offseason event "Chezy Champs"',
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
    assert subject == "[TBA] Needs review: 2026cc API write keys"
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
    assert subject == '[TBA] Needs review: offseason event "Chezy Champs"'
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
    assert subject == "[TBA] Approved: 2026cc API write keys (2026 Chezy Champs)"
    assert body.startswith("Hi Alice Author,")
    assert "accepted your request" in body
    assert "2026 Chezy Champs (2026cc)" in body
    assert (
        "What you can do next:\n"
        "1. Sign in to The Blue Alliance as author@example.com and open "
        "EventWizard: https://www.thebluealliance.com/eventwizard\n"
        "2. Choose 2026 Chezy Champs (2026cc) from the Select Event list."
    ) in body
    assert "\n3. Use EventWizard's tabs to upload" in body
    assert (
        "\n4. Your key ID and secret are listed on your account page, for "
        "tools other than EventWizard: "
        "https://www.thebluealliance.com/account#api-write-keys-row\n"
    ) in body
    assert "Note from the reviewer:\nEnjoy the keys!" in body
    assert "/request/apiwrite" not in body
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
    assert subject == "[TBA] Declined: 2026cc API write keys (2026 Chezy Champs)"
    assert "regretfully declined" in body
    assert "Reason from the reviewer:\nPlease ask your mentor." in body
    assert "Note from the reviewer" not in body
    assert (
        "What you can do next:\n"
        "1. If something in your request was wrong (such as the event key or "
        "your role), submit a new request: "
        "https://www.thebluealliance.com/request/apiwrite\n"
        "2. If you are not sure what to change, email "
        "contact@thebluealliance.com with the details of your request.\n"
    ) in body
    assert "/account" not in body
    assert "/eventwizard" not in body


def test_apiwrite_rejected_email_drops_the_pwa_default_message(
    author: Account, event: Event, sent_result_emails
) -> None:
    suggestion_key = _apiwrite_suggestion(author)

    SuggestionNotifier._deliver_apiwrite_verdict_email(
        suggestion_key, False, f" {PWA_DEFAULT_USER_MESSAGE} "
    )

    _, _, body = sent_result_emails[0]
    assert PWA_DEFAULT_USER_MESSAGE not in body
    assert "from the reviewer" not in body
    assert "/request/apiwrite" in body


def test_apiwrite_accepted_email_keeps_the_pwa_default_message(
    author: Account, event: Event, sent_result_emails
) -> None:
    suggestion_key = _apiwrite_suggestion(author)

    SuggestionNotifier._deliver_apiwrite_verdict_email(
        suggestion_key, True, PWA_DEFAULT_USER_MESSAGE
    )

    _, _, body = sent_result_emails[0]
    assert f"Note from the reviewer:\n{PWA_DEFAULT_USER_MESSAGE}" in body


def test_pwa_default_message_matches_the_pwa() -> None:
    repo_root = Path(__file__).resolve().parents[5]
    moderation_utils = repo_root / "pwa" / "app" / "lib" / "moderationUtils.ts"
    if not moderation_utils.exists():
        pytest.skip("PWA sources not checked out")
    assert (
        f"DEFAULT_USER_MESSAGE = '{PWA_DEFAULT_USER_MESSAGE}'"
        in moderation_utils.read_text()
    )


def test_apiwrite_email_without_message(
    author: Account, event: Event, sent_result_emails
) -> None:
    suggestion_key = _apiwrite_suggestion(author)

    SuggestionNotifier._deliver_apiwrite_verdict_email(suggestion_key, True, None)

    _, _, body = sent_result_emails[0]
    assert "None" not in body
    assert "accepted your request" in body
    assert "Note from the reviewer" not in body


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
    assert subject == "[TBA] Approved: 2026cc offseason event (2026 Chezy Champs)"
    assert body.startswith("Hi Alice Author,")
    assert "https://www.thebluealliance.com/event/2026cc" in body
    assert "https://www.thebluealliance.com/request/apiwrite" in body
    assert "https://www.thebluealliance.com/eventwizard" in body
    assert "/account" not in body


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


# ---------------------------------------------------------------------------
# Shared format: every email reads the same way
# ---------------------------------------------------------------------------


def _send_every_email(
    author: Account,
    sent_admin_alerts: List[Tuple[str, str]],
    sent_result_emails: List[Tuple[str, str, str]],
) -> Tuple[List[str], List[str], List[str]]:
    """Deliver each email once; return (subjects, admin bodies, user bodies)."""
    apiwrite_key = _apiwrite_suggestion(author)
    SuggestionNotifier._deliver_apiwrite_requested("author_uid", "2026cc")
    SuggestionNotifier._deliver_offseason_event_suggested("Chezy Champs")
    SuggestionNotifier._deliver_apiwrite_verdict_email(apiwrite_key, True, "Hi")
    SuggestionNotifier._deliver_apiwrite_verdict_email(apiwrite_key, False, None)
    SuggestionNotifier._deliver_offseason_event_accepted(
        _offseason_suggestion(author), "2026cc"
    )
    subjects = [s for s, _ in sent_admin_alerts] + [s for _, s, _ in sent_result_emails]
    return (
        subjects,
        [b for _, b in sent_admin_alerts],
        [b for _, _, b in sent_result_emails],
    )


def test_every_subject_leads_with_the_outcome_then_the_event(
    author: Account, event: Event, sent_admin_alerts, sent_result_emails
) -> None:
    subjects, _, _ = _send_every_email(author, sent_admin_alerts, sent_result_emails)

    assert len(subjects) == 5
    for subject in subjects:
        assert re.match(
            r"^\[TBA\] (Approved|Declined|Needs review): ", subject
        ), subject
    # Once an event exists, its key comes right after the outcome
    assert [s for s in subjects if "2026cc" in s] == [
        "[TBA] Needs review: 2026cc API write keys",
        "[TBA] Approved: 2026cc API write keys (2026 Chezy Champs)",
        "[TBA] Declined: 2026cc API write keys (2026 Chezy Champs)",
        "[TBA] Approved: 2026cc offseason event (2026 Chezy Champs)",
    ]


def test_every_email_calls_the_feature_api_write_keys(
    author: Account, event: Event, sent_admin_alerts, sent_result_emails
) -> None:
    subjects, admin_bodies, user_bodies = _send_every_email(
        author, sent_admin_alerts, sent_result_emails
    )

    text = "\n".join(subjects + admin_bodies + user_bodies).lower()
    for old_name in ("auth token", "trusted api key", "auth keys"):
        assert old_name not in text
    assert "api write keys" in text


def test_user_emails_share_the_footer(
    author: Account, event: Event, sent_admin_alerts, sent_result_emails
) -> None:
    _, _, user_bodies = _send_every_email(author, sent_admin_alerts, sent_result_emails)

    assert len(user_bodies) == 3
    for body in user_bodies:
        assert body.startswith("Hi Alice Author,\n\n")
        assert body.endswith(USER_EMAIL_FOOTER)
    assert "contact@thebluealliance.com" in USER_EMAIL_FOOTER


def test_offseason_accepted_email_numbers_its_next_steps(
    author: Account, event: Event, sent_result_emails
) -> None:
    SuggestionNotifier._deliver_offseason_event_accepted(
        _offseason_suggestion(author), "2026cc"
    )

    _, _, body = sent_result_emails[0]
    assert (
        "What you can do next:\n"
        "1. See the event: https://www.thebluealliance.com/event/2026cc\n"
        "2. If you organize this event and want to post teams, the schedule, "
        "or live results: request API write keys for 2026cc at "
        "https://www.thebluealliance.com/request/apiwrite\n"
        "3. Once a moderator approves them, upload data with EventWizard: "
        "https://www.thebluealliance.com/eventwizard\n"
    ) in body
