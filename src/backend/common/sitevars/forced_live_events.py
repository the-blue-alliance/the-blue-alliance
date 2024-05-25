from typing import List

from backend.common.models.keys import EventKey
from backend.common.sitevars.sitevar import Sitevar


class ForcedLiveEvents(Sitevar[List[EventKey]]):
    @staticmethod
    def key() -> str:
        return "forced_live_events"

    @staticmethod
    def description() -> str:
        return "To force events to show up in GameDay before they are actually live."

    @staticmethod
    def default_value() -> List[EventKey]:
        return []
