import os

from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from models.event import Event
from models.suggestion import Suggestion


class SuggestEventWebcastController(LoggedInHandler):
    """
    Allow users to suggest webcasts for TBA to add to events.
    """

    def get(self):
        self._require_login("/suggest/event/webcast?event=%s" % self.request.get("event_key"))

        if not self.request.get("event_key"):
            self.redirect("/", abort=True)

        event = Event.get_by_id(self.request.get("event_key"))

        self.template_values.update({
            "result": self.request.get("result"),
            "event": event,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/suggest_event_webcast.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_login()

        event_key = self.request.get("event_key")
        webcast_url = self.request.get("webcast_url")

        if not webcast_url:
            self.redirect('/suggest/event/webcast?event_key=%s&result=blank_webcast' % event_key, abort=True)

        suggestion = Suggestion(
            author=self.user_bundle.account.key,
            target_key=event_key,
            target_model="event",
            )
        suggestion.contents = {"webcast_url": webcast_url}
        suggestion.put()

        self.redirect('/suggest/event/webcast?event_key=%s&result=success' % event_key)
