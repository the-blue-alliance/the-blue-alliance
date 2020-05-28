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


class SuggestEventMediaReviewController(SuggestionsReviewBaseController):
    REQUIRED_PERMISSIONS = [AccountPermissions.REVIEW_EVENT_MEDIA]

    def __init__(self, *args, **kw):
        self.preferred_keys = []
        super(SuggestEventMediaReviewController, self).__init__(*args, **kw)

    """
    View the list of suggestions.
    """
    def get(self):
        suggestions = Suggestion.query().filter(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
            Suggestion.target_model == "event_media").fetch(limit=50)

        # Quick and dirty way to group images together
        suggestions = sorted(suggestions, key=lambda x: 0 if x.contents['media_type_enum'] in MediaType.image_types else 1)

        reference_keys = []
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

        reference_futures = ndb.get_multi_async(reference_keys)
        references = map(lambda r: r.get_result(), reference_futures)

        suggestions_and_references = zip(suggestions, references)

        self.template_values.update({
            "suggestions_and_references": suggestions_and_references,
        })

        self.response.out.write(jinja2_engine.render('suggestions/suggest_event_media_review_list.html', self.template_values))

    def create_target_model(self, suggestion):
        # Setup

        # Remove preferred reference from another Media if specified
        event_reference = Media.create_reference(
            suggestion.contents['reference_type'],
            suggestion.contents['reference_key'])

        media = MediaCreator.create_media_model(suggestion, event_reference, [])

        # Do all DB writes
        return MediaManipulator.createOrUpdate(media)

    def post(self):
        self.preferred_keys = self.request.POST.getall("preferred_keys[]")
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

        self.redirect("/suggest/event/media/review")
