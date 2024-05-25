from typing import TypedDict

from backend.common.consts.landing_type import LandingType
from backend.common.sitevars.sitevar import Sitevar


class ContentType(TypedDict):
    current_landing: int
    build_handler_show_avatars: bool
    build_handler_show_password: bool
    build_handler_show_ri3d: bool
    kickoff_facebook_fbid: str
    game_teaser_youtube_id: str
    game_animation_youtube_id: str
    game_name: str
    manual_password: str


class LandingConfig(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "landing_config"

    @staticmethod
    def description() -> str:
        return "Configuration data for the homepage"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(
            current_landing=2,
            build_handler_show_avatars=False,
            build_handler_show_password=False,
            build_handler_show_ri3d=False,
            kickoff_facebook_fbid="",
            game_teaser_youtube_id="",
            game_animation_youtube_id="",
            game_name="",
            manual_password="",
        )

    @classmethod
    def current_landing_type(cls) -> LandingType:
        # Default to build season handler
        landing_type = cls.get().get("current_landing", 2)
        return LandingType(landing_type)
