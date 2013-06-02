import datetime
import os
import logging

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from models.suggestion import Suggestion

class AdminSuggestionsReviewController(LoggedInHandler):
    """
    View the list of suggestions.
    """
    def get(self):
        self._require_admin()
        
        suggestions = Suggestion.query().filter(Suggestion.review_state == Suggestion.REVIEW_PENDING)

        self.template_values.update({
            "suggestions": suggestions,
        })
        
        path = os.path.join(os.path.dirname(__file__), '../../../templates/admin/suggestion_list.html')
        self.response.out.write(template.render(path, self.template_values))
        
    def post(self):
        self._require_admin()

        accept_keys = map(int, self.request.POST.getall("accept_keys[]"))
        reject_keys = map(int, self.request.POST.getall("reject_keys[]"))

        all_keys = accept_keys
        all_keys.extend(reject_keys)

        suggestions = map(lambda a: a.get_result(),
            [Suggestion.get_by_id_async(key) for key in accept_keys])
        
        # TODO: Mutate data using SuggestionAccepter objects

        for suggestion in suggestions:
            if suggestion.key.id() in accept_keys:
                suggestion.review_state = Suggestion.REVIEW_ACCEPTED
            if suggestion.key.id() in reject_keys:
                suggestion.review_state = Suggestion.REVIEW_REJECTED
            suggestion.reviewer = self.user_bundle.account.key
            suggestion.reviewer_at = datetime.datetime.now()
            logging.info(suggestion)

        ndb.put_multi(suggestions)

        self.redirect("/admin/suggestions/review")
