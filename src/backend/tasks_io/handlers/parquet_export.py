import io
import logging
from typing import List

import boto3
import pyarrow.parquet as pq
from flask import Blueprint, make_response, render_template, request, Response
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from backend.common.helpers.parquet_exporter import matches_to_table, teams_to_table
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.event import Event
from backend.common.models.keys import Year
from backend.common.models.match import Match
from backend.common.models.team import Team
from backend.common.sitevars.s3_export_config import S3ExportConfig

logger = logging.getLogger(__name__)

blueprint = Blueprint("parquet_export", __name__)


def _get_s3_client():  # pyre-ignore[3]
    config = S3ExportConfig.get()
    endpoint_url = config.get("endpoint_url") or None
    return boto3.client(
        "s3",
        aws_access_key_id=config["aws_access_key"],
        aws_secret_access_key=config["aws_secret_key"],
        endpoint_url=endpoint_url,
    )


def _upload_parquet(table, s3_path: str) -> None:  # pyre-ignore[2]
    config = S3ExportConfig.get()
    buf = io.BytesIO()
    pq.write_table(table, buf, compression="zstd")
    buf.seek(0)

    client = _get_s3_client()
    client.put_object(
        Bucket=config["s3_bucket_name"],
        Key=s3_path,
        Body=buf.getvalue(),
    )
    logger.info(f"Uploaded {s3_path} ({buf.tell()} bytes)")


@blueprint.route("/tasks/enqueue/parquet_export/dispatch")
def dispatch_parquet_export() -> Response:
    if not S3ExportConfig.is_enabled():
        logger.info("Parquet export is disabled, skipping dispatch")
        return make_response("Export disabled")

    min_year = SeasonHelper.MIN_YEAR
    max_year = SeasonHelper.get_max_year()

    for year in range(min_year, max_year + 1):
        taskqueue.add(
            queue_name="default",
            target="py3-tasks-io",
            url=f"/tasks/do/parquet_export/matches/{year}",
            method="GET",
        )

    # One task for all teams (not year-partitioned)
    taskqueue.add(
        queue_name="default",
        target="py3-tasks-io",
        url="/tasks/do/parquet_export/teams",
        method="GET",
    )

    total_tasks = (max_year - min_year + 1) + 1
    template_values = {
        "min_year": min_year,
        "max_year": max_year,
        "total_tasks": total_tasks,
    }

    if "X-Appengine-Taskname" not in request.headers:
        return make_response(
            render_template(
                "parquet_export_enqueue.html",
                **template_values,
            )
        )

    return make_response("")


@blueprint.route("/tasks/do/parquet_export/matches/<int:year>")
def export_matches_for_year(year: Year) -> Response:
    if not S3ExportConfig.is_enabled():
        return make_response("Export disabled")

    matches: List[Match] = Match.query(Match.year == year).fetch()
    table = matches_to_table(matches)

    s3_path = f"matches/year={year}/data.parquet"
    _upload_parquet(table, s3_path)

    logger.info(f"Exported {len(matches)} matches for {year}")

    if "X-Appengine-Taskname" not in request.headers:
        return make_response(f"Exported {len(matches)} matches for {year}")

    return make_response("")


@blueprint.route("/tasks/do/parquet_export/teams")
def export_teams() -> Response:
    if not S3ExportConfig.is_enabled():
        return make_response("Export disabled")

    teams: List[Team] = Team.query().fetch()
    table = teams_to_table(teams)

    s3_path = "teams/data.parquet"
    _upload_parquet(table, s3_path)

    logger.info(f"Exported {len(teams)} teams")

    if "X-Appengine-Taskname" not in request.headers:
        return make_response(f"Exported {len(teams)} teams")

    return make_response("")
