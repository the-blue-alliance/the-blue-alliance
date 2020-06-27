from typing import Dict

from typing_extensions import TypedDict


class EventInsights(TypedDict):
    """
    The format here varies by year
    """

    qual: Dict
    playoff: Dict
