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

    chairmans_tags = [
        CHAIRMANS_VIDEO,
        CHAIRMANS_PRESENTATION,
        CHAIRMANS_ESSAY,
    ]
