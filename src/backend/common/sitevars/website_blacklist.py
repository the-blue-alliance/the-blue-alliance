from typing import List, TypedDict

from backend.common.sitevars.sitevar import Sitevar


class ContentType(TypedDict):
    websites: List[str]


class WebsiteBlacklist(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "website_blacklist"

    @staticmethod
    def description() -> str:
        return "For blacklisting sketchy websites from team pages"

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(
            websites=[],
        )

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
            should_update=lambda v: website not in v["websites"],
            update_f=update_data,
        )
