import logging

from google.appengine.api import memcache

from controllers.main_controller import MainCompetitionseasonHandler, GamedayHandler, WebcastsHandler
from controllers.event_controller import EventList

class MemcacheWebcastFlusher(object):
    @classmethod
    def flush(self):
        flushed = []

        flushed.append(MainCompetitionseasonHandler().memcacheFlush())
        flushed.append(GamedayHandler().memcacheFlush())
        flushed.append(WebcastsHandler().memcacheFlush())
        flushed.append(EventList().memcacheFlush())

        return flushed