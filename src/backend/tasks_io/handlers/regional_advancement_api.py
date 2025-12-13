import json
from dataclasses import asdict
from typing import Optional

from flask import abort, Blueprint, make_response, request, Response, url_for
from google.appengine.api import taskqueue

from backend.common.helpers.season_helper import SeasonHelper
from backend.common.manipulators.regional_champs_pool_manipulator import (
    RegionalChampsPoolManipulator,
)
from backend.common.models.keys import Year
from backend.common.models.regional_champs_pool import RegionalChampsPool
from backend.tasks_io.datafeeds.datafeed_regional_advancement import (
    RegionalChampsAdvancement,
)

blueprint = Blueprint("ra_api", __name__)


@blueprint.route("/tasks/get/regional_advancement/", defaults={"year": None})
@blueprint.route("/tasks/get/regional_advancement/<int:year>")
def get_regional_advancement(year: Optional[Year]) -> Response:
    if year is None:
        year = SeasonHelper.get_current_season()

    if not SeasonHelper.is_valid_regional_pool_year(year):
        abort(400)

    ra_future = RegionalChampsAdvancement(year).fetch_async()
    pool_future = RegionalChampsPool.get_or_insert_async(
        RegionalChampsPool.render_key_name(year)
    )

    ra = ra_future.get_result()
    pool = pool_future.get_result()

    if ra:
        pool.advancement = ra.advancement
        pool.adjustments = ra.adjustments
        RegionalChampsPoolManipulator.createOrUpdate(pool)

        # If adjust points changed, enqueue a rankings update to incorporate them
        taskqueue.add(
            url=url_for("math.regional_champs_pool_rankings_calc", year=year),
            method="GET",
            target="py3-tasks-io",
            queue_name="default",
        )

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            f"Fetched advancement: <pre>{json.dumps(asdict(ra), indent=2)}</pre>"
        )

    return make_response("")
