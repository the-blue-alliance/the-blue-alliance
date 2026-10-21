from flask import Blueprint

from backend.common.consts.suggestion_state import SuggestionState
from backend.common.consts.suggestion_type import SuggestionType, TYPE_NAMES
from backend.common.helpers.outgoing_notification_helper import (
    OutgoingNotificationHelper,
    slack_link,
)
from backend.common.helpers.pwa_url_helper import PwaUrlHelper
from backend.common.helpers.suggestion_fetcher import SuggestionFetcher
from backend.common.sitevars.slack_hook_urls import SlackHookUrls

blueprint = Blueprint("cron_misc", __name__)


@blueprint.route("/tasks/do/nag_suggestions")
def nag_pending_suggestions() -> str:
    channel_url = SlackHookUrls.url_for("suggestion-nag")
    if not channel_url:
        return ""

    futures = [
        (t, SuggestionFetcher.count_async(SuggestionState.REVIEW_PENDING, t.value))
        for t in SuggestionType
    ]
    pending = [(t, f.get_result()) for t, f in futures]
    # Biggest backlog first; sorted() is stable, so ties keep enum order
    pending = sorted(
        [(t, count) for t, count in pending if count > 0],
        key=lambda tc: tc[1],
        reverse=True,
    )
    if not pending:
        return ""

    total = sum(count for _, count in pending)
    # Slack posts are prod-only, where these resolve to the PWA's beta host.
    # The review home links every queue plus the media and offseason tools.
    review_home = PwaUrlHelper.suggestion_review_url()
    headline = (
        f"1 suggestion {slack_link(review_home, 'needs review')}"
        if total == 1
        else f"{total} suggestions {slack_link(review_home, 'need review')}"
    )
    bullets = [
        f"• {count} {slack_link(PwaUrlHelper.suggestion_review_url(t), TYPE_NAMES[t])}"
        for t, count in pending
    ]
    OutgoingNotificationHelper.send_slack_alert(
        channel_url, "\n".join([f"*:inbox_tray: {headline}*"] + bullets)
    )
    return ""
