from datetime import datetime, timezone


def render_time_context_processor() -> dict[str, datetime | None]:
    return dict(
        render_time=datetime.now(timezone.utc)  # pyre-ignore[16]
        .astimezone(timezone.utc)
        .replace(second=0, microsecond=0)
    )  # Prevent ETag from changing too quickly
