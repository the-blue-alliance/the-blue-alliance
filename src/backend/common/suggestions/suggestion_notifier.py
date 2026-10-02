import logging
from typing import Any, Callable, Optional, Tuple

from google.appengine.ext import ndb

from backend.common.consts.suggestion_type import SuggestionType
from backend.common.helpers.deferred import defer_safe
from backend.common.helpers.outgoing_notification_helper import (
    CONTACT_EMAIL,
    OutgoingNotificationHelper,
)
from backend.common.helpers.pwa_url_helper import PwaUrlHelper, WWW_BASE_URL
from backend.common.models.account import Account
from backend.common.models.event import Event
from backend.common.models.suggestion import Suggestion
from backend.common.sitevars.slack_hook_urls import SlackHookUrls

# Notifications run on the tasks service so the moderator's or submitter's
# request never waits on (or fails because of) mail and Slack. The queue
# retries failed sends with backoff (see src/queue.yaml), and each task sends
# exactly one thing so a retry never re-sends something that already worked.
TASKS_TARGET = "py3-tasks-io"
NOTIFICATIONS_QUEUE = "notifications"


class SuggestionNotifier:
    """
    Notifications for the suggestion lifecycle. Admins hear about new
    requests that need a human decision; suggesters hear what happened to
    the requests where the outcome matters to them (API keys, offseason
    events); moderators see API key verdicts in Slack.

    The public methods enqueue; the `_deliver_*` methods run in the task and
    do the lookups and sends. Enqueue failures are logged, never raised: the
    review or submission that triggered the notification has already
    happened and must not fail.
    """

    # ----- enqueue (called from request handlers and the reviewer) -----

    @classmethod
    def apiwrite_requested(cls, account_key: ndb.Key, event_key: str) -> None:
        cls._enqueue(cls._deliver_apiwrite_requested, account_key.id(), event_key)

    @classmethod
    def offseason_event_suggested(cls, event_name: str) -> None:
        cls._enqueue(cls._deliver_offseason_event_suggested, event_name)

    @classmethod
    def apiwrite_reviewed(
        cls,
        suggestion_key: str,
        accepted: bool,
        user_message: Optional[str],
        auth_id: Optional[str] = None,
    ) -> None:
        # Two tasks: the requester's email and the moderators' Slack post
        # succeed or retry independently of each other
        cls._enqueue(
            cls._deliver_apiwrite_verdict_email, suggestion_key, accepted, user_message
        )
        cls._enqueue(
            cls._deliver_apiwrite_verdict_slack,
            suggestion_key,
            accepted,
            user_message,
            auth_id,
        )

    @classmethod
    def offseason_event_accepted(cls, suggestion_key: str, event_key: str) -> None:
        cls._enqueue(cls._deliver_offseason_event_accepted, suggestion_key, event_key)

    @classmethod
    def _enqueue(cls, deliver: Callable[..., None], *args: Any) -> None:
        try:
            defer_safe(deliver, *args, _queue=NOTIFICATIONS_QUEUE, _target=TASKS_TARGET)
        except Exception:
            logging.exception(f"Failed to enqueue {deliver.__name__}{args}")

    # ----- deliver (runs on the tasks service) -----

    @classmethod
    def _deliver_apiwrite_requested(cls, account_id: str, event_key: str) -> None:
        account = Account.get_by_id(account_id)
        requester = cls._describe(account, fallback=account_id)
        OutgoingNotificationHelper.send_admin_alert_email(
            subject=f"Trusted API Key Request for {event_key}",
            email_body=(
                f"{requester} has made a request for trusted API keys for the "
                f"event {event_key}.\n\n"
                f"View the event at {WWW_BASE_URL}/event/{event_key}\n\n"
                "Review the request at "
                f"{PwaUrlHelper.suggestion_review_url(SuggestionType.API_AUTH_ACCESS)}\n"
            ),
        )

    @classmethod
    def _deliver_offseason_event_suggested(cls, event_name: str) -> None:
        OutgoingNotificationHelper.send_admin_alert_email(
            subject=f"New Offseason Event Suggestion: {event_name}",
            email_body=(
                "A new offseason event suggestion has been submitted with title: "
                f"{event_name}.\n\n"
                "Review the request at "
                f"{PwaUrlHelper.suggestion_review_url(SuggestionType.OFFSEASON_EVENT)}\n"
            ),
        )

    @classmethod
    def _deliver_apiwrite_verdict_email(
        cls, suggestion_key: str, accepted: bool, user_message: Optional[str]
    ) -> None:
        """Tell the requester whether their Trusted API key request was granted."""
        loaded = cls._apiwrite_suggestion_and_event(suggestion_key)
        if loaded is None:
            return
        suggestion, event_key, event = loaded
        author: Optional[Account] = suggestion.author.get()
        if author is None or not author.email or event is None:
            logging.warning(
                f"Not emailing apiwrite verdict for {suggestion_key}: "
                f"missing author email or event {event_key!r}"
            )
            return

        message = (user_message or "").strip()
        if accepted:
            verdict_text = (
                "We have accepted your request for auth tokens so you can add "
                f"data to the following event: {event.year} {event.name}\n\n"
                "You can find the keys on your account overview page: "
                f"{WWW_BASE_URL}/account\n"
            )
        else:
            verdict_text = (
                f"We have reviewed your request for auth tokens for {event.year} "
                f"{event.name} and have regretfully declined to issue keys.\n"
            )
        OutgoingNotificationHelper.send_suggestion_result_email(
            to=author.email,
            subject=f"The Blue Alliance Auth Tokens for {event_key}",
            email_body=(
                f"Hi {cls._display_name(author)},\n\n"
                f"{verdict_text}"
                + (f"\n{message}\n" if message else "")
                + "\nIf you have any questions, please don't hesitate to reach out "
                f"to us at {CONTACT_EMAIL}\n\n"
                "Thanks,\nTBA Admins\n"
            ),
        )

    @classmethod
    def _deliver_apiwrite_verdict_slack(
        cls,
        suggestion_key: str,
        accepted: bool,
        user_message: Optional[str],
        auth_id: Optional[str],
    ) -> None:
        """Tell the moderators' channel what was decided and by whom."""
        channel_url = SlackHookUrls.url_for("suggestion-nag")
        if not channel_url:
            return
        loaded = cls._apiwrite_suggestion_and_event(suggestion_key)
        if loaded is None:
            return
        suggestion, event_key, _ = loaded
        # The review already recorded who made the call
        reviewer_key: Optional[ndb.Key] = suggestion.reviewer
        reviewer: Optional[Account] = reviewer_key.get() if reviewer_key else None
        reviewer_id = str(reviewer_key.id()) if reviewer_key else "unknown"

        message = (user_message or "").strip()
        body = (
            f"*Trusted API Key Request for {event_key}*\n"
            f"{cls._describe(reviewer, fallback=reviewer_id)} has "
            f"{'accepted' if accepted else 'rejected'} the request"
            + (f" with the following message:\n{message}" if message else "")
        )
        if auth_id:
            body += f"\n<{WWW_BASE_URL}/admin/api_auth/edit/{auth_id}|View the key>"
        OutgoingNotificationHelper.send_slack_alert(channel_url, body)

    @classmethod
    def _deliver_offseason_event_accepted(
        cls, suggestion_key: str, event_key: str
    ) -> None:
        """Tell the suggester their offseason event is live and how to feed it data."""
        suggestion = Suggestion.get_by_key_string(suggestion_key)
        if suggestion is None:
            logging.warning(f"No suggestion {suggestion_key} to notify about")
            return
        author, event = ndb.get_multi([suggestion.author, ndb.Key(Event, event_key)])
        if author is None or not author.email or event is None:
            logging.warning(
                f"Not emailing offseason approval for {suggestion_key}: "
                f"missing author email or event {event_key!r}"
            )
            return
        OutgoingNotificationHelper.send_suggestion_result_email(
            to=author.email,
            subject=f"[TBA] Offseason Event Suggestion: {event.name}",
            email_body=(
                f"Hi {cls._display_name(author)},\n\n"
                "Thank you for suggesting an offseason event to The Blue Alliance. "
                "Your suggestion has been approved and you can find the event at "
                f"{WWW_BASE_URL}/event/{event_key}\n\n"
                "If you are the event's organizer and would like to upload teams "
                "attending, match videos, or real-time match results to TBA before "
                "or during the event, you can do so using the TBA EventWizard. "
                f"Request auth keys here: {WWW_BASE_URL}/request/apiwrite\n\n"
                "Thanks for helping make TBA better,\nThe Blue Alliance Admins\n"
            ),
        )

    # ----- helpers -----

    @classmethod
    def _apiwrite_suggestion_and_event(
        cls, suggestion_key: str
    ) -> Optional[Tuple[Suggestion, str, Optional[Event]]]:
        """The apiwrite suggestion, the event key it asked about, and the Event."""
        suggestion = Suggestion.get_by_key_string(suggestion_key)
        if suggestion is None or suggestion.target_model != "api_auth_access":
            logging.warning(f"No apiwrite suggestion {suggestion_key} to notify about")
            return None
        event_key = suggestion.target_key or suggestion.contents.get("event_key") or ""
        if not event_key:
            logging.warning(f"Apiwrite suggestion {suggestion_key} names no event")
            return None
        return suggestion, event_key, Event.get_by_id(event_key)

    @staticmethod
    def _display_name(account: Account, fallback: str = "there") -> str:
        """What to call someone: display name, else nickname, else `fallback`."""
        return account.display_name or account.nickname or fallback

    @classmethod
    def _describe(cls, account: Optional[Account], fallback: str) -> str:
        """'Name (email)' for an account, degrading to whatever we know."""
        if account is None:
            return f"account {fallback}"
        name = cls._display_name(account, fallback=f"account {fallback}")
        return f"{name} ({account.email})" if account.email else name
