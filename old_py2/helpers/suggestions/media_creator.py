from helpers.media_manipulator import MediaManipulator
from models.media import Media


class MediaCreator(object):
    """
    Used to create a Media object from an accepted Suggestion
    """

    @classmethod
    def from_suggestion(cls, suggestion):
        team_reference = Media.create_reference(
            suggestion.contents['reference_type'],
            suggestion.contents['reference_key'])

        media = MediaCreator.create_media_model(suggestion, team_reference)
        return MediaManipulator.createOrUpdate(media)

    @classmethod
    def create_media_model(cls, suggestion, team_reference, preferred_references=[]):
        media_type_enum = suggestion.contents['media_type_enum']
        return Media(
            id=Media.render_key_name(media_type_enum, suggestion.contents['foreign_key']),
            foreign_key=suggestion.contents['foreign_key'],
            media_type_enum=media_type_enum,
            details_json=suggestion.contents.get('details_json', None),
            private_details_json=suggestion.contents.get('private_details_json', None),
            year=int(suggestion.contents['year']) if not suggestion.contents.get('is_social', False) else None,
            references=[team_reference],
            preferred_references=preferred_references,
        )
