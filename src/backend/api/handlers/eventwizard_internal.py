import logging
from io import BytesIO
from pathlib import Path

from flask import make_response, request, Response
from openpyxl import load_workbook
from pyre_extensions import none_throws

from backend.api.handlers.decorators import require_write_auth, validate_keys
from backend.api.handlers.helpers.profiled_jsonify import profiled_jsonify
from backend.common.auth import current_user
from backend.common.cloudrun import get_job_status, start_job
from backend.common.consts.auth_type import AuthType
from backend.common.helpers.fms_companion_helper import FMSCompanionHelper
from backend.common.helpers.fms_report_helper import FMSReportHelper
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.keys import EventKey


@require_write_auth(None, file_param="reportFile")
@validate_keys
def add_fms_report_archive(event_key: EventKey, report_type: str) -> Response:
    form_data = request.files.get("reportFile")
    if not form_data:
        return make_response(profiled_jsonify({"Error": "Missing report file"}), 400)

    file_contents: bytes = form_data.read()

    try:
        workbook = load_workbook(filename=BytesIO(file_contents))
        mtime = workbook.properties.modified
    except Exception:
        logging.exception("Failed to parse uploaded Excel file")
        return make_response(
            profiled_jsonify({"Error": "Uploaded file is not a valid Excel file"}), 400
        )

    filename = Path(form_data.filename or "fms_report.xlsx")

    user = current_user()
    FMSReportHelper.write_report(
        event_key,
        report_type,
        file_contents,
        filename=str(filename),
        mtime=mtime,
        content_type=none_throws(form_data.content_type),
        metadata={
            "X-TBA-Auth-User": str(user.uid) if user else None,
            "X-TBA-Auth-User-Email": user.email if user else None,
            "X-TBA-Auth-Id": request.headers.get("X-TBA-Auth-Id"),
        },
    )

    return profiled_jsonify({"Success": "FMS report successfully uploaded"})


@require_write_auth({AuthType.EVENT_TEAMS}, file_param="companionDb")
@validate_keys
def add_fms_companion_db(event_key: EventKey) -> Response:
    form_data = request.files.get("companionDb")
    if not form_data:
        return make_response(
            profiled_jsonify({"Error": "Missing FMS Companion database file"}), 400
        )

    file_contents: bytes = form_data.read()

    # Basic validation - check if it's a valid SQLite database file
    # SQLite databases start with "SQLite format 3\x00"
    if not file_contents.startswith(b"SQLite format 3"):
        logging.warning("Uploaded file does not appear to be a valid SQLite database")
        return make_response(
            profiled_jsonify({"Error": "Uploaded file is not valid"}),
            400,
        )

    newest_db_contents = FMSCompanionHelper.read_newest_companion_db(event_key)
    if newest_db_contents == file_contents:
        newest_file_path = FMSCompanionHelper.get_newest_file_path(event_key)
        storage_path = (
            f"{FMSCompanionHelper.get_bucket()}/{newest_file_path}"
            if newest_file_path
            else ""
        )
    else:
        filename = Path(form_data.filename or "fms_companion.db")

        user = current_user()
        storage_path = FMSCompanionHelper.write_companion_db(
            event_key,
            file_contents,
            filename=str(filename),
            content_type=none_throws(form_data.content_type),
            metadata={
                "X-TBA-Auth-User": str(user.uid) if user else None,
                "X-TBA-Auth-User-Email": user.email if user else None,
                "X-TBA-Auth-Id": request.headers.get("X-TBA-Auth-Id"),
            },
        )
        storage_path = FMSCompanionHelper.get_bucket() + "/" + storage_path

    # Trigger Cloud Run job for companion database import
    job_name = "tba-offseason-companion-import"
    auth_id = request.headers.get("X-TBA-Auth-Id")
    auth = ApiAuthAccess.get_by_id(auth_id) if auth_id else None
    if auth and auth_id and auth.secret:
        execution_id = start_job(
            job_name,
            args=[f"gs://{storage_path}"],
            env={
                "TBA_TRUSTED_AUTH_ID": auth_id,
                "TBA_TRUSTED_AUTH_SECRET": auth.secret,
            },
        )
        job_params = {
            "job_name": job_name,
            "execution_id": execution_id,
        }
    else:
        job_params = {}
        logging.warning(
            "No X-TBA-Auth-Id header provided, skipping Cloud Run job start"
        )

    return profiled_jsonify(
        {
            "Success": "FMS Companion database successfully uploaded",
            "storage_path": storage_path,
            **job_params,
        }
    )


@require_write_auth({AuthType.EVENT_TEAMS})
def get_cloudrun_job_status(
    event_key: EventKey, job_name: str, execution_id: str
) -> Response:
    """Get the status of a Cloud Run job execution.

    Args:
        job_name: The name of the Cloud Run job.
        execution_id: The execution ID.

    Returns:
        JSON response with the job status.
    """
    try:
        status = get_job_status(job_name, execution_id)
        if status is None:
            return make_response(
                profiled_jsonify({"Error": "Job execution not found"}), 404
            )
        return profiled_jsonify({"status": status})
    except Exception as e:
        logging.exception("Failed to fetch Cloud Run job status")
        return make_response(
            profiled_jsonify({"Error": f"Failed to fetch job status: {str(e)}"}), 500
        )
