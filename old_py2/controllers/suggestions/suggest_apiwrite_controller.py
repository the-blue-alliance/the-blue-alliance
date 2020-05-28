from consts.auth_type import AuthType
from controllers.base_controller import LoggedInHandler
from helpers.suggestions.suggestion_creator import SuggestionCreator
from helpers.outgoing_notification_helper import OutgoingNotificationHelper
from template_engine import jinja2_engine


class SuggestApiWriteController(LoggedInHandler):
    """
    Allow users to request trusted API keys for an offseason event
    """

    def get(self):
        self._require_login()
        self.template_values.update({
            "status": self.request.get("status"),
            "auth_types": AuthType.write_type_names,
        })
        self.response.out.write(
            jinja2_engine.render('suggestions/suggest_apiwrite.html', self.template_values))

    def post(self):
        self._require_login()

        auth_types = self.request.get_all("auth_types", [])
        clean_auth_types = filter(lambda a: int(a) in AuthType.write_type_names.keys(), auth_types)
        event_key = self.request.get("event_key", None)
        status = SuggestionCreator.createApiWriteSuggestion(
            author_account_key=self.user_bundle.account.key,
            event_key=event_key,
            affiliation=self.request.get("role", None),
            auth_types=clean_auth_types,
        )
        if status == 'success':
            subject, body = self._gen_notification_email(event_key, self.user_bundle)
            OutgoingNotificationHelper.send_admin_alert_email(subject, body)
        self.redirect('/request/apiwrite?status={}'.format(status), abort=True)

    @staticmethod
    def _gen_notification_email(event_key, user_bundle):
        # Subject should match the one in suggest_apiwrite_review_controller
        subject = "Trusted API Key Request for {}".format(event_key)
        body = u"""{} ({}) has made a request for trusted API keys for the event {}.

View the event at https://www.thebluealliance.com/event/{}

Review the request at https://www.thebluealliance.com/suggest/apiwrite/review
""".format(user_bundle.account.display_name, user_bundle.account.email, event_key, event_key).encode('utf-8')
        return subject, body
