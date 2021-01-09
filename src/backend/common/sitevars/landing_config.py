from typing_extensions import TypedDict

from backend.common.consts.landing_type import LandingType
from backend.common.sitevars.base import SitevarBase


class ContentType(TypedDict):
    kickoff_facebook_fbid: str
    game_teaser_youtube_id: str
    current_landing: int
    game_animation_youtube_id: str
    game_name: str
    build_handler_show_avatars: bool
    manual_password: str
    build_handler_show_password: bool
    build_handler_show_ri3d: bool


class LandingConfig(SitevarBase[ContentType]):
    @staticmethod
    def key() -> str:
        return "landing_config"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(
            kickoff_facebook_fbid="",
            game_teaser_youtube_id="",
            current_landing=2,
            game_animation_youtube_id="",
            game_name="",
            build_handler_show_avatars=False,
            manual_password="",
            build_handler_show_password=False,
            build_handler_show_ri3d=False,
        )

    @classmethod
    def current_landing_type(cls) -> LandingType:
        # Default to build season handler
        landing_type = cls.get().get("current_landing", 2)
        return LandingType(landing_type)
