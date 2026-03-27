import base64
import io
import logging
from datetime import timedelta
from typing import Optional

import requests
from flask import abort, request, Response

from backend.common.consts.media_type import MediaType
from backend.common.decorators import cached_public
from backend.common.environment import Environment
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.media import Media
from backend.common.models.team import Team
from backend.common.sitevars.instagram_api_secret import InstagramApiSecret


def fetch_instagram_oembed_html(
    media_key: str, omitscript: bool = False, hidecaption: bool = False
) -> Optional[str]:
    """Fetch oEmbed HTML for an Instagram post.

    The Instagram oEmbed API no longer returns thumbnail_url (deprecated by Meta
    in 2025), but the html field is still supported and returns a rich embed.
    """
    instagram_url = f"https://www.instagram.com/p/{media_key}/"
    params = {
        "url": instagram_url,
        "access_token": InstagramApiSecret.get()["api_key"],
    }
    if omitscript:
        params["omitscript"] = "true"
    if hidecaption:
        params["hidecaption"] = "true"
    try:
        response = requests.get(
            "https://graph.facebook.com/v25.0/instagram_oembed",
            params=params,
        )
        if response.status_code == 200:
            return response.json().get("html")
        else:
            logging.warning(
                f"Instagram oEmbed call failed ({instagram_url}): "
                f"HTTP {response.status_code}"
            )
    except Exception:
        logging.warning(f"Instagram oEmbed request failed for {media_key}")
    return None


@cached_public(ttl=timedelta(hours=24))
def avatar_png(year: int, team_key: str):
    if not Environment.is_dev() and (
        not request.referrer or ("thebluealliance.com" not in request.referrer)
    ):
        return abort(403)
    if not Team.validate_key_name(team_key):
        return abort(404)
    if year < 2018 or year > SeasonHelper.get_max_year():
        return abort(404)

    avatar = Media.get_by_id(
        Media.render_key_name(MediaType.AVATAR, f"avatar_{year}_{team_key}")
    )
    if not avatar:
        return abort(404)

    image_data = base64.b64decode(avatar.avatar_base64_image)
    image_io = io.BytesIO(image_data)
    return Response(image_io, mimetype="image/png")
