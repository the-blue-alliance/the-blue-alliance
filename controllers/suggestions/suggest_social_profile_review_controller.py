import datetime
import os
import json

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.suggestions.suggestions_review_base_controller import SuggestionsReviewBaseController
from helpers.social_connection_manipulator import SocialConnectionManipulator
from models.media import Media
from models.social_connection import SocialConnection
from models.suggestion import Suggestion


class SuggestSocialProfileReviewController(SuggestionsReviewBaseController):
    """
    View the list of suggestions.
    """
    def get(self):
        suggestions = Suggestion.query().filter(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
            Suggestion.target_model == "social_connection")

        reference_keys = []
        for suggestion in suggestions:
            reference_keys.append(Media.create_reference(
                suggestion.contents['reference_type'],
                suggestion.contents['reference_key']))

        reference_futures = ndb.get_multi_async(reference_keys)
        references = map(lambda r: r.get_result(), reference_futures)

        suggestions_and_references = zip(suggestions, references)

        self.template_values.update({
            "suggestions_and_references": suggestions_and_references,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/suggest_social_review_list.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_admin()

        accept_keys = map(int, self.request.POST.getall("accept_keys[]"))
        reject_keys = map(int, self.request.POST.getall("reject_keys[]"))

        accepted_suggestion_futures = [Suggestion.get_by_id_async(key) for key in accept_keys]
        rejected_suggestion_futures = [Suggestion.get_by_id_async(key) for key in reject_keys]
        accepted_suggestions = map(lambda a: a.get_result(), accepted_suggestion_futures)
        rejected_suggestions = map(lambda a: a.get_result(), rejected_suggestion_futures)

        for suggestion in accepted_suggestions:
            media = SocialConnection(
                id=SocialConnection.render_key_name(suggestion.contents['social_type_enum'], suggestion.contents['foreign_key']),
                foreign_key=suggestion.contents['foreign_key'],
                social_type_enum=suggestion.contents['social_type_enum'],
                references=[SocialConnection.create_reference(
                    suggestion.contents['reference_type'],
                    suggestion.contents['reference_key'])],
            )
            SocialConnectionManipulator.createOrUpdate(media)

        all_suggestions = accepted_suggestions
        all_suggestions.extend(rejected_suggestions)

        for suggestion in all_suggestions:
            if suggestion.key.id() in accept_keys:
                suggestion.review_state = Suggestion.REVIEW_ACCEPTED
            if suggestion.key.id() in reject_keys:
                suggestion.review_state = Suggestion.REVIEW_REJECTED
            suggestion.reviewer = self.user_bundle.account.key
            suggestion.reviewer_at = datetime.datetime.now()

        ndb.put_multi(all_suggestions)

        self.redirect("/suggest/team/social/review")
