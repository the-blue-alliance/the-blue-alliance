import datetime
import os
import json
import logging

from google.appengine.ext import ndb

from consts.account_permissions import AccountPermissions
from consts.media_type import MediaType
from controllers.suggestions.suggestions_review_base_controller import SuggestionsReviewBaseController
from helpers.media_manipulator import MediaManipulator
from helpers.suggestions.media_creator import MediaCreator
from models.media import Media
from models.suggestion import Suggestion
from template_engine import jinja2_engine


class SuggestSocialMediaReviewController(SuggestionsReviewBaseController):

    def __init__(self, *args, **kw):
        self.REQUIRED_PERMISSIONS.append(AccountPermissions.REVIEW_MEDIA)
        super(SuggestSocialMediaReviewController, self).__init__(*args, **kw)

    """
    View the list of suggestions.
    """
    def get(self):
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

        self.response.out.write(jinja2_engine.render('suggest_team_social_review.html', self.template_values))

    @ndb.transactional(xg=True)
    def _process_accepted(self, accept_key):
        """
        Performs all actions for an accepted Suggestion in a Transaction.
        Suggestions are processed one at a time (instead of in batch) in a
        Transaction to prevent possible race conditions.

        Actions include:
        - Creating and saving a new Media for the Suggestion
        - Removing a reference from another Media's preferred_references
        - Marking the Suggestion as accepted and saving it
        """
        # Async get
        suggestion_future = Suggestion.get_by_id_async(accept_key)

        # Resolve async Futures
        suggestion = suggestion_future.get_result()

        # Make sure Suggestion hasn't been processed (by another thread)
        if suggestion.review_state != Suggestion.REVIEW_PENDING:
            return

        team_reference = Media.create_reference(
            suggestion.contents['reference_type'],
            suggestion.contents['reference_key'])

        media = MediaCreator.create_media(suggestion, team_reference)

        # Mark Suggestion as accepted
        suggestion.review_state = Suggestion.REVIEW_ACCEPTED
        suggestion.reviewer = self.user_bundle.account.key
        suggestion.reviewed_at = datetime.datetime.now()

        # Do all DB writes
        MediaManipulator.createOrUpdate(media)
        suggestion.put()

    def post(self):
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
        rejected_suggestion_futures = [Suggestion.get_by_id_async(key) for key in reject_keys]
        rejected_suggestions = map(lambda a: a.get_result(), rejected_suggestion_futures)

        for suggestion in rejected_suggestions:
            if suggestion.review_state == Suggestion.REVIEW_PENDING:
                suggestion.review_state = Suggestion.REVIEW_REJECTED
                suggestion.reviewer = self.user_bundle.account.key
                suggestion.reviewed_at = datetime.datetime.now()

        ndb.put_multi(rejected_suggestions)

        self.redirect("/suggest/team/social/review")
