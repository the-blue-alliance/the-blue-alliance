import datetime
import hashlib
import logging
from typing import Optional, Set

from flask import abort, jsonify, make_response, request
from pyre_extensions import none_throws

from backend.common.auth import current_user
from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.auth_type import AuthType, WRITE_TYPE_NAMES
from backend.common.consts.event_type import EventType
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
        cls, event_key: EventKey, required_auth_types: Set[AuthType]
    ) -> None:
        event = Event.get_by_id(event_key)
        if not event:
            abort(
                make_response(jsonify({"Error": f"Event {event_key} not found"}), 404)
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
        if user:
            user_has_auth = any(
                cls._validate_auth(auth, event_key, required_auth_types) is None
                for auth in user.api_write_keys
            )
            if user_has_auth:
                return

        # Finally, check for an auth ID/secret passed as headers to the request
        auth_id = request.headers.get("X-TBA-Auth-Id")
        if not auth_id:
            abort(
                make_response(
                    jsonify(
                        {
                            "Error": "Must provide a request header parameter 'X-TBA-Auth-Id'"
                        }
                    ),
                    400,
                ),
            )

        auth_sig = request.headers.get("X-TBA-Auth-Sig")
        if not auth_sig:
            abort(
                make_response(
                    jsonify(
                        {
                            "Error": "Must provide a request header parameter 'X-TBA-Auth-Sig'"
                        }
                    ),
                    400,
                )
            )

        auth = ApiAuthAccess.get_by_id(auth_id)
        expected_sig = cls.compute_auth_signature(
            auth.secret if auth else None, request.path, request.get_data(as_text=True)
        )
        if not auth or expected_sig != auth_sig:
            logging.info(
                "Auth sig: {}, Expected sig: {}".format(auth_sig, expected_sig)
            )
            abort(
                make_response(
                    jsonify({"Error": "Invalid X-TBA-Auth-Id and/or X-TBA-Auth-Sig!"}),
                    401,
                )
            )

        # Checks event key is valid, correct auth types, and expiration
        error = cls._validate_auth(auth, event_key, required_auth_types)
        if error:
            abort(make_response(jsonify({"Error": error}), 401))

    @classmethod
    def _validate_auth(
        cls,
        auth: ApiAuthAccess,
        event_key: EventKey,
        required_auth_types: Set[AuthType],
    ) -> Optional[str]:
        allowed_event_keys = [none_throws(ekey.string_id()) for ekey in auth.event_list]
        if event_key not in allowed_event_keys:
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
