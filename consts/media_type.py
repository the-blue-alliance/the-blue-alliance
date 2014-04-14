class MediaType(object):
    # ndb keys are based on these! Don't change!
    YOUTUBE = 0
    CD_PHOTO_THREAD = 1
    IMGUR = 2

    type_names = {
        YOUTUBE: 'YouTube Video',
        CD_PHOTO_THREAD: 'Chief Delphi Photo Thread',
        IMGUR: 'Imgur Image',
    }
