import logging

from consts.auth_type import AuthType
from controllers.base_controller import LoggedInHandler
from helpers.suggestions.suggestion_creator import SuggestionCreator
from template_engine import jinja2_engine


class SuggestApiWriteController(LoggedInHandler):
    """
    Allow users to request trusted API keys for an offseason event
    """

    def get(self):
        self._require_login()
        self.template_values.update({
            "status": self.request.get("status"),
            "auth_types": AuthType.type_names,
        })
        self.response.out.write(
            jinja2_engine.render('suggest_apiwrite.html', self.template_values))

    def post(self):
        self._require_login()

        status = SuggestionCreator.createApiWriteSuggestion(
            author_account_key=self.user_bundle.account.key,
            event_key=self.request.get("event_key", None),
            affiliation=self.request.get("role", None),
            auth_types=self.request.get_all("auth_types", [])
        )
        self.template_values.update({
            'status': status,
            "auth_types": AuthType.type_names,
        })
        self.response.out.write(
            jinja2_engine.render('suggest_apiwrite.html', self.template_values))
