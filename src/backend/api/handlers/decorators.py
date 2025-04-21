import json
from functools import wraps
from typing import Callable, Set, Type, TypeVar

from flask import g, jsonify, request, Response

from backend.api.client_api_types import VoidRequest
from backend.api.trusted_api_auth_helper import TrustedApiAuthHelper
from backend.common.auth import current_user
from backend.common.consts.auth_type import AuthType
from backend.common.consts.event_code_exceptions import EventCodeExceptions
from backend.common.consts.renamed_districts import RenamedDistricts
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.team import Team
from backend.common.profiler import Span


def api_authenticated(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        with Span("api_authenticated"):
            auth_key = request.headers.get(
                "X-TBA-Auth-Key", request.args.get("X-TBA-Auth-Key")
            )

            auth_owner_id = None

            if auth_key:
                auth = ApiAuthAccess.get_by_id(auth_key)
                if auth:
                    auth_owner_id = auth.owner.id() if auth.owner else None
                else:
                    return (
                        {
                            "Error": "X-TBA-Auth-Key is invalid. Please get an access key at http://www.thebluealliance.com/account."
                        },
                        401,
                    )
            else:
                user = current_user()
                if user:
                    auth_owner_id = user.account_key.id()
                else:
                    return (
                        {
                            "Error": "X-TBA-Auth-Key is a required header or URL param. Please get an access key at http://www.thebluealliance.com/account."
                        },
                        401,
                    )

            # Set for our GA event tracking in `track_call_after_response`
            g.auth_owner_id = auth_owner_id

        return func(*args, **kwargs)

    return decorated_function


def require_write_auth(auth_types: Set[AuthType]):
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            with Span("require_write_auth"):
                event_key = kwargs["event_key"]

                # This will abort the request on failure
                TrustedApiAuthHelper.do_trusted_api_auth(event_key, auth_types)
            return func(*args, **kwargs)

        return decorated_function

    return decorator


T = TypeVar("T")
R = TypeVar("R")


def client_api_method(
    req_type: Type[T], resp_type: Type[R]
) -> Callable[[Callable[[T], R]], Callable[..., Response]]:
    """
    This is a decorator to apply JSON request/response models
    to the API methods
    """

    def decorator(func: Callable[[T], R]) -> Callable[..., Response]:
        @wraps(func)
        def decorated_function(*args, **kwargs) -> Response:
            data = request.get_data()
            if data:
                req = json.loads(data)
            else:
                req = VoidRequest()

            resp = func(req)
            return jsonify(resp)

        return decorated_function

    return decorator


def validate_keys(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        with Span("validate_keys"):
            # Check key format
            team_key = kwargs.get("team_key")
            if team_key and not Team.validate_key_name(team_key):
                return {"Error": f"{team_key} is not a valid team key"}, 404

            event_key = kwargs.get("event_key")
            if event_key and not Event.validate_key_name(event_key):
                return {"Error": f"{event_key} is not a valid event key"}, 404

            match_key = kwargs.get("match_key")
            if match_key and not Match.validate_key_name(match_key):
                return {"Error": f"{match_key} is not a valid match key"}, 404

            district_key = kwargs.get("district_key")
            if district_key and not District.validate_key_name(district_key):
                return {"Error": f"{district_key} is not a valid district key"}, 404

            # Check key existence
            team_future = None
            if team_key:
                team_future = Team.get_by_id_async(team_key)

            event_future = None
            if event_key:
                event_key = EventCodeExceptions.resolve(event_key)
                event_future = Event.get_by_id_async(event_key)

            match_future = None
            if match_key:
                match_future = Match.get_by_id_async(match_key)

            district_exists_future = None
            if district_key:
                district_exists_future = RenamedDistricts.district_exists_async(
                    district_key
                )

            if team_future is not None and not team_future.get_result():
                return {"Error": f"team key: {team_key} does not exist"}, 404

            if event_future is not None and not event_future.get_result():
                return {"Error": f"event key: {event_key} does not exist"}, 404

            if match_future is not None and not match_future.get_result():
                return {"Error": f"match key: {match_key} does not exist"}, 404

            if (
                district_exists_future is not None
                and not district_exists_future.get_result()
            ):
                return {"Error": f"district key: {district_key} does not exist"}, 404

        return func(*args, **kwargs)

    return decorated_function
