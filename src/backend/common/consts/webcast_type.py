import enum


@enum.unique
class WebcastType(str, enum.Enum):
    TWITCH = "twitch"
    YOUTUBE = "youtube"
    IFRAME = "iframe"
    MMS = "mms"
    RTMP = "rtmp"
    USTREAM = "ustream"
    LIVESTREAM = "livestream"
    HTML5 = "html5"
    DACAST = "dacast"
    STEMTV = "stemtv"
