import enum
from typing import List

from backend.common.consts.string_enum import StrEnum


@enum.unique
class SuggestionType(StrEnum):
    EVENT = "event"
    MATCH = "match"
    MEDIA = "media"
    SOCIAL_MEDIA = "social-media"
    OFFSEASON_EVENT = "offseason-event"
    API_AUTH_ACCESS = "api_auth_access"
    ROBOT = "robot"
    EVENT_MEDIA = "event_media"


SUGGESTION_TYPES: List[SuggestionType] = [t.value for t in SuggestionType]


TYPE_NAMES = {
    SuggestionType.EVENT: "Webcasts",
    SuggestionType.MATCH: "Match Videos",
    SuggestionType.MEDIA: "Team Media",
    SuggestionType.SOCIAL_MEDIA: "Social Media",
    SuggestionType.OFFSEASON_EVENT: "Offseason Events",
    SuggestionType.API_AUTH_ACCESS: "API Key Requests",
    SuggestionType.ROBOT: "CAD Models",
    SuggestionType.EVENT_MEDIA: "Event Videos",
}
