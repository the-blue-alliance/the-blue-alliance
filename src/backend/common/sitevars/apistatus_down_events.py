from typing import List

from backend.common.models.keys import EventKey
from backend.common.sitevars.sitevar import Sitevar


class ApiStatusDownEvents(Sitevar[List[EventKey]]):
    @staticmethod
    def key() -> str:
        return "apistatus.down_events"

    @staticmethod
    def description() -> str:
        return "A list of down event keys"

    @staticmethod
    def default_value() -> List[EventKey]:
        return []
