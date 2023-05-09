from typing import Optional

from flask import request

from backend.common.auth import verify_id_token
from backend.common.models.user import User


class ClientApiAuthHelper:
    @staticmethod
    def get_current_user() -> Optional[User]:
        auth_header = request.headers.get("Authorization")
        bearer_token_prefix = "Bearer "
        if not auth_header or not auth_header.startswith(bearer_token_prefix):
            return None

        id_token = auth_header[len(bearer_token_prefix) :]
        decoded_token = verify_id_token(id_token)
        return User(decoded_token) if decoded_token is not None else None
