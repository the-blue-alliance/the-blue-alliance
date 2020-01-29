class MediaType(object):
    # ndb keys are based on these! Don't change!
    YOUTUBE_VIDEO = 0
    CD_PHOTO_THREAD = 1
    IMGUR = 2
    FACEBOOK_PROFILE = 3
    TWITTER_PROFILE = 4
    YOUTUBE_CHANNEL = 5
    GITHUB_PROFILE = 6
    INSTAGRAM_PROFILE = 7
    PERISCOPE_PROFILE = 8
    GRABCAD = 9
    INSTAGRAM_IMAGE = 10
    EXTERNAL_LINK = 11
    AVATAR = 12
    ONSHAPE = 13

    type_names = {
        YOUTUBE_VIDEO: 'YouTube Video',
        CD_PHOTO_THREAD: 'Chief Delphi Photo Thread',
        IMGUR: 'Imgur Image',
        FACEBOOK_PROFILE: 'Facebook Profile',
        TWITTER_PROFILE: 'Twitter Profile',
        YOUTUBE_CHANNEL: 'YouTube Channel',
        GITHUB_PROFILE: 'GitHub Profile',
        INSTAGRAM_PROFILE: 'Instagram Profile',
        PERISCOPE_PROFILE: 'Periscope Profile',
        GRABCAD: 'GrabCAD',
        INSTAGRAM_IMAGE: 'Instagram Image',
        EXTERNAL_LINK: 'External Link',
        AVATAR: 'Avatar',
        ONSHAPE: 'Onshape',
    }

    image_types = [
        CD_PHOTO_THREAD,
        IMGUR,
        INSTAGRAM_IMAGE,
    ]

    social_types = [
        FACEBOOK_PROFILE,
        TWITTER_PROFILE,
        YOUTUBE_CHANNEL,
        GITHUB_PROFILE,
        INSTAGRAM_PROFILE,
        PERISCOPE_PROFILE,
    ]

    # Media used to back a Robot Profile
    robot_types = [
        GRABCAD,
        ONSHAPE,
    ]

    profile_urls = {  # Format with foreign_key
        FACEBOOK_PROFILE: 'https://www.facebook.com/{}',
        TWITTER_PROFILE: 'https://twitter.com/{}',
        YOUTUBE_CHANNEL: 'https://www.youtube.com/{}',
        GITHUB_PROFILE: 'https://github.com/{}',
        INSTAGRAM_PROFILE: 'https://www.instagram.com/{}',
        PERISCOPE_PROFILE: 'https://www.periscope.tv/{}',
    }
