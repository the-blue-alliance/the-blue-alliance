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
    headline = (
        "1 suggestion needs review"
        if total == 1
        else f"{total} suggestions need review"
    )
    # Slack posts are prod-only, where this resolves to the PWA's beta host
    bullets = [
        f"• {slack_link(PwaUrlHelper.suggestion_review_url(t), TYPE_NAMES[t])}: {count}"
        for t, count in pending
    ]
    OutgoingNotificationHelper.send_slack_alert(
        channel_url, "\n".join([f"*:inbox_tray: {headline}*"] + bullets)
    )
    return ""
