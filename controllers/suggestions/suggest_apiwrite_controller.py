from consts.auth_type import AuthType
from controllers.base_controller import LoggedInHandler
from controllers.suggestions.suggestions_base_controller import SuggestionsBaseController
from helpers.suggestions.suggestion_creator import SuggestionCreator
from template_engine import jinja2_engine


class SuggestApiWriteController(SuggestionsBaseController):
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

        auth_types = self.request.get_all("auth_types", [])
        clean_auth_types = filter(lambda a: int(a) in AuthType.type_names.keys(), auth_types)
        event_key = self.request.get("event_key", None)
        status = SuggestionCreator.createApiWriteSuggestion(
            author_account_key=self.user_bundle.account.key,
            event_key=event_key,
            affiliation=self.request.get("role", None),
            auth_types=clean_auth_types,
        )
        subject, body = self._gen_notification_email(event_key)
        self.send_admin_alert_email(subject, body)
        self.template_values.update({
            'status': status,
            "auth_types": AuthType.type_names,
        })
        self.response.out.write(
            jinja2_engine.render('suggest_apiwrite.html', self.template_values))

    @staticmethod
    def _gen_notification_email(event_key):
        subject = "Trusted API Key Request for {}".format(event_key)
        body = """A new request has been made for trusted API keys for the event {}.

View the event at https://thebluealliance.com/event/{}

Review the request at https://thebluealliance.com/suggest/apiwrite/review
""".format(event_key, event_key)
        return subject, body
