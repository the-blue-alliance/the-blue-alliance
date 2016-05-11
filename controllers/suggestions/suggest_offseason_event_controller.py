from controllers.base_controller import LoggedInHandler
from helpers.suggestions.suggestion_creator import SuggestionCreator
from template_engine import jinja2_engine


class SuggestOffseasonEventController(LoggedInHandler):
    """
    Allow users to suggest Offseason Events
    """

    def get(self):
        self.template_values.update({
            "status": self.request.get("status"),
        })
        self.response.out.write(
            jinja2_engine.render('suggest_offseason_event.html', self.template_values))

    def post(self):
        self._require_login()

        status = SuggestionCreator.createOffseasonEventSuggestion(
            author_account_key=self.user_bundle.account.key,
            name=self.request.get("name", None),
            start_date=self.request.get("start_date", None),
            end_date=self.request.get("end_date", None),
            website=self.request.get("website", None),
            address=self.request.get("venue_address", None),
        )
        self.redirect('/suggest/offseason?status=%s' % status)
