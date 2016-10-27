from controllers.base_controller import LoggedInHandler
from helpers.suggestions.suggestion_creator import SuggestionCreator
from helpers.suggestions.suggestion_notifier import SuggestionNotifier
from template_engine import jinja2_engine


class SuggestOffseasonEventController(LoggedInHandler):
    """
    Allow users to suggest Offseason Events
    """

    def get(self):
        self._require_registration()
        self.template_values.update({
            "status": self.request.get("status"),
        })
        self.response.out.write(
            jinja2_engine.render('suggest_offseason_event.html', self.template_values))

    def post(self):
        self._require_registration()

        event_name = self.request.get("name", None)
        status, failures = SuggestionCreator.createOffseasonEventSuggestion(
            author_account_key=self.user_bundle.account.key,
            name=event_name,
            start_date=self.request.get("start_date", None),
            end_date=self.request.get("end_date", None),
            website=self.request.get("website", None),
            venue_name=self.request.get("venue_name", None),
            address=self.request.get("venue_address", None),
            city=self.request.get("venue_city", None),
            state=self.request.get("venue_state", None),
            country=self.request.get("venue_country", None)
        )
        if status != 'success':
            # Don't completely wipe form data if validation fails
            self.template_values.update({
                'status': status,
                'failures': failures,
                'name': self.request.get('name', None),
                'start_date': self.request.get('start_date', None),
                'end_date': self.request.get('end_date', None),
                'website': self.request.get('website', None),
                'venue_address': self.request.get('venue_address', None),
            })
            self.response.out.write(
                jinja2_engine.render('suggest_offseason_event.html', self.template_values))
        else:
            subject, body = self._gen_notification_email(event_name)
            SuggestionNotifier.send_admin_alert_email(subject, body)
            self.redirect('/suggest/offseason?status=%s' % status)

    @staticmethod
    def _gen_notification_email(event_name):
        subject = "New Offseason Event Suggestion: {}".format(event_name)
        body = """A new offseason event suggestion has been submitted with title: {}.

Review the request at https://thebluealliance.com/suggest/offseason/review
""".format(event_name)
        return subject, body
