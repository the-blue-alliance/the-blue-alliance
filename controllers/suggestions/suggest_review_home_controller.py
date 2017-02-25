import os

from google.appengine.ext.webapp import template

from consts.account_permissions import AccountPermissions
from controllers.suggestions.suggestions_review_base_controller import SuggestionsReviewBaseController
from helpers.suggestions.suggestion_fetcher import SuggestionFetcher
from models.suggestion import Suggestion
from template_engine import jinja2_engine


class SuggestReviewHomeController(SuggestionsReviewBaseController):
    """The main view for a data reviewer to see the state of pending suggestions."""

    def __init__(self, *args, **kw):
        super(SuggestReviewHomeController, self).__init__(*args, **kw)

        # Ensure that the user is logged in and has some permission
        self._require_registration()
        if not self.user_bundle.account.permissions and not self.user_bundle.is_current_user_admin:
            self.redirect(
                "/",
                abort=True
            )

    def get(self):
        self.template_values['suggestions'] = dict()
        self.template_values['suggestions']['match'] = SuggestionFetcher.count(Suggestion.REVIEW_PENDING, "match")
        self.template_values['suggestions']['event'] = SuggestionFetcher.count(Suggestion.REVIEW_PENDING, "event")
        self.template_values['suggestions']['media'] = SuggestionFetcher.count(Suggestion.REVIEW_PENDING, "media")
        self.template_values['suggestions']['event_media'] = SuggestionFetcher.count(Suggestion.REVIEW_PENDING, "event_media")
        self.template_values['suggestions']['social'] = SuggestionFetcher.count(Suggestion.REVIEW_PENDING, "social-media")
        self.template_values['suggestions']['offseason'] = SuggestionFetcher.count(Suggestion.REVIEW_PENDING, "offseason-event")
        self.template_values['suggestions']['apiwrite'] = SuggestionFetcher.count(Suggestion.REVIEW_PENDING, "api_auth_access")
        self.template_values['suggestions']['cad'] = SuggestionFetcher.count(Suggestion.REVIEW_PENDING, "robot")

        self.template_values['media_permission'] = AccountPermissions.REVIEW_MEDIA
        self.template_values['offseason_permission'] = AccountPermissions.REVIEW_OFFSEASON_EVENTS
        self.template_values['apiwrite_permission'] = AccountPermissions.REVIEW_APIWRITE
        self.template_values['cad_permission'] = AccountPermissions.REVIEW_DESIGNS
        self.template_values['event_media_permission'] = AccountPermissions.REVIEW_EVENT_MEDIA
        self.template_values['status'] = self.request.get('status')

        self.response.out.write(jinja2_engine.render('suggestions/suggest_review_home.html', self.template_values))
