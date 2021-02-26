import json
from typing import List, Optional, Union

from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.models.event import Event
from backend.common.models.webcast import Webcast, WebcastType


class EventWebcastAdder:
    @classmethod
    def add_webcast(
        cls, event: Event, webcast: Union[Webcast, List[Webcast]], update: bool = True
    ) -> Event:
        """Takes a webcast dictionary and adds it to an event"""

        if isinstance(webcast, list):
            event.webcast_json = json.dumps(webcast)
        elif event.webcast:
            webcasts = event.webcast
            if webcast in webcasts:
                return event
            else:
                webcasts.append(webcast)
                event.webcast_json = json.dumps(webcasts)
        else:
            event.webcast_json = json.dumps([webcast])
        event._dirty = True

        if update:
            EventManipulator.createOrUpdate(event, auto_union=False)
            # TODO port memcache
            # MemcacheWebcastFlusher.flushEvent(event.key_name)

        return event

    @classmethod
    def remove_webcast(
        cls,
        event: Event,
        index: int,
        webcast_type: WebcastType,
        channel: str,
        file: Optional[str],
    ) -> None:
        webcasts = event.webcast
        if not webcasts or index >= len(webcasts):
            return

        webcast = webcasts[index]
        if (
            webcast_type != webcast.get("type")
            or channel != webcast.get("channel")
            or file != webcast.get("file")
        ):
            return

        webcasts.pop(index)
        event.webcast_json = json.dumps(webcasts)
        EventManipulator.createOrUpdate(event, auto_union=False)

        # TODO port memcache
        # MemcacheWebcastFlusher.flushEvent(event.key_name)
