import json
import logging

from google.appengine.api import mail

import tba_config


class OutgoingNotificationHelper(object):

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

    @classmethod
    def send_suggestion_result_email(cls, to, subject, email_body):
        # Send an alert to the user who submitted a suggestion updating them on the status
        if tba_config.DEBUG:
            return
        mail.send_mail(sender="The Blue Alliance Admin <contact@thebluealliance.com>",
                       to=to,
                       cc="contact@thebluealliance.com",
                       subject=subject,
                       body=email_body)

    @classmethod
    def send_slack_alert(cls, webhook_url, body_text, attachment_list=None):
        # Send an alert to a specified slack channel
        # Only do this on prod
        import urllib
        import urllib2

        if tba_config.DEBUG or not webhook_url:
            return

        post_dict = {
            'text': body_text,
        }
        if attachment_list:
            post_dict.update({
                'attachments': attachment_list,
            })

        post_data = urllib.urlencode({"payload": json.dumps(post_dict)})
        request = urllib2.Request(webhook_url, post_data)
        response = urllib2.urlopen(request)
        logging.info("Response from slack webhook {}".format(response.read()))
