from models.media import Media


class MediaCreator(object):
    """
    Used to create a Media object from an accepted Suggestion
    """

    @classmethod
    def create_media(cls, suggestion, team_reference, preferred_references=[]):
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
