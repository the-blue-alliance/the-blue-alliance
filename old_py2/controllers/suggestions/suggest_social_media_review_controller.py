import logging

from google.appengine.ext import ndb

from consts.account_permissions import AccountPermissions
from controllers.suggestions.suggestions_review_base_controller import SuggestionsReviewBaseController
from helpers.suggestions.media_creator import MediaCreator
from models.media import Media
from models.suggestion import Suggestion
from template_engine import jinja2_engine


class SuggestSocialMediaReviewController(SuggestionsReviewBaseController):
    REQUIRED_PERMISSIONS = [AccountPermissions.REVIEW_MEDIA]
    ALLOW_TEAM_ADMIN_ACCESS = True

    def __init__(self, *args, **kw):
        super(SuggestSocialMediaReviewController, self).__init__(*args, **kw)

    def create_target_model(self, suggestion):
        # Create a basic Media from this suggestion
        return MediaCreator.from_suggestion(suggestion)

    """
    View the list of suggestions.
    """
    def get(self):
        super(SuggestSocialMediaReviewController, self).get()
        suggestions = Suggestion.query().filter(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
            Suggestion.target_model == "social-media").fetch(limit=50)

        reference_keys = []
        for suggestion in suggestions:
            reference_key = suggestion.contents['reference_key']
            reference = Media.create_reference(
                suggestion.contents['reference_type'],
                reference_key)
            reference_keys.append(reference)

        reference_futures = ndb.get_multi_async(reference_keys)
        references = map(lambda r: r.get_result(), reference_futures)
        suggestions_and_references = zip(suggestions, references)

        self.template_values.update({
            "suggestions_and_references": suggestions_and_references,
        })

        self.response.out.write(jinja2_engine.render('suggestions/suggest_team_social_review.html', self.template_values))

    def post(self):
        super(SuggestSocialMediaReviewController, self).post()
        accept_keys = []
        reject_keys = []
        for value in self.request.POST.values():
            logging.debug(value)
            split_value = value.split('::')
            if len(split_value) == 2:
                key = split_value[1]
            else:
                continue
            if value.startswith('accept'):
                accept_keys.append(key)
            elif value.startswith('reject'):
                reject_keys.append(key)

        # Process accepts
        for accept_key in accept_keys:
            self._process_accepted(accept_key)

        # Process rejects
        self._process_rejected(reject_keys)

        return_url = self.request.get('return_url', '/suggest/team/social/review')
        self.redirect(return_url)
