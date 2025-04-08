import datetime
from typing import NotRequired, Optional, TypedDict

from backend.common.sitevars.sitevar import Sitevar


class WebConfig(TypedDict):
    travis_job: str
    tbaClient_endpoints_sha: str
    current_commit: str
    deploy_time: str
    endpoints_sha: str
    commit_time: str


class AndroidConfig(TypedDict):
    min_app_version: int
    latest_app_version: int


class IOSConfig(TypedDict):
    min_app_version: int
    latest_app_version: int


class ContentType(TypedDict):
    current_season: int
    max_season: int
    web: NotRequired[Optional[WebConfig]]
    android: Optional[AndroidConfig]
    ios: Optional[IOSConfig]
    max_team_page: int


class ApiStatus(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "apistatus"

    @staticmethod
    def description() -> str:
        return "For setting max year, min app versions, etc."

    @staticmethod
    def default_value() -> ContentType:
        current_year = datetime.datetime.now().year
        return ContentType(
            current_season=current_year,
            max_season=current_year,
            web=None,
            android=None,
            ios=None,
            max_team_page=0,
        )

    @classmethod
    def status(cls) -> ContentType:
        return cls.get()
