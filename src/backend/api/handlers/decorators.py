import logging
from functools import wraps

from flask import g, request

from backend.common.auth import current_user
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
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
