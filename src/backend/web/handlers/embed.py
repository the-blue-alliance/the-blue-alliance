import logging
import urllib.parse
from datetime import timedelta

import requests
from flask import abort, redirect, request

from backend.common.auth import current_user
from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.media_type import MediaType
from backend.common.decorators import cached_public
from backend.common.models.media import Media
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
        if not request.referrer or ("thebluealliance.com" not in request.referrer):
            return abort(403)

        media = Media.get_by_id(
            Media.render_key_name(MediaType.INSTAGRAM_IMAGE, media_key)
        )
        if not media:
            return abort(404)

        instagram_url = media.instagram_url

    width = int(request.args.get("width") or 320)

    response = requests.get(
        "https://graph.facebook.com/v14.0/instagram_oembed"
        + f"?url={urllib.parse.quote_plus(instagram_url)}"
        + f"&maxwidth={width}"
        + f"&access_token={InstagramApiSecret.get()['api_key']}"
    )

    if response.status_code != 200:
        logging.error(f"Instagram oembed call failed: {response.json().get("error")}")
        return abort(500)

    return redirect(response.json()["thumbnail_url"])
