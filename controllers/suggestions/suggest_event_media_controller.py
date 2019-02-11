import json

from controllers.base_controller import LoggedInHandler
from database.media_query import EventMediasQuery
from helpers.media_helper import MediaHelper
from helpers.suggestions.suggestion_creator import SuggestionCreator
from helpers.outgoing_notification_helper import OutgoingNotificationHelper
from models.event import Event
from models.sitevar import Sitevar
from template_engine import jinja2_engine


class SuggestEventMediaController(LoggedInHandler):
    """
    Allow users to suggest a playlist of YouTube videos for matches
    """
    def get(self):
        self._require_registration()

        if not self.request.get("event_key"):
            self.redirect("/", abort=True)

        event_future = Event.get_by_id_async(self.request.get("event_key"))
        event = event_future.get_result()

        if not event:
            self.abort(404)

        medias_future = EventMediasQuery(event.key_name).fetch_async()
        medias = medias_future.get_result()
        medias_by_slugname = MediaHelper.group_by_slugname(medias)

        self.template_values.update({
            "status": self.request.get("status"),
            "medias_by_slugname": medias_by_slugname,
            "event": event,
        })

        self.response.out.write(jinja2_engine.render('suggestions/suggest_event_media.html', self.template_values))

    def post(self):
        self._require_registration()

        event_key = self.request.get("event_key")

        status, suggestion = SuggestionCreator.createEventMediaSuggestion(
            author_account_key=self.user_bundle.account.key,
            media_url=self.request.get("media_url"),
            event_key=event_key)

        if status == 'success':
            # Send an update to the FUN slack
            slack_sitevar = Sitevar.get_or_insert('slack.hookurls')
            if slack_sitevar:
                slack_url = slack_sitevar.contents.get('fun', '')
                if slack_url:
                    message_body = u"{0} ({1}) has suggested a video for <https://www.thebluealliance.com/event/{2}|{2}>: https://youtu.be/{3}.\nSee all suggestions at https://www.thebluealliance.com/suggest/event/media/review".format(
                        self.user_bundle.account.display_name,
                        self.user_bundle.account.email,
                        event_key,
                        suggestion.contents['foreign_key']).encode('utf-8')

                    OutgoingNotificationHelper.send_slack_alert(slack_url, message_body, [])

        self.redirect('/suggest/event/media?event_key=%s&status=%s' % (event_key, status))
