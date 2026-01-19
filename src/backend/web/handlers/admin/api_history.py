import os
from typing import Any, Dict, List, Optional

from flask import abort
from google.appengine.api.blobstore import blobstore_stub

from backend.common.consts.fms_report_type import FMSReportType
from backend.common.environment import Environment
from backend.common.helpers.fms_companion_helper import FMSCompanionHelper
from backend.common.helpers.fms_report_helper import FMSReportHelper
from backend.common.models.event import Event
from backend.common.models.keys import EventKey
from backend.common.storage import get_files
from backend.web.profiled_render import render_template


def api_history(event_key: EventKey) -> str:
    """
    Display API response history for an event from Cloud Storage.
    Shows FRC API, FMS Reports, and Companion DB tabs.
    """
    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    # Get FRC API histories for various endpoints (uses default project bucket)
    frc_api_data = {
        "alliances": _get_storage_files(
            event, f"frc-api-response/v3.0/{event.year}/alliances/{event.event_short}/"
        ),
        "event_details": _get_storage_files(
            event,
            f"frc-api-response/v3.0/{event.year}/events?eventCode={event.event_short}/",
        ),
        "schedule_qual": _get_storage_files(
            event,
            f"frc-api-response/v3.0/{event.year}/schedule/{event.event_short}/qual/hybrid/",
        ),
        "schedule_playoff": _get_storage_files(
            event,
            f"frc-api-response/v3.0/{event.year}/schedule/{event.event_short}/playoff/hybrid/",
        ),
        "scores_qual": _get_storage_files(
            event,
            f"frc-api-response/v3.0/{event.year}/scores/{event.event_short}/qual/",
        ),
        "scores_playoff": _get_storage_files(
            event,
            f"frc-api-response/v3.0/{event.year}/scores/{event.event_short}/playoff/",
        ),
        "awards": _get_storage_files(
            event,
            f"frc-api-response/v3.0/{event.year}/awards/event/{event.event_short}/",
        ),
    }

    # Get FMS Reports from eventwizard-fms-reports bucket
    fms_reports_bucket = FMSReportHelper.get_bucket()
    fms_reports_data = {
        "team_list": _get_storage_files(
            event,
            FMSReportHelper.get_storage_dir(event_key, FMSReportType.TEAM_LIST),
            fms_reports_bucket,
        ),
        "qual_schedule": _get_storage_files(
            event,
            FMSReportHelper.get_storage_dir(event_key, FMSReportType.QUAL_SCHEDULE),
            fms_reports_bucket,
        ),
        "playoff_schedule": _get_storage_files(
            event,
            FMSReportHelper.get_storage_dir(event_key, FMSReportType.PLAYOFF_SCHEDULE),
            fms_reports_bucket,
        ),
        "qual_results": _get_storage_files(
            event,
            FMSReportHelper.get_storage_dir(event_key, FMSReportType.QUAL_RESULTS),
            fms_reports_bucket,
        ),
        "playoff_results": _get_storage_files(
            event,
            FMSReportHelper.get_storage_dir(event_key, FMSReportType.PLAYOFF_RESULTS),
            fms_reports_bucket,
        ),
        "qual_rankings": _get_storage_files(
            event,
            FMSReportHelper.get_storage_dir(event_key, FMSReportType.QUAL_RANKINGS),
            fms_reports_bucket,
        ),
        "playoff_alliances": _get_storage_files(
            event,
            FMSReportHelper.get_storage_dir(event_key, FMSReportType.PLAYOFF_ALLIANCES),
            fms_reports_bucket,
        ),
    }

    # Get FMS Companion DB from eventwizard-fms-companion bucket
    companion_db_data = _get_storage_files(
        event,
        FMSCompanionHelper.get_storage_dir(event_key),
        FMSCompanionHelper.get_bucket(),
    )

    template_values = {
        "event": event,
        "frc_api_data": frc_api_data,
        "fms_reports_data": fms_reports_data,
        "companion_db_data": companion_db_data,
    }

    return render_template("admin/api_history.html", template_values)


def _get_storage_files(
    event: Event, gcs_path: str, bucket: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get files from Cloud Storage for a given path and bucket.

    Args:
        event: Event model instance
        gcs_path: GCS directory path
        bucket: Storage bucket name (optional, defaults to project bucket)

    Returns:
        List of file metadata dicts with timestamp, filename, path, and public_url
    """
    # Use project bucket if not specified
    if bucket is None:
        bucket = f"{Environment.project()}.appspot.com"

    try:
        file_paths = get_files(gcs_path, bucket=bucket)
        import logging

        logging.info(f"File paths: {file_paths}")
        files = []

        for file_path in file_paths:
            # Extract filename from full path
            filename = file_path.split("/")[-1]

            # Extract timestamp from filename
            # Two formats:
            # 1. FRC API: "2020-03-15 10:30:00.json" -> timestamp is basename without extension
            # 2. FMS Reports: "team_list.2020-03-14T08:00:00.xlsx" -> timestamp is middle part
            parts = filename.split(".")
            if len(parts) >= 3:
                # FMS format: name.timestamp.extension
                # timestamp is everything between first and last part
                timestamp = ".".join(parts[1:-1])
            else:
                # FRC API format: timestamp.extension
                timestamp = os.path.splitext(filename)[0]

            # Generate URL based on environment
            if Environment.is_dev():
                # For dev server, use local blobstore URL
                gcs_filename = f"{bucket}/{file_path}"
                blobkey = (
                    blobstore_stub.BlobstoreServiceStub.CreateEncodedGoogleStorageKey(
                        gcs_filename
                    )
                )
                public_url = (
                    f"http://localhost:8000/blobstore/blob/{blobkey}?display=inline"
                )
            else:
                # For production, use public GCS URL
                public_url = f"https://storage.googleapis.com/{bucket}/{file_path}"

            files.append(
                {
                    "timestamp": timestamp,
                    "filename": filename,
                    "path": file_path,
                    "public_url": public_url,
                }
            )

        # Sort by timestamp (descending order, newest first)
        files.sort(key=lambda x: x["timestamp"], reverse=True)
        return files
    except Exception as e:
        # Log error but return empty list so page still renders
        import logging

        logging.exception(
            f"Error fetching files from {bucket}/{gcs_path} for {event.event_short}: {e}"
        )
        return []
