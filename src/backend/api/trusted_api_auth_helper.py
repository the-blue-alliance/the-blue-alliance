import datetime
import hashlib
from typing import Optional

from flask import abort, make_response, request
from pyre_extensions import none_throws

from backend.api.handlers.helpers.profiled_jsonify import profiled_jsonify
from backend.common.auth import current_user
from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.auth_type import AuthType, WRITE_TYPE_NAMES
from backend.common.consts.event_code_exceptions import EventCodeExceptions
from backend.common.consts.event_type import EventType
from backend.common.consts.fms_report_type import (
    FMSReportType,
    REQUIRED_REPORT_PERMISSOINS,
)
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.models.keys import EventKey
from backend.common.sitevars.trusted_api import TrustedApiConfig


class TrustedApiAuthHelper:
    @staticmethod
    def compute_auth_signature(
        auth_secret: Optional[str], request_path: str, request_body: str
    ) -> str:
        to_hash = f"{auth_secret}{request_path}{request_body}"
        return hashlib.md5(to_hash.encode()).hexdigest()

    @classmethod
    def do_trusted_api_auth(
        cls,
        event_key: EventKey,
        fms_report_type: FMSReportType | None,
        required_auth_types: set[AuthType] | None,
        file_param: str | None = None,
    ) -> None:
        event_key = EventCodeExceptions.resolve(event_key)
        event = Event.get_by_id(event_key)
        if not event:
            abort(
                make_response(
                    profiled_jsonify({"Error": f"Event {event_key} not found"}), 404
                )
            )

        # Start by allowing admins to edit any event
        user = current_user()
        user_is_admin = user and user.is_admin
        if user_is_admin:
            return

        # Also grant access if the user has the EVENTWIZARD permission and
        # are making requests for a current year offseason event
        current_year = datetime.datetime.now().year
        user_has_permission = (
            event.event_type_enum == EventType.OFFSEASON
            and event.year == current_year
            and user is not None
            and AccountPermission.OFFSEASON_EVENTWIZARD in (user.permissions or {})
        )
        if user_has_permission:
            return

        # Next, check if the logged in user has any write API keys linked to their account
        # that are valid for this event
        if required_auth_types is None:
            required_auth_types = set()
        if user:
            user_has_auth = any(
                cls._validate_auth(auth, event, required_auth_types) is None
                for auth in user.api_write_keys
            )
            if user_has_auth:
                return

        # Finally, check for an auth ID/secret passed as headers to the request
        auth_id = request.headers.get("X-TBA-Auth-Id")
        if not auth_id:
            abort(
                make_response(
                    profiled_jsonify(
                        {
                            "Error": "Must provide a request header parameter 'X-TBA-Auth-Id'"
                        }
                    ),
                    401,
                ),
            )

        auth_sig = request.headers.get("X-TBA-Auth-Sig")
        if not auth_sig:
            abort(
                make_response(
                    profiled_jsonify(
                        {
                            "Error": "Must provide a request header parameter 'X-TBA-Auth-Sig'"
                        }
                    ),
                    401,
                )
            )

        if file_param:
            file = request.files.get(file_param)
            if not file:
                abort(
                    make_response(
                        profiled_jsonify({"Error": "Expected file upload not found"}),
                        401,
                    )
                )
            file_contents = file.read()
            file.seek(0)
            request_data = hashlib.sha256(file_contents).hexdigest()
            file_digest = request.form.get("fileDigest")
            if request_data != file_digest:
                abort(
                    make_response(
                        profiled_jsonify(
                            {"Error": "File digest does not match uploaded file"}
                        ),
                        401,
                    )
                )

            # Create a new set for file upload auth types to avoid mutating the passed-in set
            required_auth_types = set(required_auth_types)
            if fms_report_type in REQUIRED_REPORT_PERMISSOINS:
                required_auth_types.add(REQUIRED_REPORT_PERMISSOINS[fms_report_type])

            if len(required_auth_types) == 0:
                abort(
                    make_response(
                        profiled_jsonify(
                            {
                                "Error": "Unable to authorize request: no required auth types could be determined."
                            }
                        ),
                        401,
                    )
                )
        else:
            request_data = request.get_data(as_text=True)

        auth = ApiAuthAccess.get_by_id(auth_id)
        expected_sig = cls.compute_auth_signature(
            auth.secret if auth else None, request.path, request_data
        )
        if not auth or expected_sig != auth_sig:
            abort(
                make_response(
                    profiled_jsonify(
                        {"Error": "Invalid X-TBA-Auth-Id and/or X-TBA-Auth-Sig!"}
                    ),
                    401,
                )
            )

        # Checks event key is valid, correct auth types, and expiration
        error = cls._validate_auth(auth, event, required_auth_types)
        if error:
            abort(make_response(profiled_jsonify({"Error": error}), 401))

    @classmethod
    def _validate_auth(
        cls,
        auth: ApiAuthAccess,
        event: Event,
        required_auth_types: set[AuthType],
    ) -> Optional[str]:
        allowed_event_keys = [none_throws(ekey.string_id()) for ekey in auth.event_list]
        if (
            event.key_name not in allowed_event_keys
            and not (
                auth.all_official_events
                and event.official
                and event.year == datetime.datetime.now().year
            )
            and not (
                required_auth_types == {AuthType.MATCH_VIDEO}
                and any(
                    (
                        ApiAuthAccess.webcast_key(w) in auth.offseason_webcast_channels
                        for w in event.webcast
                    )
                )
                and event.event_type_enum == EventType.OFFSEASON
                and event.year == datetime.datetime.now().year
            )
        ):
            return "Only allowed to edit events: {}".format(
                ", ".join(allowed_event_keys)
            )

        missing_auths = required_auth_types.difference(set(auth.auth_types_enum))
        if missing_auths != set():
            return "You do not have permission to edit: {}. If this is incorrect, please contact TBA admin.".format(
                ",".join([WRITE_TYPE_NAMES[ma] for ma in missing_auths])
            )

        expiration = auth.expiration
        if expiration is not None and expiration < datetime.datetime.now():
            return "These keys expired on {}. Contact TBA admin to make changes".format(
                auth.expiration
            )

        if not TrustedApiConfig.is_auth_enalbed(required_auth_types):
            return "The trusted API has been temporarily disabled by the TBA admins. Please contact them for more details."

        return None
