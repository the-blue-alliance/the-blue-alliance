"""Tasks of the predictions_v2 pipeline (see helpers/predictions_v2/pipeline.py).

The enqueue routes run on py3-tasks-cpu-enqueue and only check whether there is work, so
the cron does not wake the py3-tasks-cpu instance when nothing changed. The do routes run
on py3-tasks-cpu, one at a time on the predictions-v2 queue.
"""

import logging
import time
from html import escape
from typing import Optional

from flask import Blueprint, make_response, request, url_for
from google.appengine.api import taskqueue
from werkzeug.wrappers import Response

from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.predictions_v2 import pipeline
from backend.common.helpers.predictions_v2.model.config import DEFAULT_CONFIG
from backend.common.helpers.predictions_v2.model.predictor import model_fingerprint
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.keys import Year
from backend.common.queries.event_query import EventListQuery
from backend.common.sitevars.predictions_v2_config import PredictionsV2Config

blueprint = Blueprint("predictions_v2", __name__)

QUEUE = "predictions-v2"
ADVANCE_BUCKET_SECONDS = 120


def _add_task(url: str, name: Optional[str] = None) -> bool:
    """Enqueue on the predictions-v2 queue. A named task that already exists is skipped."""
    try:
        taskqueue.add(
            url=url,
            method="GET",
            target="py3-tasks-cpu",
            queue_name=QUEUE,
            name=name,
        )
        return True
    except (taskqueue.TaskAlreadyExistsError, taskqueue.TombstonedTaskError):
        return False


def _request_rebuild() -> None:
    """Rebuild every season from the first, once per model version."""
    _add_task(
        url_for("predictions_v2.do_rebuild", season=pipeline.FIRST_SEASON, chain=1),
        name=f"predictions_v2_rebuild_{model_fingerprint(DEFAULT_CONFIG)}",
    )


@blueprint.route("/backend-tasks-b2/enqueue/math/predictions_v2/advance")
def enqueue_advance() -> Response:
    if not PredictionsV2Config.enabled():
        return make_response("predictions_v2 is disabled")
    seasons = sorted(
        {e.year for e in EventHelper.events_within_a_day() if pipeline.needs_update(e)}
    )
    bucket = int(time.time()) // ADVANCE_BUCKET_SECONDS
    for season in seasons:
        _add_task(
            url_for("predictions_v2.do_advance", season=season),
            name=f"predictions_v2_advance_{season}_{bucket}",
        )
    return make_response(f"enqueued predictions_v2 advance for {seasons}")


@blueprint.route("/backend-tasks-b2/do/math/predictions_v2/advance/<int:season>")
def do_advance(season: Year) -> Response:
    if not PredictionsV2Config.enabled():
        return make_response("predictions_v2 is disabled")
    events = [e for e in EventHelper.events_within_a_day() if e.year == season]
    try:
        written = pipeline.advance(season, events)
    except pipeline.NeedsRebuild as e:
        logging.warning(f"predictions_v2: {e}")
        _request_rebuild()
        return make_response(f"needs rebuild: {escape(str(e))}")
    return make_response(f"advanced {season}: {sorted(written)}")


@blueprint.route("/backend-tasks-b2/enqueue/math/predictions_v2/reconcile/<int:season>")
@blueprint.route(
    "/backend-tasks-b2/enqueue/math/predictions_v2/reconcile",
    defaults={"season": None},
)
def enqueue_reconcile(season: Optional[Year]) -> Response:
    if not PredictionsV2Config.enabled():
        return make_response("predictions_v2 is disabled")
    season = season or SeasonHelper.get_current_season()
    _add_task(url_for("predictions_v2.do_reconcile", season=season))
    return make_response(f"enqueued predictions_v2 reconcile for {season}")


@blueprint.route("/backend-tasks-b2/do/math/predictions_v2/reconcile/<int:season>")
def do_reconcile(season: Year) -> Response:
    """Check every event of the season, to catch late results and corrections."""
    if not PredictionsV2Config.enabled():
        return make_response("predictions_v2 is disabled")
    try:
        written = pipeline.advance(season, EventListQuery(year=season).fetch())
    except pipeline.NeedsRebuild as e:
        logging.warning(f"predictions_v2: {e}")
        _request_rebuild()
        return make_response(f"needs rebuild: {escape(str(e))}")
    return make_response(f"reconciled {season}: {len(written)} events written")


@blueprint.route("/backend-tasks-b2/enqueue/math/predictions_v2/rebuild/<int:season>")
def enqueue_rebuild(season: Year) -> Response:
    """Admin: rebuild a season (?chain=1 also rebuilds every later season)."""
    chain = 1 if request.args.get("chain") == "1" else 0
    _add_task(url_for("predictions_v2.do_rebuild", season=season, chain=chain))
    return make_response(f"enqueued predictions_v2 rebuild of {season} (chain={chain})")


@blueprint.route("/backend-tasks-b2/do/math/predictions_v2/rebuild/<int:season>")
def do_rebuild(season: Year) -> Response:
    if not PredictionsV2Config.enabled():
        return make_response("predictions_v2 is disabled")
    pipeline.rebuild(season)
    if request.args.get("chain") == "1" and season < SeasonHelper.get_max_year():
        _add_task(url_for("predictions_v2.do_rebuild", season=season + 1, chain=1))
    return make_response(f"rebuilt {season}")
