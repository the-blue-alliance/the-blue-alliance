import base64
import io
import logging
import urllib.parse
from datetime import timedelta

import requests
from flask import abort, redirect, request, Response

from backend.common.auth import current_user
from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.media_type import MediaType
from backend.common.decorators import cached_public
from backend.common.environment import Environment
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.media import Media
from backend.common.models.team import Team
from backend.common.profiler import Span
from backend.common.sitevars.instagram_api_secret import InstagramApiSecret


@cached_public(ttl=timedelta(hours=6), cache_redirects=True)
def instagram_oembed(media_key: str):
    user = current_user()

    if (
        user
        and user.permissions
        and (AccountPermission.REVIEW_MEDIA in user.permissions)
    ):
        # Skip validation for media reviewers
        instagram_url = f"https://www.instagram.com/p/{media_key}/"
    else:
        if not Environment.is_dev() and (
            not request.referrer or ("thebluealliance.com" not in request.referrer)
        ):
            return abort(403)

        media = Media.get_by_id(
            Media.render_key_name(MediaType.INSTAGRAM_IMAGE, media_key)
        )
        if not media:
            return abort(404)

        instagram_url = media.instagram_url

    width = int(request.args.get("width") or 320)

    with Span("GET: https://graph.facebook.com/v14.0/instagram_oembed"):
        response = requests.get(
            "https://graph.facebook.com/v14.0/instagram_oembed"
            + f"?url={urllib.parse.quote_plus(instagram_url)}"
            + f"&maxwidth={width}"
            + f"&access_token={InstagramApiSecret.get()['api_key']}"
        )

    if response.status_code != 200:
        logging.warning(
            f"Instagram oembed call failed ({instagram_url}): {response.json()}"
        )
        return redirect("/images/instagram_blank.png")

    return redirect(response.json()["thumbnail_url"])


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
