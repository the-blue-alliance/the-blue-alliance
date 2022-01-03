from typing import Dict, List, Optional, TypedDict

from backend.common.models.webcast import Webcast
from backend.common.sitevars.sitevar import Sitevar


class WebcastType(Webcast):
    name: str


class ContentType(TypedDict):
    default_chat: str
    webcasts: List[WebcastType]
    aliases: Dict[str, str]


class GamedaySpecialWebcasts(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "gameday.special_webcasts"

    @staticmethod
    def description() -> str:
        return "For GameDay webcasts not associated with an event"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(
            default_chat="tbagameday",
            webcasts=[],
            aliases={},
        )

    @classmethod
    def default_chat(cls) -> str:
        return cls.get()["default_chat"]

    @classmethod
    def webcasts(cls) -> List[WebcastType]:
        return cls.get()["webcasts"]

    @classmethod
    def get_alias(cls, alias) -> Optional[str]:
        return cls.get()["aliases"].get(alias)
