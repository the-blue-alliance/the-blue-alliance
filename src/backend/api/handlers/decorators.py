from flask import request
from functools import wraps


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
