from datetime import datetime, timezone
from typing import Dict, Optional


def render_time_context_processor() -> Dict[str, Optional[datetime]]:
    return dict(
        render_time=datetime.now(timezone.utc).astimezone().replace(second=0, microsecond=0)  # pyre-ignore[16]
    )  # Prevent ETag from changing too quickly
