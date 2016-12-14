import logging
import random
import string
from datetime import datetime, timedelta

from google.appengine.api import mail
from google.appengine.api.app_identity import app_identity
from google.appengine.ext import ndb

import tba_config
from consts.account_permissions import AccountPermissions
from consts.auth_type import AuthType
from controllers.suggestions.suggestions_review_base_controller import \
    SuggestionsReviewBaseController
from helpers.suggestions.suggestion_notifier import SuggestionNotifier
from models.api_auth_access import ApiAuthAccess
from models.event import Event
from models.suggestion import Suggestion
from template_engine import jinja2_engine


class SuggestApiWriteReviewController(SuggestionsReviewBaseController):

    def __init__(self, *args, **kw):
        self.REQUIRED_PERMISSIONS.append(AccountPermissions.REVIEW_APIWRITE)
        super(SuggestApiWriteReviewController, self).__init__(*args, **kw)

    def get(self):
        suggestions = Suggestion.query().filter(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
            Suggestion.target_model == "api_auth_access").fetch()
        suggestions = [self._ids_and_events(suggestion) for suggestion in suggestions]

        self.template_values.update({
            'success': self.request.get("success"),
            'suggestions': suggestions,
            'auth_names': AuthType.type_names,
        })
        self.response.out.write(
            jinja2_engine.render('suggest_apiwrite_review_list.html', self.template_values))

    @ndb.transactional(xg=True)
    def _process_accepted(self, suggestion_id, message):
        suggestion = Suggestion.get_by_id(suggestion_id)
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
            description="{} @ {}".format(user.display_name, suggestion.contents['event_key']),
            secret=''.join(
                random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _
                in range(64)),
            event_list=[ndb.Key(Event, event_key)],
            auth_types_enum=[int(type) for type in auth_types],
            owner=suggestion.author,
            expiration=expiration
        )
        auth.put()

        suggestion.review_state = Suggestion.REVIEW_ACCEPTED
        suggestion.reviewer = self.user_bundle.account.key
        suggestion.reviewed_at = datetime.now()
        suggestion.put()

        return auth_id, user, event_key, """Hi {},

We graciously accept your request for auth tokens so you can add data to the following event: {} {}

You can find the keys on your account overview page: https://www.thebluealliance.com/account
{}
If you have any questions, please don't heasitate to reach out to us at contact@thebluealliance.com

Thanks,
TBA Admins
            """.format(user.display_name, event.year, event.name, message)

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
            auth_id, user, event_key, email_body = self._process_accepted(suggestion_id, message)
            admin_email_body = """{} ({}) has accepted the request with the following message:
{}

View the key: https://www.thebluealliance.com/admin/api_auth/edit/{}

""".format(self.user_bundle.account.display_name, self.user_bundle.account.email, message, auth_id)

        elif verdict == "reject":
            suggestion = Suggestion.get_by_id(suggestion_id)
            event_key = suggestion.contents['event_key']
            user = suggestion.author.get()
            event = Event.get_by_id(event_key)
            suggestion.review_state = Suggestion.REVIEW_REJECTED
            suggestion.reviewer = self.user_bundle.account.key
            suggestion.reviewed_at = datetime.now()
            suggestion.put()

            status = 'reject'
            email_body = """Hi {},

We have reviewer your request for auth tokens for {} {} and have regretfully declined with the following message:

{}

If you have any questions, please don't hesitate to reach out to us at contact@thebluealliance.com

Thanks,
TBA Admins
""".format(user.display_name, event.year, event.name, message)

            admin_email_body = """{} ({}) has rejected this request with the following reason:
{}
""".format(self.user_bundle.account.display_name, self.user_bundle.account.email, message)

        # Notify the user their keys are available
        if email_body:
            mail.send_mail(sender="The Blue Alliance Contact <contact@thebluealliance.com>",
                           to=user.email,
                           subject="The Blue Alliance Auth Tokens for {}".format(event_key),
                           body=email_body)
        if admin_email_body:
            # Subject should match the one in suggest_apiwrite_controller
            subject = "Trusted API Key Request for {}".format(event_key)
            SuggestionNotifier.send_admin_alert_email(subject, admin_email_body)

        self.redirect("/suggest/apiwrite/review?success={}".format(status))

    @classmethod
    def _ids_and_events(cls, suggestion):
        event_key = suggestion.contents['event_key']
        account = suggestion.author.get()
        existing_keys = ApiAuthAccess.query(ApiAuthAccess.event_list == ndb.Key(Event, event_key))
        existing_users = [key.owner.get() if key.owner else None for key in existing_keys]
        return suggestion.key.id(), Event.get_by_id(event_key), account, zip(existing_keys, existing_users), suggestion
