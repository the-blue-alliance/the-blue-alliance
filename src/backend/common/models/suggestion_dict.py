from typing import TypedDict

from backend.common.consts.auth_type import AuthType
from backend.common.consts.media_type import MediaType
from backend.common.models.keys import Year
from backend.common.models.webcast import Webcast


class SuggestionDict(TypedDict, total=False):
    media_type_enum: MediaType
    profile_url: str
    is_social: bool
    foreign_key: str
    site_name: str
    details_json: str
    private_details_json: str

    year: Year | None
    reference_type: str
    reference_key: str
    default_preferred: bool

    # For event suggestions
    name: str
    start_date: str
    end_date: str
    website: str | None
    address: str
    city: str
    state: str
    country: str
    venue_name: str

    # For apiwrite suggestions
    event_key: str
    affiliation: str
    auth_types: list[AuthType]

    # For webcast suggestions
    webcast_dict: Webcast
    webcast_url: str
    webcast_date: str | None

    # For match videos
    youtube_videos: list[str]

    # For ApiWrite access
    first_code: str | None
