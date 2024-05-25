from typing import Any, Dict, Optional, TypedDict


class EventInsights(TypedDict):
    """
    The format here varies by year
    """

    qual: Optional[Dict[str, Any]]
    playoff: Optional[Dict[str, Any]]
