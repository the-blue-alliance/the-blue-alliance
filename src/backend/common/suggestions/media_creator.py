from typing import List

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.manipulators.media_manipulator import MediaManipulator
from backend.common.models.media import Media
from backend.common.models.suggestion import Suggestion


class MediaCreator:
    """
    Used to create a Media object from an accepted Suggestion
    """

    @classmethod
    def from_suggestion(cls, suggestion: Suggestion) -> Media:
        team_reference = Media.create_reference(
            suggestion.contents["reference_type"], suggestion.contents["reference_key"]
        )

        media = cls.create_media_model(suggestion, team_reference)
        return MediaManipulator.createOrUpdate(media)

    @staticmethod
    def create_media_model(
        suggestion: Suggestion,
        team_reference: ndb.Key,
        preferred_references: List[ndb.Key] = [],
    ) -> Media:
        media_type_enum = suggestion.contents["media_type_enum"]
        return Media(
            id=Media.render_key_name(
                media_type_enum, suggestion.contents["foreign_key"]
            ),
            foreign_key=suggestion.contents["foreign_key"],
            media_type_enum=media_type_enum,
            details_json=suggestion.contents.get("details_json", None),
            private_details_json=suggestion.contents.get("private_details_json", None),
            year=(
                int(none_throws(suggestion.contents["year"]))
                if not suggestion.contents.get("is_social", False)
                else None
            ),
            references=[team_reference],
            preferred_references=preferred_references,
        )
