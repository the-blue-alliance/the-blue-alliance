import logging
from typing import Optional

from flask import request

from backend.common.auth import verify_id_token
from backend.common.models.user import User

logger = logging.getLogger(__name__)


class ClientApiAuthHelper:
    @staticmethod
    def get_current_user() -> Optional[User]:
        auth_header = request.headers.get("Authorization")
        bearer_token_prefix = "Bearer "
        if not auth_header or not auth_header.startswith(bearer_token_prefix):
            return None

        id_token = auth_header[len(bearer_token_prefix) :]
        decoded_token = verify_id_token(id_token)
        if decoded_token is None:
            logger.warning("[CLIENT_API_AUTH] Token verification failed")
            return None

        uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        provider = decoded_token.get("firebase", {}).get("sign_in_provider", "unknown")
        if not email:
            logger.warning(
                f"[CLIENT_API_AUTH] Token missing email claim: uid={uid}, provider={provider}"
            )
            return None

        return User(decoded_token)
