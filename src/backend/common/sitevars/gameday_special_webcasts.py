from typing import Dict, List, Optional, TypedDict

from backend.common.models.webcast import Webcast
from backend.common.sitevars.sitevar import Sitevar


class WebcastType(Webcast):
    name: str
    key_name: str


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

    @classmethod
    def add_special_webcast(cls, webcast: WebcastType) -> None:
        sv_value = cls.get()
        if any(
            filter(lambda w: w["key_name"] == webcast["key_name"], sv_value["webcasts"])
        ):
            return
        sv_value["webcasts"].append(webcast)
        cls.put(sv_value)

    @classmethod
    def remove_special_webcast(cls, webcast_key: str) -> None:
        sv_value = cls.get()
        sv_value["webcasts"] = [
            webcast
            for webcast in sv_value["webcasts"]
            if webcast["key_name"] != webcast_key
        ]
        cls.put(sv_value)

    @classmethod
    def add_alias(cls, alias_name: str, alias_args: str) -> None:
        sv_value = cls.get()
        sv_value["aliases"][alias_name] = alias_args
        cls.put(sv_value)

    @classmethod
    def remove_alias(cls, alias_name: str) -> None:
        sv_value = cls.get()
        if alias_name in sv_value["aliases"]:
            del sv_value["aliases"][alias_name]
            cls.put(sv_value)

    @classmethod
    def set_default_chat(cls, default_chat: str) -> None:
        sv_value = cls.get()
        sv_value["default_chat"] = default_chat
        cls.put(sv_value)
