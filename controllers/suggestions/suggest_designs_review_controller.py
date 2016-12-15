import datetime
import os
import json
import logging

from google.appengine.ext import ndb

from consts.account_permissions import AccountPermissions
from controllers.suggestions.suggestions_review_base_controller import SuggestionsReviewBaseController
from helpers.media_manipulator import MediaManipulator
from helpers.suggestions.media_creator import MediaCreator
from helpers.suggestions.suggestion_notifier import SuggestionNotifier
from models.media import Media
from models.sitevar import Sitevar
from models.suggestion import Suggestion
from template_engine import jinja2_engine


class SuggestDesignsReviewController(SuggestionsReviewBaseController):

    def __init__(self, *args, **kw):
        self.REQUIRED_PERMISSIONS.append(AccountPermissions.REVIEW_DESIGNS)
        super(SuggestDesignsReviewController, self).__init__(*args, **kw)

    """
    View the list of suggestions.
    """
    def get(self):

        if self.request.get('action') and self.request.get('id'):
            # Fast-path review
            self.verify_permissions()
            suggestion = Suggestion.get_by_id(self.request.get('id'))
            if suggestion and suggestion.target_model == 'robot' and suggestion.review_state == Suggestion.REVIEW_PENDING:
                slack_message = None
                if self.request.get('action') == 'accept':
                    self._process_accepted(suggestion.key.id())
                    slack_message = "{} ({}) accepted the <https://grabcad.com/library/{}|suggestion> for team {} in {}".format(
                        self.user_bundle.account.display_name,
                        self.user_bundle.account.email,
                        suggestion.contents['foreign_key'],
                        suggestion.contents['reference_key'][3:],
                        suggestion.contents['year']
                    )
                elif self.request.get('action') == 'reject':
                    suggestion.review_state = Suggestion.REVIEW_REJECTED
                    suggestion.reviewer = self.user_bundle.account.key
                    suggestion.reviewed_at = datetime.datetime.now()
                    suggestion.put()
                    slack_message = "{} ({}) rejected the <https://grabcad.com/library/{}|suggestion> for team {} in {}".format(
                        self.user_bundle.account.display_name,
                        self.user_bundle.account.email,
                        suggestion.contents['foreign_key'],
                        suggestion.contents['reference_key'][3:],
                        suggestion.contents['year']
                    )

                if slack_message:
                    slack_sitevar = Sitevar.get_or_insert('slack.hookurls')
                    if slack_sitevar:
                        slack_url = slack_sitevar.contents.get('tbablog', '')
                        SuggestionNotifier.send_slack_alert(slack_url, slack_message)
                self.redirect('/suggest/review', abort=True)

        suggestions = Suggestion.query().filter(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
            Suggestion.target_model == "robot").fetch(limit=50)

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

        self.response.out.write(jinja2_engine.render('suggest_designs_review.html', self.template_values))

    @ndb.transactional(xg=True)
    def _process_accepted(self, accept_key):
        """
        Performs all actions for an accepted Suggestion in a Transaction.
        Suggestions are processed one at a time (instead of in batch) in a
        Transaction to prevent possible race conditions.
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
        self.verify_permissions()
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

        self.redirect("/suggest/cad/review")
