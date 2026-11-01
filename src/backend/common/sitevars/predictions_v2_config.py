from typing import TypedDict

from backend.common.sitevars.sitevar import Sitevar


class ContentType(TypedDict):
    enabled: bool


class PredictionsV2Config(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "predictions_v2_config"

    @staticmethod
    def description() -> str:
        return "Kill switch of the predictions_v2 pipeline (set enabled to run it)"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(enabled=False)

    @classmethod
    def enabled(cls) -> bool:
        return bool(cls.get().get("enabled", False))
