import enum
from typing import Dict, Set


@enum.unique
class VideoType(str, enum.Enum):
    YOUTUBE = "youtube"
    TBA = "tba"


@enum.unique
class MediaType(enum.IntEnum):
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


MEDIA_TYPES: Set[MediaType] = {t for t in MediaType}

# Do not change! key_names are generated based on this
SLUG_NAMES: Dict[MediaType, str] = {
    MediaType.YOUTUBE_VIDEO: "youtube",
    MediaType.CD_PHOTO_THREAD: "cdphotothread",
    MediaType.IMGUR: "imgur",
    MediaType.FACEBOOK_PROFILE: "facebook-profile",
    MediaType.YOUTUBE_CHANNEL: "youtube-channel",
    MediaType.TWITTER_PROFILE: "twitter-profile",
    MediaType.GITHUB_PROFILE: "github-profile",
    MediaType.INSTAGRAM_PROFILE: "instagram-profile",
    MediaType.PERISCOPE_PROFILE: "periscope-profile",
    MediaType.GRABCAD: "grabcad",
    MediaType.ONSHAPE: "onshape",
    MediaType.INSTAGRAM_IMAGE: "instagram-image",
    MediaType.EXTERNAL_LINK: "external-link",
    MediaType.AVATAR: "avatar",
}

TYPE_NAMES: Dict[MediaType, str] = {
    MediaType.YOUTUBE_VIDEO: "YouTube Video",
    MediaType.CD_PHOTO_THREAD: "Chief Delphi Photo Thread",
    MediaType.IMGUR: "Imgur Image",
    MediaType.FACEBOOK_PROFILE: "Facebook Profile",
    MediaType.TWITTER_PROFILE: "Twitter Profile",
    MediaType.YOUTUBE_CHANNEL: "YouTube Channel",
    MediaType.GITHUB_PROFILE: "GitHub Profile",
    MediaType.INSTAGRAM_PROFILE: "Instagram Profile",
    MediaType.PERISCOPE_PROFILE: "Periscope Profile",
    MediaType.GRABCAD: "GrabCAD",
    MediaType.INSTAGRAM_IMAGE: "Instagram Image",
    MediaType.EXTERNAL_LINK: "External Link",
    MediaType.AVATAR: "Avatar",
    MediaType.ONSHAPE: "Onshape",
}

IMAGE_TYPES: Set[MediaType] = {
    MediaType.CD_PHOTO_THREAD,
    MediaType.IMGUR,
    MediaType.INSTAGRAM_IMAGE,
}

SOCIAL_TYPES: Set[MediaType] = {
    MediaType.FACEBOOK_PROFILE,
    MediaType.TWITTER_PROFILE,
    MediaType.YOUTUBE_CHANNEL,
    MediaType.GITHUB_PROFILE,
    MediaType.INSTAGRAM_PROFILE,
    MediaType.PERISCOPE_PROFILE,
}

# Media used to back a Robot Profile
ROBOT_TYPES: Set[MediaType] = {
    MediaType.GRABCAD,
    MediaType.ONSHAPE,
}

# Format with foreign_key
PROFILE_URLS = {
    MediaType.FACEBOOK_PROFILE: "https://www.facebook.com/{}",
    MediaType.TWITTER_PROFILE: "https://twitter.com/{}",
    MediaType.YOUTUBE_CHANNEL: "https://www.youtube.com/{}",
    MediaType.GITHUB_PROFILE: "https://github.com/{}",
    MediaType.INSTAGRAM_PROFILE: "https://www.instagram.com/{}",
    MediaType.PERISCOPE_PROFILE: "https://www.periscope.tv/{}",
}
