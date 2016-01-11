class SocialConnectionType(object):
    """
    Constants for social connections
    """

    FACEBOOK = 0
    TWITTER = 1
    YOUTUBE = 2
    GITHUB = 3

    type_names = {
        FACEBOOK: 'Facebook',
        TWITTER: 'Twitter',
        YOUTUBE: 'YouTube',
        GITHUB: 'GitHub',
    }

    PROFILE_URLS = {
        FACEBOOK: "https://www.facebook.com/{}",
        TWITTER: "https://twitter.com/{}",
        YOUTUBE: "https://www.youtube.com/user/{}",
        GITHUB: "https://github.com/{}"
    }