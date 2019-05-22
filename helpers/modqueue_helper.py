from helpers.outgoing_notification_helper import OutgoingNotificationHelper
from helpers.suggestions.suggestion_fetcher import SuggestionFetcher

from models.sitevar import Sitevar
from models.suggestion import Suggestion


class ModQueueHelper(object):

    @classmethod
    def nag_mods(cls):
        hook_sitevars = Sitevar.get_by_id('slack.hookurls')
        if not hook_sitevars:
            return
        channel_url = hook_sitevars.contents.get('suggestion-nag')
        if not channel_url:
            return
        counts = map(lambda t: SuggestionFetcher.count(Suggestion.REVIEW_PENDING, t),
                     Suggestion.MODELS)

        nag_text = "There are pending suggestions!\n"
        suggestions_to_nag = False
        for count, name in zip(counts, Suggestion.MODELS):
            if count > 0:
                suggestions_to_nag = True
                nag_text += "*{0}*: {1} pending suggestions\n".format(
                    Suggestion.MODEL_NAMES.get(name),
                    count
                )

        if suggestions_to_nag:
            nag_text += "_Review them on <https://www.thebluealliance.com/suggest/review|TBA>_"
            OutgoingNotificationHelper.send_slack_alert(channel_url, nag_text)
