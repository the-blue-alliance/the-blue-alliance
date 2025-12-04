from typing import Any, TypedDict


class EventInsights(TypedDict):
    """
    The format here varies by year
    """

    qual: dict[str, Any] | None
    playoff: dict[str, Any] | None
