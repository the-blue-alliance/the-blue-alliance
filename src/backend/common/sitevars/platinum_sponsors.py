from typing import Any, List, Literal, Optional, TypedDict

from backend.common.sitevars.sitevar import Sitevar

MAX_SPONSORS = 3

LogoStyle = Literal["wordmark", "mark"]

# Served from src/backend/web/static/images/sponsors/ by the web service
LOGO_BASE_URL = "https://www.thebluealliance.com/images/sponsors"


class Sponsor(TypedDict):
    # Display name, also the logo's alt text
    name: str
    # Absolute https URL the sponsor credit links to
    url: str
    # "wordmark": the logo spells the name and is shown alone.
    # "mark": a square logo shown with the name beside it.
    # Anything else in the sitevar is served as "wordmark".
    logo_style: LogoStyle
    # Absolute https URL of a full-color PNG for light backgrounds
    logo_url: Optional[str]
    # Absolute https URL of a white PNG for dark/brand backgrounds
    logo_url_dark: Optional[str]


class ContentType(TypedDict):
    sponsors: List[Sponsor]


def _is_https_url(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("https://")


def _clean_sponsor(entry: Any) -> Optional[Sponsor]:
    if not isinstance(entry, dict):
        return None

    name = entry.get("name")
    url = entry.get("url")
    logo_style = entry.get("logo_style")
    if not isinstance(name, str) or not name.strip():
        return None
    if not _is_https_url(url):
        return None

    # Clients treat unknown styles as wordmark; never emit one
    style: LogoStyle = "mark" if logo_style == "mark" else "wordmark"
    logo_url = entry.get("logo_url")
    logo_url_dark = entry.get("logo_url_dark")
    return Sponsor(
        name=name.strip(),
        url=url,
        logo_style=style,
        logo_url=logo_url if _is_https_url(logo_url) else None,
        logo_url_dark=logo_url_dark if _is_https_url(logo_url_dark) else None,
    )


class PlatinumSponsors(Sitevar[ContentType]):
    @staticmethod
    def key() -> str:
        return "platinum_sponsors"

    @staticmethod
    def description() -> str:
        return (
            "Platinum sponsors credited in the site footer and apps, in display "
            "order (max 3). Each: name, url, logo_style ('wordmark' or 'mark'), "
            "logo_url (PNG for light backgrounds), logo_url_dark (white PNG for "
            "dark backgrounds). URLs must be absolute https."
        )

    @staticmethod
    def default_value() -> ContentType:
        return ContentType(
            sponsors=[
                Sponsor(
                    name="AndyMark",
                    url="https://www.andymark.com/",
                    logo_style="wordmark",
                    logo_url=f"{LOGO_BASE_URL}/andymark-on-light.png",
                    logo_url_dark=f"{LOGO_BASE_URL}/andymark-on-dark.png",
                )
            ]
        )

    @classmethod
    def sponsors(cls) -> List[Sponsor]:
        """
        The configured sponsors, dropping malformed entries (and entries past
        the cap) so a bad edit never breaks a page or API response.
        """
        contents: Any = cls.get()
        entries = contents.get("sponsors") if isinstance(contents, dict) else None
        if not isinstance(entries, list):
            return []

        sponsors: List[Sponsor] = []
        for entry in entries:
            sponsor = _clean_sponsor(entry)
            if sponsor is not None:
                sponsors.append(sponsor)
        return sponsors[:MAX_SPONSORS]
