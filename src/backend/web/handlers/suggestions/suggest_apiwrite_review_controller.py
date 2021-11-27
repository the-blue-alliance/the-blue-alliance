import random
import string
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

from flask import redirect, request
from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.wrappers import Response

from backend.common.auth import current_user
from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.auth_type import AuthType, WRITE_TYPE_NAMES
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.account import Account
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.models.keys import EventKey
from backend.common.models.suggestion import Suggestion
from backend.web.handlers.suggestions.suggestion_review_base import (
    SuggestionsReviewBase,
)
from backend.web.profiled_render import render_template


@dataclass
class ApiWriteTargetModel:
    auth_id: str
    user: Account
    event_key: EventKey
    message: str


class SuggestApiWriteReviewController(SuggestionsReviewBase[ApiWriteTargetModel]):
    REQUIRED_PERMISSIONS = [AccountPermission.REVIEW_APIWRITE]

    def __init__(self, *args, **kw):
        super(SuggestApiWriteReviewController, self).__init__(*args, **kw)

    def create_target_model(
        self, suggestion: Suggestion
    ) -> Optional[ApiWriteTargetModel]:
        message = request.args.get("user_message")
        event_key = suggestion.contents["event_key"]
        user = suggestion.author.get()
        event = Event.get_by_id(event_key)

        auth_id = "".join(
            random.choice(
                string.ascii_lowercase + string.ascii_uppercase + string.digits
            )
            for _ in range(16)
        )
        auth_types = request.form.getlist("auth_types") or []
        expiration_offset = int(request.form.get("expiration_days"))
        if expiration_offset != -1:
            expiration_event_end = event.end_date + timedelta(
                days=expiration_offset + 1
            )
            expiration_now = datetime.now() + timedelta(days=expiration_offset)
            expiration = max(expiration_event_end, expiration_now)
        else:
            expiration = None
        auth = ApiAuthAccess(
            id=auth_id,
            description="{} @ {}".format(
                user.display_name, suggestion.contents["event_key"]
            ).encode("utf-8"),
            secret="".join(
                random.choice(
                    string.ascii_lowercase + string.ascii_uppercase + string.digits
                )
                for _ in range(64)
            ),
            event_list=[ndb.Key(Event, event_key)],
            auth_types_enum=[AuthType(int(t)) for t in auth_types],
            owner=suggestion.author,
            expiration=expiration,
        )
        auth.put()

        email_message = """Hi {},

We graciously accept your request for auth tokens so you can add data to the following event: {} {}

You can find the keys on your account overview page: https://www.thebluealliance.com/account
{}
If you have any questions, please don't heasitate to reach out to us at contact@thebluealliance.com

Thanks,
TBA Admins
            """.format(
            user.display_name, event.year, event.name, message
        )

        return ApiWriteTargetModel(
            auth_id=auth_id, user=user, event_key=event_key, message=email_message
        )

    def get(self) -> Response:
        super().get()
        suggestions = (
            Suggestion.query()
            .filter(Suggestion.review_state == SuggestionState.REVIEW_PENDING)
            .filter(Suggestion.target_model == "api_auth_access")
            .fetch()
        )
        suggestions = [self._ids_and_events(suggestion) for suggestion in suggestions]

        template_values = {
            "success": request.args.get("success"),
            "suggestions": suggestions,
            "auth_names": WRITE_TYPE_NAMES,
        }
        return render_template(
            "suggestions/suggest_apiwrite_review_list.html", template_values
        )

    def post(self) -> Response:
        super().post()
        self.verify_permissions()

        suggestion_id = int(request.form.get("suggestion_id"))
        verdict = request.form.get("verdict")
        message = request.form.get("user_message")

        admin_email_body = None
        email_body = None
        user = None
        event_key = None
        status = ""

        logged_in_user = none_throws(current_user())
        if verdict == "accept":
            status = "accept"
            accepted = self._process_accepted(suggestion_id)
            admin_email_body = """{} ({}) has accepted the request with the following message:
{}

View the key: https://www.thebluealliance.com/admin/api_auth/edit/{}

""".format(
                logged_in_user.display_name,
                logged_in_user.email,
                message,
                accepted.auth_id,
            ).encode(
                "utf-8"
            )

        elif verdict == "reject":
            suggestion: Suggestion = none_throws(Suggestion.get_by_id(suggestion_id))
            event_key = suggestion.contents["event_key"]
            user = suggestion.author.get()
            event = Event.get_by_id(event_key)
            self._process_rejected([none_throws(suggestion.key.id())])

            status = "reject"
            email_body = """Hi {},  # noqa: F841

We have reviewed your request for auth tokens for {} {} and have regretfully declined to issue keys with the following message:

{}

If you have any questions, please don't hesitate to reach out to us at contact@thebluealliance.com

Thanks,
TBA Admins
""".format(
                user.display_name, event.year, event.name, message
            ).encode(
                "utf-8"
            )

            admin_email_body = """{} ({}) has rejected this request with the following reason:  # noqa: F841
{}
""".format(
                logged_in_user.display_name,
                logged_in_user.email,
                message,
            ).encode(
                "utf-8"
            )

        # Notify the user their keys are available
        """
        TODO port outoing email
        if email_body:
            mail.send_mail(sender="The Blue Alliance Contact <contact@thebluealliance.com>",
                           to=user.email,
                           subject="The Blue Alliance Auth Tokens for {}".format(event_key),
                           body=email_body)
        if admin_email_body:
            # Subject should match the one in suggest_apiwrite_controller
            subject = "Trusted API Key Request for {}".format(event_key)
            OutgoingNotificationHelper.send_admin_alert_email(subject, admin_email_body)
        """

        return redirect(f"/suggest/apiwrite/review?success={status}")

    @classmethod
    def _ids_and_events(cls, suggestion: Suggestion) -> Any:
        event_key = suggestion.contents["event_key"]

        account = suggestion.author.get()
        existing_keys = ApiAuthAccess.query(
            ApiAuthAccess.event_list == ndb.Key(Event, event_key)
        )
        existing_users = [
            key.owner.get() if key.owner else None for key in existing_keys
        ]
        return (
            none_throws(suggestion.key.id()),
            Event.get_by_id(event_key),
            account,
            zip(existing_keys, existing_users),
            suggestion,
        )
