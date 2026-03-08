from typing import Any, Dict, Generator, List, Tuple

from google.appengine.ext import ndb

from backend.common.helpers.special_webcast_helper import SpecialWebcastHelper
from backend.common.models.event import Event
from backend.common.models.keys import EventKey
from backend.common.models.webcast import Webcast
from backend.common.sitevars.forced_live_events import ForcedLiveEvents
from backend.common.sitevars.gameday_special_webcasts import (
    WebcastType as TSpecialWebcast,
)
from backend.common.tasklets import typed_toplevel
from backend.tasks_io.helpers.webcast_online_helper import WebcastOnlineHelper


class LiveEventHelper:
    @classmethod
    @typed_toplevel
    def get_live_events_with_current_webcasts(
        cls,
        week_events: list[Event],
    ) -> Generator[Any, Any, Tuple[Dict[EventKey, Event], List[TSpecialWebcast]]]:
        events_by_key: Dict[EventKey, Event] = {}
        live_events: List[Event] = []
        all_webcasts: List[Webcast] = []

        for event in week_events:
            if event.now:
                event._webcast = event.current_webcasts  # Only show current webcasts
                all_webcasts.extend(event.webcast)
                events_by_key[event.key_name] = event
            if event.within_a_day:
                live_events.append(event)

        # To get Champ events to show up before they are actually going on
        forced_live_event_keys = ForcedLiveEvents.get()
        forced_live_events = yield ndb.get_multi_async(
            [ndb.Key(Event, ekey) for ekey in forced_live_event_keys]
        )
        for event in forced_live_events:
            if event.webcast:
                all_webcasts.extend(event.webcast)
            events_by_key[event.key_name] = event

        special_webcasts: List[TSpecialWebcast] = (
            yield SpecialWebcastHelper.get_special_webcasts_with_online_status_async()
        )

        all_webcasts.extend(special_webcasts)

        # Batch process all webcasts together for efficiency
        if all_webcasts:
            yield WebcastOnlineHelper.add_online_status_batch_async(all_webcasts)

        # # Add in the Fake TBA BlueZone event (watch for circular imports)
        # from helpers.bluezone_helper import BlueZoneHelper
        # bluezone_event = BlueZoneHelper.update_bluezone(live_events)
        # if bluezone_event:
        #     yield WebcastOnlineHelper.add_online_status_batch_async(
        #         bluezone_event.webcast
        #     )
        #     events_by_key[bluezone_event.key_name] = bluezone_event

        return (events_by_key, special_webcasts)
