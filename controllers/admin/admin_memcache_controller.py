import os

from google.appengine.api import memcache
from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from controllers.event_controller import EventDetail
from controllers.team_controller import TeamDetail, TeamCanonical
from helpers.memcache.memcache_webcast_flusher import MemcacheWebcastFlusher
from models.event import Event

# Main memcache view.


class AdminMemcacheMain(LoggedInHandler):
    def post(self):
        self._require_admin()
        flushed = list()

        if self.request.get("all_keys") == "all_keys":
            memcache.flush_all()
            flushed.append("all memcache values")

        if self.request.get("webcast_keys") == "webcast_keys":
            flushed.append(MemcacheWebcastFlusher.flush())

        if self.request.get('memcache_key') is not "":
            memcache.delete(self.request.get("memcache_key"))
            flushed.append(self.request.get("memcache_key"))

        if self.request.get('event_key') is not "":
            # Clear event page and event teams pages
            event_key = self.request.get('event_key')
            memcache_keys_to_delete = [EventDetail().cache_key.format(event_key)]

            event = Event.get_by_id(event_key)
            for team in event.teams:
                memcache_keys_to_delete.append(
                    TeamDetail().cache_key.format(team.key.id(), event.year)
                )
                memcache_keys_to_delete.append(
                    TeamCanonical().cache_key.format(team.key.id())
                )

            memcache.delete_multi(memcache_keys_to_delete)
            flushed += memcache_keys_to_delete

        if self.request.get('return_url') is not "":
            self.redirect("{}?flushed={}".format(self.request.get('return_url'), flushed))
            return

        self.template_values.update({
            "flushed": flushed,
            "memcache_stats": memcache.get_stats(),
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/memcache_index.html')
        self.response.out.write(template.render(path, self.template_values))

    def get(self):
        self._require_admin()

        self.template_values.update({
            "memcache_stats": memcache.get_stats(),
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/memcache_index.html')
        self.response.out.write(template.render(path, self.template_values))
