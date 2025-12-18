# Eventwizard Internal API
from flask import Blueprint
from flask_cors import CORS

from backend.api.handlers.eventwizard_internal import (
    add_fms_companion_db,
    add_fms_report_archive,
    get_cloudrun_job_status,
)

# Eventwizard Internal API
eventwizard_api = Blueprint(
    "eventwizard_api", __name__, url_prefix="/api/_eventwizard/"
)
CORS(
    eventwizard_api,
    origins="*",
    methods=["OPTIONS", "GET", "POST"],
    allow_headers=["Content-Type", "X-TBA-Auth-Id", "X-TBA-Auth-Sig"],
)

eventwizard_api.add_url_rule(
    "/event/<string:event_key>/fms_reports/<string:report_type>",
    methods=["POST", "GET"],
    view_func=add_fms_report_archive,
)

eventwizard_api.add_url_rule(
    "/event/<string:event_key>/fms_companion_db",
    methods=["POST"],
    view_func=add_fms_companion_db,
)

eventwizard_api.add_url_rule(
    "/_cloudrun/status/<string:event_key>/<string:job_name>/<string:execution_id>",
    methods=["POST"],
    view_func=get_cloudrun_job_status,
)
