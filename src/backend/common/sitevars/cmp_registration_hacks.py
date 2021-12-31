from typing import List, TypedDict

from backend.common.models.keys import EventKey
from backend.common.sitevars.sitevar import Sitevar


class EventNameOverride(TypedDict):
    event: EventKey
    short_name: str
    name: str


class ContentType(TypedDict):
    set_start_to_last_day: List[EventKey]
    event_name_override: List[EventNameOverride]
    divisions_to_skip: List[EventKey]
    skip_eventteams: List[EventKey]


class ChampsRegistrationHacks(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "cmp_registration_hacks"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(
            set_start_to_last_day=[],
            event_name_override=[],
            divisions_to_skip=[],
            skip_eventteams=[],
        )

    @staticmethod
    def description() -> str:
        return "Hacks surrounding Division registration edge cases"
