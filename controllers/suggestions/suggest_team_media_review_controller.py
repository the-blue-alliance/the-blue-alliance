import datetime
import os
import json

from google.appengine.ext import ndb

from consts.media_type import MediaType
from controllers.suggestions.suggestions_review_base_controller import SuggestionsReviewBaseController
from helpers.media_manipulator import MediaManipulator
from models.media import Media
from models.suggestion import Suggestion
from template_engine import jinja2_engine


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
        existing_preferred_keys_futures = []
        for suggestion in suggestions:
            reference_key = suggestion.contents['reference_key']
            reference = Media.create_reference(
                suggestion.contents['reference_type'],
                reference_key)
            reference_keys.append(reference)

            if 'details_json' in suggestion.contents:
                suggestion.details = json.loads(suggestion.contents['details_json'])
                if 'image_partial' in suggestion.details:
                    suggestion.details['thumbnail'] = suggestion.details['image_partial'].replace('_l', '_m')

            # Find existing preferred images
            existing_preferred_keys_futures.append(
                Media.query(
                    Media.media_type_enum==suggestion.contents['media_type_enum'],
                    Media.references==reference,
                    Media.preferred_references==reference
                ).fetch_async(keys_only=True)
            )

        reference_futures = ndb.get_multi_async(reference_keys)
        existing_preferred_futures = map(lambda x: ndb.get_multi_async(x.get_result()), existing_preferred_keys_futures)

        references = map(lambda r: r.get_result(), reference_futures)
        existing_preferred = map(lambda l: map(lambda x: x.get_result(), l),  existing_preferred_futures)

        suggestions_and_references_and_preferred = zip(suggestions, references, existing_preferred)

        self.template_values.update({
            "suggestions_and_references_and_preferred": suggestions_and_references_and_preferred,
            "max_preferred": Media.MAX_PREFERRED,
        })

        self.response.out.write(jinja2_engine.render('suggest_team_media_review_list.html', self.template_values))

    def _process_accepted(self, accept_key, preferred_keys):
        """
        Performs all actions for an accepted Suggestion.
        Suggestions are processed one at a time (instead of in batch) to reduce
        the likelihood of a race condition. We can't use GAE Transactions here
        due to the ancestor query limitations.

        Actions include:
        - Creating and saving a new Media for the Suggestion
        - Removing a reference from another Media's preferred_references
        - Marking the Suggestion as accepted and saving it
        """
        # Async get
        suggestion_future = Suggestion.get_by_id_async(accept_key)

        # Setup
        to_replace_id = self.request.POST.get('replace-preferred-{}'.format(accept_key), None)

        # Resolve async Futures
        suggestion = suggestion_future.get_result()

        # Make sure Suggestion hasn't been processed (by another thread)
        if suggestion.review_state != Suggestion.REVIEW_PENDING:
            return

        # Remove preferred reference from another Media if specified
        team_reference = Media.create_reference(
            suggestion.contents['reference_type'],
            suggestion.contents['reference_key'])
        if to_replace_id:
            to_replace = Media.get_by_id(to_replace_id)
            if team_reference not in to_replace.preferred_references:
                return  # Preferred reference must have been edited earlier. Skip this Suggestion for now.
            to_replace.preferred_references.remove(team_reference)

        # Add preferred reference to current Media (images only) if explicitly listed in preferred_keys or if to_replace_id exists
        media_type_enum = suggestion.contents['media_type_enum']
        preferred_references = []
        if media_type_enum in MediaType.image_types and (suggestion.key.id() in preferred_keys or to_replace_id):
            preferred_references = [team_reference]

        media = Media(
            id=Media.render_key_name(suggestion.contents['media_type_enum'], suggestion.contents['foreign_key']),
            foreign_key=suggestion.contents['foreign_key'],
            media_type_enum=media_type_enum,
            details_json=suggestion.contents.get('details_json', None),
            private_details_json=suggestion.contents.get('private_details_json', None),
            year=int(suggestion.contents['year']),
            references=[team_reference],
            preferred_references=preferred_references,
        )

        # Mark Suggestion as accepted
        suggestion.review_state = Suggestion.REVIEW_ACCEPTED
        suggestion.reviewer = self.user_bundle.account.key
        suggestion.reviewed_at = datetime.datetime.now()

        # Do all DB writes
        if to_replace_id:
            MediaManipulator.createOrUpdate(to_replace, auto_union=False)
        MediaManipulator.createOrUpdate(media)
        suggestion.put()

    def post(self):
        accept_keys = self.request.POST.getall("accept_keys[]")
        reject_keys = self.request.POST.getall("reject_keys[]")
        preferred_keys = self.request.POST.getall("preferred_keys[]")

        # Process accepts
        for accept_key in accept_keys:
            self._process_accepted(accept_key, preferred_keys)

        # Process rejects
        rejected_suggestion_futures = [Suggestion.get_by_id_async(key) for key in reject_keys]
        rejected_suggestions = map(lambda a: a.get_result(), rejected_suggestion_futures)
        for suggestion in rejected_suggestions:
            if suggestion.review_state == Suggestion.REVIEW_PENDING:
                suggestion.review_state = Suggestion.REVIEW_REJECTED
        ndb.put_multi(rejected_suggestions)

        self.redirect("/suggest/team/media/review")
