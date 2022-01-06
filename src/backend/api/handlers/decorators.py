import logging
from functools import wraps
from typing import Set

from flask import g, request

from backend.api.trusted_api_auth_helper import TrustedApiAuthHelper
from backend.common.auth import current_user
from backend.common.consts.auth_type import AuthType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.team import Team
from backend.common.queries.exceptions import DoesNotExistException


def api_authenticated(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        auth_key = request.headers.get(
            "X-TBA-Auth-Key", request.args.get("X-TBA-Auth-Key")
        )

        auth_owner_id = None
        auth_owner_mechanism = None

        if auth_key:
            auth = ApiAuthAccess.get_by_id(auth_key)
            if auth and auth.is_read_key:
                auth_owner_id = auth.owner.id() if auth.owner else None
                auth_owner_mechanism = f"X-TBA-Auth-Key: {auth_key}"
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
                auth_owner_mechanism = "LOGGED IN"
            else:
                return (
                    {
                        "Error": "X-TBA-Auth-Key is a required header or URL param. Please get an access key at http://www.thebluealliance.com/account."
                    },
                    401,
                )

        logging.info(f"Auth owner: {auth_owner_id}, {auth_owner_mechanism}")
        # Set for our GA event tracking in `track_call_after_response`
        g.auth_owner_id = auth_owner_id

        return func(*args, **kwargs)

    return decorated_function


def require_write_auth(auth_types: Set[AuthType]):
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            event_key = kwargs["event_key"]

            # This will abort the request on failure
            TrustedApiAuthHelper.do_trusted_api_auth(event_key, auth_types)
            return func(*args, **kwargs)

        return decorated_function

    return decorator


def validate_team_key(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        team_key = kwargs["team_key"]
        if not Team.validate_key_name(team_key):
            return {"Error": f"{team_key} is not a valid team key"}, 404

        try:
            return func(*args, **kwargs)
        except DoesNotExistException:
            return {"Error": f"team key: {team_key} does not exist"}, 404

    return decorated_function


def validate_event_key(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        event_key = kwargs["event_key"]
        if not Event.validate_key_name(event_key):
            return {"Error": f"{event_key} is not a valid event key"}, 404

        try:
            return func(*args, **kwargs)
        except DoesNotExistException:
            return {"Error": f"event key: {event_key} does not exist"}, 404

    return decorated_function


def validate_match_key(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        match_key = kwargs["match_key"]
        if not Match.validate_key_name(match_key):
            return {"Error": f"{match_key} is not a valid match key"}, 404

        try:
            return func(*args, **kwargs)
        except DoesNotExistException:
            return {"Error": f"match key: {match_key} does not exist"}, 404

    return decorated_function


def validate_district_key(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        district_key = kwargs["district_key"]
        if not District.validate_key_name(district_key):
            return {"Error": f"{district_key} is not a valid district key"}, 404

        try:
            return func(*args, **kwargs)
        except DoesNotExistException:
            return {"Error": f"district key: {district_key} does not exist"}, 404

    return decorated_function
