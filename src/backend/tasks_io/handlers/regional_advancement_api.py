import json
from typing import Optional

from flask import abort, Blueprint, make_response, request, Response

from backend.common.helpers.season_helper import SeasonHelper
from backend.common.manipulators.regional_champs_pool_manipulator import (
    RegionalChampsPoolManipulator,
)
from backend.common.models.keys import Year
from backend.common.models.regional_champs_pool import RegionalChampsPool
from backend.tasks_io.datafeeds.datafeed_regional_advancemnet import (
    DatafeedRegionalAdvancement,
)

blueprint = Blueprint("ra_api", __name__)


@blueprint.route("/tasks/get/regional_advancement/", defaults={"year": None})
@blueprint.route("/tasks/get/regional_advancement/<int:year>")
def get_regional_advancement(year: Optional[Year]) -> Response:
    if year is None:
        year = SeasonHelper.get_current_season()

    if not SeasonHelper.is_valid_regional_pool_year(year):
        abort(400)

    df = DatafeedRegionalAdvancement(year)
    advancement_future = df.cmp_advancement()
    pool_future = RegionalChampsPool.get_or_insert_async(
        RegionalChampsPool.render_key_name(year)
    )

    advancement = advancement_future.get_result()
    pool = pool_future.get_result()

    pool.advancement = advancement
    RegionalChampsPoolManipulator.createOrUpdate(pool)

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            f"Fetched advancement: {json.dumps(advancement, indent=2)}"
        )

    return make_response("")
