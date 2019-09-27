import random
import string
from datetime import datetime, timedelta

from google.appengine.api import mail
from google.appengine.ext import ndb

from consts.account_permissions import AccountPermissions
from consts.auth_type import AuthType
from controllers.suggestions.suggestions_review_base_controller import \
    SuggestionsReviewBaseController
from helpers.outgoing_notification_helper import OutgoingNotificationHelper
from models.api_auth_access import ApiAuthAccess
from models.event import Event
from models.suggestion import Suggestion
from template_engine import jinja2_engine


class SuggestApiWriteReviewController(SuggestionsReviewBaseController):
    REQUIRED_PERMISSIONS = [AccountPermissions.REVIEW_APIWRITE]

    def __init__(self, *args, **kw):
        super(SuggestApiWriteReviewController, self).__init__(*args, **kw)

    def create_target_model(self, suggestion):
        message = self.request.get("user_message")
        event_key = suggestion.contents['event_key']
        user = suggestion.author.get()
        event = Event.get_by_id(event_key)

        auth_id = ''.join(
            random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in
            range(16))
        auth_types = self.request.get_all("auth_types", [])
        expiration_offset = int(self.request.get("expiration_days"))
        if expiration_offset != -1:
            expiration_event_end = event.end_date + timedelta(days=expiration_offset + 1)
            expiration_now = datetime.now() + timedelta(days=expiration_offset)
            expiration = max(expiration_event_end, expiration_now)
        else:
            expiration = None
        auth = ApiAuthAccess(
            id=auth_id,
            description=u"{} @ {}".format(user.display_name, suggestion.contents['event_key']).encode('utf-8'),
            secret=''.join(
                random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _
                in range(64)),
            event_list=[ndb.Key(Event, event_key)],
            auth_types_enum=[int(type) for type in auth_types],
            owner=suggestion.author,
            expiration=expiration
        )
        auth.put()
        return auth_id, user, event_key, u"""Hi {},

We graciously accept your request for auth tokens so you can add data to the following event: {} {}

You can find the keys on your account overview page: https://www.thebluealliance.com/account
{}
If you have any questions, please don't heasitate to reach out to us at contact@thebluealliance.com

Thanks,
TBA Admins
            """.format(user.display_name, event.year, event.name, message).encode('utf-8')

    def get(self):
        suggestions = Suggestion.query().filter(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
            Suggestion.target_model == "api_auth_access").fetch()
        suggestions = [self._ids_and_events(suggestion) for suggestion in suggestions]

        self.template_values.update({
            'success': self.request.get("success"),
            'suggestions': suggestions,
            'auth_names': AuthType.write_type_names,
        })
        self.response.out.write(
            jinja2_engine.render('suggestions/suggest_apiwrite_review_list.html', self.template_values))

    def post(self):
        self.verify_permissions()
        suggestion_id = int(self.request.get("suggestion_id"))
        verdict = self.request.get("verdict")
        message = self.request.get("user_message")

        admin_email_body = None
        email_body = None
        user = None
        event_key = None
        status = ''
        if verdict == "accept":
            status = 'accept'
            auth_id, user, event_key, email_body = self._process_accepted(suggestion_id)
            admin_email_body = u"""{} ({}) has accepted the request with the following message:
{}

View the key: https://www.thebluealliance.com/admin/api_auth/edit/{}

""".format(self.user_bundle.account.display_name, self.user_bundle.account.email, message, auth_id).encode('utf-8')

        elif verdict == "reject":
            suggestion = Suggestion.get_by_id(suggestion_id)
            event_key = suggestion.contents['event_key']
            user = suggestion.author.get()
            event = Event.get_by_id(event_key)
            self._process_rejected(suggestion.key.id())

            status = 'reject'
            email_body = u"""Hi {},

We have reviewed your request for auth tokens for {} {} and have regretfully declined to issue keys with the following message:

{}

If you have any questions, please don't hesitate to reach out to us at contact@thebluealliance.com

Thanks,
TBA Admins
""".format(user.display_name, event.year, event.name, message).encode('utf-8')

            admin_email_body = u"""{} ({}) has rejected this request with the following reason:
{}
""".format(self.user_bundle.account.display_name, self.user_bundle.account.email, message).encode('utf-8')

        # Notify the user their keys are available
        if email_body:
            mail.send_mail(sender="The Blue Alliance Contact <contact@thebluealliance.com>",
                           to=user.email,
                           subject="The Blue Alliance Auth Tokens for {}".format(event_key),
                           body=email_body)
        if admin_email_body:
            # Subject should match the one in suggest_apiwrite_controller
            subject = "Trusted API Key Request for {}".format(event_key)
            OutgoingNotificationHelper.send_admin_alert_email(subject, admin_email_body)

        self.redirect("/suggest/apiwrite/review?success={}".format(status))

    @classmethod
    def _ids_and_events(cls, suggestion):
        event_key = suggestion.contents['event_key']
        account = suggestion.author.get()
        existing_keys = ApiAuthAccess.query(ApiAuthAccess.event_list == ndb.Key(Event, event_key))
        existing_users = [key.owner.get() if key.owner else None for key in existing_keys]
        return suggestion.key.id(), Event.get_by_id(event_key), account, zip(existing_keys, existing_users), suggestion
