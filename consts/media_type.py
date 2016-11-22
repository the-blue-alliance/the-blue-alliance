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
    PINTEREST_PROFILE = 9
    SNAPCHAT_PROFILE = 10
    TWITCH_CHANNEL = 11

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
        PINTEREST_PROFILE: 'Pinterest Profile',
        SNAPCHAT_PROFILE: 'Snapchat Profile',
        TWITCH_CHANNEL: 'Twitch Channel',
    }

    image_types = [
        CD_PHOTO_THREAD,
        IMGUR,
    ]

    social_types = [
        FACEBOOK_PROFILE,
        TWITTER_PROFILE,
        YOUTUBE_CHANNEL,
        GITHUB_PROFILE,
        INSTAGRAM_PROFILE,
        PERISCOPE_PROFILE,
        PINTEREST_PROFILE,
        SNAPCHAT_PROFILE,
        TWITCH_CHANNEL,
    ]

    profile_urls = {  # Format with foreign_key
        FACEBOOK_PROFILE: 'https://www.facebook.com/{}',
        TWITTER_PROFILE: 'https://twitter.com/{}',
        YOUTUBE_CHANNEL: 'https://www.youtube.com/{}',
        GITHUB_PROFILE: 'https://github.com/{}',
        INSTAGRAM_PROFILE: 'https://www.instagram.com/{}',
        PERISCOPE_PROFILE: 'https://www.periscope.tv/{}',
        PINTEREST_PROFILE: 'https://www.pinterest.com/{}',
        SNAPCHAT_PROFILE: 'https://www.snapchat.com/add/{}',
        TWITCH_CHANNEL: 'https://www.twitch.tv/{}',
    }
