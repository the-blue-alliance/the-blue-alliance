import logging
from typing import List

from flask import Blueprint

from backend.common.consts.media_tag import MediaTag
from backend.common.consts.media_type import MediaType
from backend.common.manipulators.media_manipulator import MediaManipulator
from backend.common.models.media import Media
from backend.tasks_io.datafeeds.datafeed_resource_library import (
    DatafeedResourceLibrary,
)

blueprint = Blueprint("hall_of_fame", __name__)


@blueprint.route("/tasks/get/hof_teams")
def get_hall_of_fame_teams() -> str:
    teams = DatafeedResourceLibrary().get_hall_of_fame_teams()
    if not teams:
        logging.warning("No Hall of Fame teams found")
        return "No Hall of Fame teams found"

    media_to_update: List[Media] = []
    for team in teams:
        team_reference = Media.create_reference("team", team["team_id"])

        for foreign_key, media_type, media_tag in (
            (team["video"], MediaType.YOUTUBE_VIDEO, MediaTag.CHAIRMANS_VIDEO),
            (
                team["presentation"],
                MediaType.YOUTUBE_VIDEO,
                MediaTag.CHAIRMANS_PRESENTATION,
            ),
            (team["essay"], MediaType.EXTERNAL_LINK, MediaTag.CHAIRMANS_ESSAY),
        ):
            if not foreign_key:
                continue
            media_to_update.append(
                Media(
                    id=Media.render_key_name(media_type, foreign_key),
                    media_type_enum=media_type,
                    media_tag_enum=[media_tag],
                    references=[team_reference],
                    year=team["year"],
                    foreign_key=foreign_key,
                )
            )

    MediaManipulator.createOrUpdate(media_to_update)
    return f"Updated {len(media_to_update)} Hall of Fame media items"
