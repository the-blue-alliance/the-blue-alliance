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
from backend.web.profiled_render import render_template


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

    # Validate our user input "width" can be converted to an integer
    try:
        width = int(request.args.get("width") or 320)
    except Exception:
        return abort(400)

    with Span("GET: https://graph.facebook.com/v25.0/instagram_oembed"):
        response = requests.get(
            "https://graph.facebook.com/v25.0/instagram_oembed"
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


def oembed_test():
    access_token = InstagramApiSecret.get()["api_key"]
    instagram_url = "https://www.instagram.com/p/CbAabcyNUda/"
    facebook_url = "https://www.facebook.com/thebluealliance/posts/pfbid0yVvTAw61qYufQZ1Pg288ioN6P3JAfCFMvgs5Cij6d7Ld2xSwVomxKRgR2CHM6bwVl"

    instagram_html = None
    instagram_error = None
    facebook_html = None
    facebook_error = None

    try:
        ig_response = requests.get(
            "https://graph.facebook.com/v25.0/instagram_oembed",
            params={
                "url": instagram_url,
                "access_token": access_token,
            },
        )
        if ig_response.status_code == 200:
            instagram_html = ig_response.json().get("html", "")
        else:
            instagram_error = f"HTTP {ig_response.status_code}: {ig_response.text}"
    except Exception as e:
        instagram_error = str(e)

    try:
        fb_response = requests.get(
            "https://graph.facebook.com/v25.0/oembed_post",
            params={
                "url": facebook_url,
                "access_token": access_token,
            },
        )
        if fb_response.status_code == 200:
            facebook_html = fb_response.json().get("html", "")
        else:
            facebook_error = f"HTTP {fb_response.status_code}: {fb_response.text}"
    except Exception as e:
        facebook_error = str(e)

    return render_template(
        "local/oembed_test.html",
        {
            "instagram_html": instagram_html,
            "instagram_error": instagram_error,
            "facebook_html": facebook_html,
            "facebook_error": facebook_error,
        },
    )


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
