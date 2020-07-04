import datetime
from typing import Optional

from typing_extensions import TypedDict

from backend.common.sitevars.base import SitevarBase


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
    web: Optional[WebConfig]
    android: Optional[AndroidConfig]
    ios: Optional[IOSConfig]


class ApiStatus(SitevarBase[ContentType]):
    @staticmethod
    def key() -> str:
        return "apistatus"

    @staticmethod
    def default_value() -> ContentType:
        current_year = datetime.datetime.now().year
        return ContentType(
            current_season=current_year,
            max_season=current_year,
            web=None,
            android=None,
            ios=None,
        )
