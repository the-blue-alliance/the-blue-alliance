import enum

from backend.common.consts.string_enum import StrEnum


@enum.unique
class WebcastStatus(StrEnum):
    UNKNOWN = "unknown"
    ONLINE = "online"
    OFFLINE = "offline"
