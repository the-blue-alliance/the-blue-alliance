import json

from controllers.base_controller import LoggedInHandler
from template_engine import jinja2_engine

from helpers.event_helper import EventHelper


class BlueZoneDebugHandler(LoggedInHandler):
    def get(self):
        self._require_admin()

        current_events = filter(lambda e: e.now, EventHelper.getEventsWithinADay())

        self.template_values.update({
            'event_keys_json': json.dumps([e.key.id() for e in current_events]),
        })

        self.response.out.write(jinja2_engine.render('bluezone_debug.html', self.template_values))
