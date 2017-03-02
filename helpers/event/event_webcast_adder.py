import json

from helpers.event_manipulator import EventManipulator
from helpers.memcache.memcache_webcast_flusher import MemcacheWebcastFlusher


class EventWebcastAdder(object):

    @classmethod
    def add_webcast(cls, event, webcast):
        """Takes a webcast dictionary and adds it to an event"""

        if event.webcast:
            webcasts = event.webcast
            if webcast in webcasts:
                return event
            else:
                webcasts.append(webcast)
                event.webcast_json = json.dumps(webcasts)
        else:
            event.webcast_json = json.dumps([webcast])
        event.dirty = True
        EventManipulator.createOrUpdate(event)
        MemcacheWebcastFlusher.flushEvent(event.key_name)

        return event

    @classmethod
    def remove_webcast(cls, event, index, type, channel, file):
        webcasts = event.webcast
        if not webcasts or index >= len(webcasts):
            return

        webcast = webcasts[index]
        if type != webcast.get("type") or channel != webcast.get("channel") or file != webcast.get("file"):
            return

        webcasts.pop(index)
        event.webcast_json = json.dumps(webcasts)
        EventManipulator.createOrUpdate(event)
        MemcacheWebcastFlusher.flushEvent(event.key_name)
