import datetime
import os
import json

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from consts.media_type import MediaType
from controllers.suggestions.suggestions_review_base_controller import SuggestionsReviewBaseController
from helpers.media_manipulator import MediaManipulator
from models.media import Media
from models.suggestion import Suggestion


class SuggestTeamMediaReviewController(SuggestionsReviewBaseController):
    """
    View the list of suggestions.
    """
    def get(self):
        suggestions = Suggestion.query().filter(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
            Suggestion.target_model == "media")

        # Quick and dirty way to group images together
        suggestions = sorted(suggestions, key=lambda x: 0 if x.contents['media_type_enum'] in MediaType.image_types else 1)

        reference_keys = []
        for suggestion in suggestions:
            reference_keys.append(Media.create_reference(
                suggestion.contents['reference_type'],
                suggestion.contents['reference_key']))
            if 'details_json' in suggestion.contents:
                suggestion.details = json.loads(suggestion.contents['details_json'])
                if 'image_partial' in suggestion.details:
                    suggestion.details['thumbnail'] = suggestion.details['image_partial'].replace('_l', '_m')

        reference_futures = ndb.get_multi_async(reference_keys)
        references = map(lambda r: r.get_result(), reference_futures)

        suggestions_and_references = zip(suggestions, references)

        self.template_values.update({
            "suggestions_and_references": suggestions_and_references,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/suggest_team_media_review_list.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        accept_keys = map(lambda x: int(x) if x.isdigit() else x, self.request.POST.getall("accept_keys[]"))
        reject_keys = map(lambda x: int(x) if x.isdigit() else x, self.request.POST.getall("reject_keys[]"))

        accepted_suggestion_futures = [Suggestion.get_by_id_async(key) for key in accept_keys]
        rejected_suggestion_futures = [Suggestion.get_by_id_async(key) for key in reject_keys]
        accepted_suggestions = map(lambda a: a.get_result(), accepted_suggestion_futures)
        rejected_suggestions = map(lambda a: a.get_result(), rejected_suggestion_futures)

        for suggestion in accepted_suggestions:
            media = Media(
                id=Media.render_key_name(suggestion.contents['media_type_enum'], suggestion.contents['foreign_key']),
                foreign_key=suggestion.contents['foreign_key'],
                media_type_enum=suggestion.contents['media_type_enum'],
                details_json=suggestion.contents.get('details_json', None),
                private_details_json=suggestion.contents.get('private_details_json', None),
                year=int(suggestion.contents['year']),
                references=[Media.create_reference(
                    suggestion.contents['reference_type'],
                    suggestion.contents['reference_key'])],
            )
            MediaManipulator.createOrUpdate(media)

        all_suggestions = accepted_suggestions
        all_suggestions.extend(rejected_suggestions)

        for suggestion in all_suggestions:
            if suggestion.key.id() in accept_keys:
                suggestion.review_state = Suggestion.REVIEW_ACCEPTED
            if suggestion.key.id() in reject_keys:
                suggestion.review_state = Suggestion.REVIEW_REJECTED
            suggestion.reviewer = self.user_bundle.account.key
            suggestion.reviewed_at = datetime.datetime.now()

        ndb.put_multi(all_suggestions)

        self.redirect("/suggest/team/media/review")
