from flask import Blueprint

from backend.common.consts.suggestion_state import SuggestionState
from backend.common.consts.suggestion_type import (
    SUGGESTION_TYPES,
    TYPE_NAMES as SUGGESTION_NAMES,
)
from backend.common.helpers.outgoing_notification_helper import (
    OutgoingNotificationHelper,
)
from backend.common.helpers.suggestion_fetcher import SuggestionFetcher
from backend.common.sitevars.slack_hook_urls import SlackHookUrls

blueprint = Blueprint("cron_misc", __name__)


@blueprint.route("/tasks/do/nag_suggestions")
def nag_pending_suggestions() -> str:
    channel_url = SlackHookUrls.url_for("suggestion-nag")
    if not channel_url:
        return ""

    counts = map(
        lambda t: SuggestionFetcher.count_async(SuggestionState.REVIEW_PENDING, t),
        SUGGESTION_TYPES,
    )

    nag_text = "There are pending suggestions!\n"
    suggestions_to_nag = False
    for count_future, name in zip(counts, SUGGESTION_TYPES):
        count = count_future.get_result()
        if count > 0:
            suggestions_to_nag = True
            nag_text += "*{0}*: {1} pending suggestions\n".format(
                SUGGESTION_NAMES.get(name), count
            )

    if suggestions_to_nag:
        nag_text += (
            "_Review them on <https://www.thebluealliance.com/suggest/review|TBA>_"
        )
        OutgoingNotificationHelper.send_slack_alert(channel_url, nag_text)

    return ""
