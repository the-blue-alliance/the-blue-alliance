from typing import Dict, List, TypedDict

from backend.common.sitevars.sitevar import Sitevar


class WebcastType(TypedDict):
    key_name: str
    type: str
    file: str
    channel: str
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
        return cls.get().get("default_chat")

    @classmethod
    def webcasts(cls) -> List[WebcastType]:
        return cls.get().get("webcasts")
