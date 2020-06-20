from typing import List

from typing_extensions import TypedDict

from backend.common.sitevars.base import SitevarBase


class ContentType(TypedDict):
    websites: List[str]


class WebsiteBlacklist(SitevarBase[ContentType]):
    @staticmethod
    def key() -> str:
        return "website_blacklist"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(websites=[],)

    @classmethod
    def is_blacklisted(cls, website: str) -> bool:
        website_blacklist = cls.get()
        return website in website_blacklist["websites"]

    @classmethod
    def blacklist(cls, website: str) -> None:
        def update_data(data: ContentType):
            data["websites"].append(website)
            return data

        cls.update(
            should_update=lambda v: website not in v["websites"], update_f=update_data,
        )
