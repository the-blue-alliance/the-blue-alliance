from google.appengine.api import mail
from google.appengine.api.app_identity import app_identity

import tba_config
from controllers.base_controller import LoggedInHandler


class SuggestionsReviewBaseController(LoggedInHandler):
    """
    Base controller for reviewing suggestions.
    """

    REQUIRED_PERMISSIONS = []

    def __init__(self, *args, **kw):
        super(SuggestionsReviewBaseController, self).__init__(*args, **kw)
        self.verify_permissions()

    def verify_permissions(self):
        for permission in self.REQUIRED_PERMISSIONS:
            self._require_permission(permission)


class SuggestionsBaseController(LoggedInHandler):
    """
    Base controller for submitting suggestions
    """

    def send_admin_alert_email(self, subject, email_body):
        # Send an email to contact@ telling them to review this
        # Only do this on prod
        if tba_config.DEBUG:
            return
        sender = "keys@{}.appspotmail.com".format(app_identity.get_application_id())
        reply_to = "contact@thebluealliance.com"
        mail.send_mail(sender=sender,
                       reply_to=reply_to,
                       to="contact@thebluealliance.com",
                       subject=subject,
                       body=email_body)

