import logging
from typing import Any, Dict, List, Optional

import requests
from google.appengine.api import mail

from backend.common.environment import Environment

CONTACT_EMAIL = "contact@thebluealliance.com"
CONTACT_SENDER = f"The Blue Alliance Contact <{CONTACT_EMAIL}>"
ADMIN_SENDER = f"The Blue Alliance Admin <{CONTACT_EMAIL}>"


class OutgoingNotificationHelper(object):
    @classmethod
    def email_enabled(cls) -> bool:
        """
        Email reaches end users, so unlike Slack it is gated on the production
        project itself, not on "any App Engine deploy": a contributor's own GAE
        project seeded with prod data must never email real requesters.
        """
        return Environment.is_prod_project()

    @classmethod
    def send_admin_alert_email(cls, subject: str, email_body: str) -> None:
        """Email contact@ so the admins know something needs attention."""
        cls._send_mail(
            sender=CONTACT_SENDER, to=CONTACT_EMAIL, subject=subject, body=email_body
        )

    @classmethod
    def send_suggestion_result_email(
        cls, to: str, subject: str, email_body: str
    ) -> None:
        """
        Tell the person who submitted a suggestion what happened to it.
        contact@ is cc'd so the admins keep a record of what was sent.
        """
        cls._send_mail(
            sender=ADMIN_SENDER,
            to=to,
            subject=subject,
            body=email_body,
            cc=CONTACT_EMAIL,
        )

    @classmethod
    def _send_mail(
        cls,
        sender: str,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
    ) -> None:
        """
        Raises on failure. Callers run inside tasks on the `notifications`
        queue, so an exception means the send is retried rather than lost.
        """
        if not cls.email_enabled():
            logging.info(f"Skipping email outside prod: {subject!r} -> {to}")
            return
        kwargs: Dict[str, Any] = dict(sender=sender, to=to, subject=subject, body=body)
        if cc:
            kwargs["cc"] = cc
        mail.send_mail(**kwargs)

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
