from google.appengine.ext import ndb

from consts.account_permissions import AccountPermissions
from controllers.suggestions.suggestions_review_base_controller import SuggestionsReviewBaseController
from helpers.suggestions.media_creator import MediaCreator
from helpers.outgoing_notification_helper import OutgoingNotificationHelper
from models.media import Media
from models.sitevar import Sitevar
from models.suggestion import Suggestion
from template_engine import jinja2_engine


class SuggestDesignsReviewController(SuggestionsReviewBaseController):
    REQUIRED_PERMISSIONS = [AccountPermissions.REVIEW_DESIGNS]
    ALLOW_TEAM_ADMIN_ACCESS = True

    def __init__(self, *args, **kw):
        super(SuggestDesignsReviewController, self).__init__(*args, **kw)

    def create_target_model(self, suggestion):
        # Create a basic Media from this suggestion
        return MediaCreator.from_suggestion(suggestion)

    """
    View the list of suggestions.
    """
    def get(self):
        super(SuggestDesignsReviewController, self).get()
        if self.request.get('action') and self.request.get('id'):
            # Fast-path review
            self._fastpath_review()

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

        self.response.out.write(jinja2_engine.render('suggestions/suggest_designs_review.html', self.template_values))

    def _fastpath_review(self):
        suggestion = Suggestion.get_by_id(self.request.get('id'))
        status = None
        if suggestion and suggestion.target_model == 'robot':
            if suggestion.review_state == Suggestion.REVIEW_PENDING:
                slack_message = None
                if self.request.get('action') == 'accept':
                    self._process_accepted(suggestion.key.id())
                    status = 'accepted'
                    slack_message = u"{0} ({1}) accepted the <https://grabcad.com/library/{2}|suggestion> for team <https://www.thebluealliance.com/team/{3}/{4}|{3} in {4}>".format(
                        self.user_bundle.account.display_name,
                        self.user_bundle.account.email,
                        suggestion.contents['foreign_key'],
                        suggestion.contents['reference_key'][3:],
                        suggestion.contents['year']
                    ).encode('utf-8')
                elif self.request.get('action') == 'reject':
                    self._process_rejected(suggestion.key.id())
                    status = 'rejected'
                    slack_message = u"{0} ({1}) rejected the <https://grabcad.com/library/{2}|suggestion> for team <https://www.thebluealliance.com/team/{3}/{4}|{3} in {4}>".format(
                        self.user_bundle.account.display_name,
                        self.user_bundle.account.email,
                        suggestion.contents['foreign_key'],
                        suggestion.contents['reference_key'][3:],
                        suggestion.contents['year']
                    ).encode('utf-8')

                if slack_message:
                    slack_sitevar = Sitevar.get_or_insert('slack.hookurls')
                    if slack_sitevar:
                        slack_url = slack_sitevar.contents.get('tbablog', '')
                        OutgoingNotificationHelper.send_slack_alert(slack_url, slack_message)
            else:
                status = 'already_reviewed'
        else:
            status = 'bad_suggestion'

        if status:
            self.redirect('/suggest/review?status={}'.format(status), abort=True)

    def post(self):
        super(SuggestDesignsReviewController, self).post()
        accept_keys = []
        reject_keys = []
        for value in self.request.POST.values():
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

        return_url = self.request.get('return_url', '/suggest/cad/review')
        self.redirect(return_url)
