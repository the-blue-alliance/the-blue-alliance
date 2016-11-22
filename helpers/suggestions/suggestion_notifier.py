from google.appengine.api import mail
from google.appengine.api.app_identity import app_identity

import tba_config


class SuggestionNotifier(object):

    @classmethod
    def send_admin_alert_email(cls, subject, email_body):
        # Send an email to contact@ telling them to review this
        # Only do this on prod
        if tba_config.DEBUG:
            return
        mail.send_mail(sender="The Blue Alliance Contact <contact@thebluealliance.com>",
                       to="contact@thebluealliance.com",
                       subject=subject,
                       body=email_body)
