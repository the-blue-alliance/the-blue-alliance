#!/usr/bin/env python
import webapp2

import tba_config

from controllers.datafeed_controller import EventListEnqueue, EventDetailsEnqueue
from controllers.datafeed_controller import EventListGet, EventDetailsGet, TeamDetailsGet


app = webapp2.WSGIApplication([('/backend-tasks/enqueue/event_list/([0-9]*)', EventListEnqueue),
                               ('/backend-tasks/enqueue/event_details/(.*)', EventDetailsEnqueue),
                               ('/backend-tasks/get/event_list/([0-9]*)', EventListGet),
                               ('/backend-tasks/get/event_details/(.*)', EventDetailsGet),
                               ('/backend-tasks/get/team_details/(.*)', TeamDetailsGet),
                               ],
                              debug=tba_config.DEBUG)
