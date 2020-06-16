from functools import wraps

from flask import request

from backend.common.models.event import Event
from backend.common.models.team import Team
from backend.common.queries.exceptions import DoesNotExistException


def api_authenticated(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # TODO: Validate with database
        auth_key = request.headers.get(
            "X-TBA-Auth-Key", request.args.get("X-TBA-Auth-Key")
        )
        if not auth_key:
            return (
                {
                    "Error": "X-TBA-Auth-Key is a required header or URL param. Please get an access key at http://www.thebluealliance.com/account.",
                },
                401,
            )
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
