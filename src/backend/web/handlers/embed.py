import base64
import io
from datetime import timedelta

from flask import abort, request, Response

from backend.common.consts.media_type import MediaType
from backend.common.decorators import cached_public
from backend.common.environment import Environment
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.media import Media
from backend.common.models.team import Team


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
