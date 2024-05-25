from typing import List, TypedDict

from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
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

    @classmethod
    def should_skip_eventteams(cls, event: Event) -> bool:
        sv = cls.get()
        if event.key_name in sv["skip_eventteams"]:
            return True

        # For events that have divisions (like DCMP or Einstein), the FRC API returns
        # team registrations. Once the event starts though, we want the registrations
        # to only be for the division, and let the "finals" event only include teams
        # who play a match or win an award
        if (
            event.event_type_enum in [EventType.DISTRICT_CMP, EventType.CMP_FINALS]
            and len(event.divisions) > 0
            and (event.now or event.past)
        ):
            return True

        return False
