import enum

from backend.common.consts.string_enum import StrEnum


@enum.unique
class WebcastType(StrEnum):
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
