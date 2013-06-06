import logging

from google.appengine.api import memcache


from controllers.ajax_controller import WebcastHandler
from controllers.event_controller import EventList
from controllers.main_controller import MainCompetitionseasonHandler, GamedayHandler, WebcastsHandler

class MemcacheWebcastFlusher(object):
    @classmethod
    def flush(self):
        flushed = []

        flushed.append(MainCompetitionseasonHandler().cacheFlush())
        flushed.append(GamedayHandler().cacheFlush())
        flushed.append(WebcastsHandler().cacheFlush())
        flushed.append(EventList().cacheFlush())

        return flushed

    @classmethod
    def flushEvent(self, event_key):
        flushed = self.flush()
        flushed.append(WebcastHandler().cacheFlush(event_key))
        return flushed