import datetime
import os
import logging

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from helpers.event.event_webcast_adder import EventWebcastAdder

from models.event import Event
from models.suggestion import Suggestion


class AdminEventWebcastSuggestionsReviewController(LoggedInHandler):
    """
    View the list of suggestions.
    """
    def get(self):
        self._require_admin()

        suggestions = Suggestion.query().filter(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
            Suggestion.target_model == "event")

        self.template_values.update({
            "event_key": self.request.get("event_key"),
            "success": self.request.get("success"),
            "suggestions": suggestions,
        })

        path = os.path.join(os.path.dirname(__file__), '../../../templates/admin/event_webcast_suggestion_list.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_admin()

        webcast = dict()
        webcast["type"] = self.request.get("webcast_type")
        webcast["channel"] = self.request.get("webcast_channel")
        if self.request.get("webcast_file"):
            webcast["file"] = self.request.get("webcast_file")

        event = Event.get_by_id(self.request.get("event_key"))
        suggestion = Suggestion.get_by_id(int(self.request.get("suggestion_key")))

        EventWebcastAdder.add_webcast(event, webcast)

        suggestion.review_state = Suggestion.REVIEW_ACCEPTED
        suggestion.reviewer = self.user_bundle.account.key
        suggestion.reviewer_at = datetime.datetime.now()
        suggestion.put()

        # TODO: Allow rejecting suggestions -gregmarra 20130921

        self.redirect("/admin/suggestions/event/webcast/review?success=1&event_key=%s" % event.key.id())
