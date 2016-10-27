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
        sender = "suggestions@{}.appspotmail.com".format(app_identity.get_application_id())
        reply_to = "contact@thebluealliance.com"
        mail.send_mail(sender=sender,
                       reply_to=reply_to,
                       to="contact@thebluealliance.com",
                       subject=subject,
                       body=email_body)