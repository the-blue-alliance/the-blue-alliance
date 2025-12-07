import logging
from io import BytesIO
from pathlib import Path

from flask import make_response, request, Response
from openpyxl import load_workbook
from pyre_extensions import none_throws

from backend.api.handlers.decorators import require_write_auth, validate_keys
from backend.api.handlers.helpers.profiled_jsonify import profiled_jsonify
from backend.common.auth import current_user
from backend.common.models.keys import EventKey
from backend.common.storage import (
    get_files as storage_get_files,
    write as storage_write,
)


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
    file_name = filename.stem
    extension = ".".join(filename.suffixes)

    storage_dir = f"fms_reports/{event_key}/{report_type}"
    storage_file = f"{file_name}.{mtime}{extension}"
    storage_path = f"{storage_dir}/{storage_file}"

    existing_reports = storage_get_files(
        path=storage_dir,
        bucket="eventwizard-fms-reports",
    )
    if not any(
        existing.split("/")[-1] == storage_file for existing in existing_reports
    ):
        user = current_user()
        storage_write(
            storage_path,
            file_contents,
            bucket="eventwizard-fms-reports",
            content_type=none_throws(form_data.content_type),
            metadata={
                "X-TBA-Auth-User": str(user.uid) if user else None,
                "X-TBA-Auth-User-Email": user.email if user else None,
                "X-TBA-Auth-Id": request.headers.get("X-TBA-Auth-Id"),
            },
        )

    return profiled_jsonify({"Success": "FMS report successfully uploaded"})
