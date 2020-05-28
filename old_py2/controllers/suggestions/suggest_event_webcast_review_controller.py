import datetime
import os
import logging

from google.appengine.ext import deferred
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from consts.account_permissions import AccountPermissions
from controllers.suggestions.suggestions_review_base_controller import SuggestionsReviewBaseController
from helpers.event.event_webcast_adder import EventWebcastAdder
from helpers.memcache.memcache_webcast_flusher import MemcacheWebcastFlusher

from models.event import Event
from models.suggestion import Suggestion


class SuggestEventWebcastReviewController(SuggestionsReviewBaseController):
    REQUIRED_PERMISSIONS = [AccountPermissions.REVIEW_MEDIA]

    def __init__(self, *args, **kw):
        super(SuggestEventWebcastReviewController, self).__init__(*args, **kw)

    def create_target_model(self, suggestion):
        webcast = dict()
        webcast["type"] = self.request.get("webcast_type")
        webcast["channel"] = self.request.get("webcast_channel")
        if self.request.get("webcast_file"):
            webcast["file"] = self.request.get("webcast_file")
        if self.request.get('webcast_date'):
            webcast['date'] = self.request.get('webcast_date')

        event = Event.get_by_id(self.request.get("event_key"))
        # Defer because of transactions
        deferred.defer(EventWebcastAdder.add_webcast, event, webcast)
        deferred.defer(MemcacheWebcastFlusher.flush)
        return True

    """
    View the list of suggestions.
    """
    def get(self):
        suggestions = Suggestion.query().filter(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
            Suggestion.target_model == "event")

        suggestions_by_event_key = {}
        for suggestion in suggestions:
            if 'webcast_dict' in suggestion.contents:
                suggestion.webcast_template = 'webcast/{}.html'.format(suggestion.contents['webcast_dict']['type'])
            suggestions_by_event_key.setdefault(suggestion.target_key, []).append(suggestion)

        suggestion_sets = []
        for event_key, suggestions in suggestions_by_event_key.items():
            suggestion_sets.append({
                "event": Event.get_by_id(event_key),
                "suggestions": suggestions
                })

        self.template_values.update({
            "event_key": self.request.get("event_key"),
            "success": self.request.get("success"),
            "suggestion_sets": suggestion_sets
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/suggest_event_webcast_review_list.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        event_key = self.request.get("event_key")
        if self.request.get("verdict") == "accept":
            suggestion_key = self.request.get("suggestion_key")
            suggestion_key = int(suggestion_key) if suggestion_key.isdigit() else suggestion_key
            self._process_accepted(suggestion_key)
            self.redirect("/suggest/event/webcast/review?success=accept&event_key=%s" % event_key)
            return

        elif self.request.get("verdict") == "reject":
            suggestion_key = self.request.get("suggestion_key")
            suggestion_key = int(suggestion_key) if suggestion_key.isdigit() else suggestion_key
            self._process_rejected(suggestion_key)
            self.redirect("/suggest/event/webcast/review?success=reject")
            return

        elif self.request.get("verdict") == "reject_all":
            suggestion_keys = self.request.get("suggestion_keys").split(",")
            suggestion_keys = [int(suggestion_key) if suggestion_key.isdigit() else suggestion_key for suggestion_key in suggestion_keys]
            self._process_rejected(suggestion_keys)
            self.redirect("/suggest/event/webcast/review?success=reject_all&event_key=%s" % event_key)
            return

        self.redirect("/suggest/event/webcast/review")
