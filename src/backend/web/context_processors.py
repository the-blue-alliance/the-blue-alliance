import datetime
from typing import Dict, Optional


def render_time_context_processor() -> Dict[str, Optional[datetime.datetime]]:
    return dict(
        render_time=datetime.datetime.now().replace(second=0, microsecond=0)
    )  # Prevent ETag from changing too quickly
