import os

from controllers.base_controller import LoggedInHandler
from helpers.suggestions.suggestion_creator import SuggestionCreator
from models.event import Event
from models.suggestion import Suggestion
from template_engine import jinja2_engine


class SuggestEventWebcastController(LoggedInHandler):
    """
    Allow users to suggest webcasts for TBA to add to events.
    """

    def get(self):
        self._require_registration()

        if not self.request.get("event_key"):
            self.redirect("/", abort=True)

        event = Event.get_by_id(self.request.get("event_key"))

        self.template_values.update({
            "status": self.request.get("status"),
            "event": event,
        })

        self.response.out.write(jinja2_engine.render('suggestions/suggest_event_webcast.html', self.template_values))

    def post(self):
        self._require_registration()

        event_key = self.request.get("event_key")
        webcast_url = self.request.get("webcast_url")
        webcast_date = self.request.get("webcast_date")

        if not webcast_url:
            self.redirect('/suggest/event/webcast?event_key={}&status=blank_webcast'.format(event_key), abort=True)

        if ' ' in webcast_url:
            # This is an invalid url
            self.redirect('/suggest/event/webcast?event_key={}&status=invalid_url'.format(event_key), abort=True)

        if 'thebluealliance' in webcast_url:
            # TBA doesn't host webcasts, so we can reject this outright
            self.redirect('/suggest/event/webcast?event_key={}&status=invalid_url'.format(event_key), abort=True)

        status = SuggestionCreator.createEventWebcastSuggestion(
            author_account_key=self.user_bundle.account.key,
            webcast_url=self.request.get("webcast_url"),
            webcast_date=self.request.get("webcast_date"),
            event_key=event_key)

        self.redirect('/suggest/event/webcast?event_key={}&status={}'.format(event_key, status))
