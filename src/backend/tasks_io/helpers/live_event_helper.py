from collections.abc import Generator
from typing import Any

from google.appengine.ext import ndb

from backend.common.futures import TypedFuture
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.special_webcast_helper import SpecialWebcastHelper
from backend.common.models.event import Event
from backend.common.models.keys import EventKey
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
    ) -> Generator[Any, Any, tuple[dict[EventKey, Event], list[TSpecialWebcast]]]:
        week_events = EventHelper.week_events()
        events_by_key: dict[EventKey, Event] = {}

        live_events: list[Event] = []
        webcast_status_futures: list[TypedFuture[None]] = []
        for event in week_events:
            if event.now:
                event._webcast = event.current_webcasts  # Only show current webcasts
                for webcast in event.webcast:
                    webcast_status_futures.append(
                        WebcastOnlineHelper.add_online_status_async(webcast)
                    )
                events_by_key[event.key.id()] = event
            if event.within_a_day:
                live_events.append(event)

        # To get Champ events to show up before they are actually going on
        forced_live_event_keys = ForcedLiveEvents.get()
        forced_live_events = yield ndb.get_multi_async(
            [ndb.Key(Event, ekey) for ekey in forced_live_event_keys]
        )
        for event in forced_live_events:
            if event.webcast:
                for webcast in event.webcast:
                    webcast_status_futures.append(
                        WebcastOnlineHelper.add_online_status_async(webcast)
                    )
            events_by_key[event.key.id()] = event

        special_webcasts: list[TSpecialWebcast] = (
            yield SpecialWebcastHelper.get_special_webcasts_with_online_status_async()
        )

        for webcast in special_webcasts:
            webcast_status_futures.append(
                WebcastOnlineHelper.add_online_status_async(webcast)
            )

        yield webcast_status_futures

        # # Add in the Fake TBA BlueZone event (watch for circular imports)
        # from helpers.bluezone_helper import BlueZoneHelper
        # bluezone_event = BlueZoneHelper.update_bluezone(live_events)
        # if bluezone_event:
        #     for webcast in bluezone_event.webcast:
        #         WebcastOnlineHelper.add_online_status_async(webcast)
        #     events_by_key[bluezone_event.key_name] = bluezone_event

        return (events_by_key, special_webcasts)
