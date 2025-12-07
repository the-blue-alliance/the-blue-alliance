# Eventwizard Internal API
from flask import Blueprint
from flask_cors import CORS

from backend.api.handlers.eventwizard_internal import add_fms_report_archive

# Eventwizard Internal API
eventwizard_api = Blueprint("eventwizard_api", __name__, url_prefix="/_eventwizard/")
CORS(
    eventwizard_api,
    origins="*",
    methods=["OPTIONS", "POST"],
    allow_headers=["Content-Type", "X-TBA-Auth-Id", "X-TBA-Auth-Sig"],
)

eventwizard_api.add_url_rule(
    "/event/<string:event_key>/fms_reports/<string:report_type>",
    methods=["POST"],
    view_func=add_fms_report_archive,
)
