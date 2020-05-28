class MediaTag(object):
    # ndb keys are based on these! Don't change!
    CHAIRMANS_VIDEO = 0
    CHAIRMANS_PRESENTATION = 1
    CHAIRMANS_ESSAY = 2

    tag_names = {
        CHAIRMANS_VIDEO: 'Chairman\'s Video',
        CHAIRMANS_PRESENTATION: 'Chairman\'s Presentation',
        CHAIRMANS_ESSAY: 'Chairman\'s Essay',
    }

    tag_url_names = {
        CHAIRMANS_VIDEO: 'chairmans_video',
        CHAIRMANS_PRESENTATION: 'chairmans_presentation',
        CHAIRMANS_ESSAY: 'chairmans_essay',
    }

    chairmans_tags = [
        CHAIRMANS_VIDEO,
        CHAIRMANS_PRESENTATION,
        CHAIRMANS_ESSAY,
    ]

    @classmethod
    def get_enum_from_url(self, url_name):
        inversed = {v: k for k, v in self.tag_url_names.items()}
        if url_name in inversed:
            return inversed[url_name]
        else:
            return None
