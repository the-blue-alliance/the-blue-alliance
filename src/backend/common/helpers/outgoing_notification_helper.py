import logging
from typing import Any, Dict, List, Optional

import requests

from backend.common.environment import Environment


class OutgoingNotificationHelper(object):
    """
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
    """

    @classmethod
    def send_slack_alert(
        cls, webhook_url: str, body_text: str, attachment_list: Optional[List] = None
    ) -> None:
        if not Environment.is_prod():
            return
        post_dict: Dict[str, Any] = {
            "text": body_text,
        }
        if attachment_list:
            post_dict.update(
                {
                    "attachments": attachment_list,
                }
            )

        response = requests.post(webhook_url, json=post_dict)
        response.raise_for_status()
        logging.info("Response from slack webhook {}".format(response.text))
