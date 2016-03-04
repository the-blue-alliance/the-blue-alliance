class MediaType(object):
    # ndb keys are based on these! Don't change!
    YOUTUBE_VIDEO = 0
    CD_PHOTO_THREAD = 1
    IMGUR = 2

    type_names = {
        YOUTUBE_VIDEO: 'YouTube Video',
        CD_PHOTO_THREAD: 'Chief Delphi Photo Thread',
        IMGUR: 'Imgur Image'
    }

    image_types = [
        CD_PHOTO_THREAD,
        IMGUR,
    ]
