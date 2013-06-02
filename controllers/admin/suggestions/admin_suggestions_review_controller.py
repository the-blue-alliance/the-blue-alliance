import os

from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from models.suggestion import Suggestion

class AdminSuggestionsReviewController(LoggedInHandler):
    """
    View the list of suggestions.
    """
    def get(self):
        self._require_admin()
        
        suggestions = Suggestion.query().filter(Suggestion.accepted == False)
        
        self.template_values.update({
            "suggestions": suggestions,
        })
        
        path = os.path.join(os.path.dirname(__file__), '../../../templates/admin/suggestion_list.html')
        self.response.out.write(template.render(path, self.template_values))
        