from typing import Any, Optional

DELIMITER: bytes
DEFAULT_TIMEOUT_SECS: Any

def generate_token(key: Any, user_id: Any, action_id: str = ..., when: Optional[Any] = ...): ...
def validate_token(key: Any, token: Any, user_id: Any, action_id: str = ..., current_time: Optional[Any] = ...): ...
