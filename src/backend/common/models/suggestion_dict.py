from typing import List, Optional

from typing_extensions import TypedDict

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

    year: Optional[Year]
    reference_type: str
    reference_key: str
    default_preferred: bool

    # For event suggestions
    name: str
    start_date: str
    end_date: str
    website: Optional[str]
    address: str
    city: str
    state: str
    country: str
    venue_name: str

    # For apiwrite suggestions
    event_key: str
    affiliation: str
    auth_types: List[AuthType]

    # For webcast suggestions
    webcast_dict: Webcast
    webcast_url: str
    webcast_date: Optional[str]

    # For match videos
    youtube_videos: List[str]

    # For ApiWrite access
    first_code: Optional[str]
