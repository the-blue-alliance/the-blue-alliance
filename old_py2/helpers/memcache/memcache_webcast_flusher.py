from controllers.ajax_controller import WebcastHandler
from controllers.event_controller import EventList
from controllers.main_controller import MainChampsHandler, MainCompetitionseasonHandler, MainOffseasonHandler, MainInsightsHandler, \
    WebcastsHandler
from controllers.gameday_controller import GamedayHandler, Gameday2Controller
from helpers.firebase.firebase_pusher import FirebasePusher


class MemcacheWebcastFlusher(object):
    @classmethod
    def flush(self):
        flushed = []

        flushed.append(MainChampsHandler().memcacheFlush())
        flushed.append(MainCompetitionseasonHandler().memcacheFlush())
        flushed.append(MainOffseasonHandler().memcacheFlush())
        flushed.append(MainInsightsHandler().memcacheFlush())
        flushed.append(GamedayHandler().memcacheFlush())
        flushed.append(Gameday2Controller().memcacheFlush())
        flushed.append(WebcastsHandler().memcacheFlush())
        flushed.append(EventList().memcacheFlush())
        FirebasePusher.update_live_events()

        return flushed

    @classmethod
    def flushEvent(self, event_key):
        flushed = self.flush()
        flushed.append(WebcastHandler().memcacheFlush(event_key))
        FirebasePusher.update_live_events()
        return flushed
