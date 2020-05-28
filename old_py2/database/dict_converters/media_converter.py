from database.dict_converters.converter_base import ConverterBase


class MediaConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        3: 4,
    }

    @classmethod
    def _convert(cls, medias, dict_version):
        MEDIA_CONVERTERS = {
            3: cls.mediasConverter_v3,
        }
        return MEDIA_CONVERTERS[dict_version](medias)

    @classmethod
    def mediasConverter_v3(cls, medias):
        medias = map(cls.mediaConverter_v3, medias)
        return medias

    @classmethod
    def mediaConverter_v3(cls, media):
        dict = {
            'type': media.slug_name,
            'foreign_key': media.foreign_key,
            'details': media.details if media.details else {},
            'preferred': True if media.preferred_references != [] else False,
            'view_url': None,
            'direct_url': None,
        }
        if media.slug_name == "youtube":
            dict["direct_url"] = "https://img.youtube.com/vi/{}/hqdefault.jpg".format(media.foreign_key)
            dict["view_url"] = media.youtube_url_link
        else:
            dict["direct_url"] = media.image_direct_url
            dict["view_url"] = media.view_image_url
        return dict
