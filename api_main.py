#!/usr/bin/env python
import os
import webapp2

import tba_config

from controllers.api_controller import ApiEventsShow, ApiTeamDetails, ApiTeamsShow, ApiEventList, ApiEventDetails

app = webapp2.WSGIApplication([('/api/v1/team/details', ApiTeamDetails),
                               ('/api/v1/teams/show', ApiTeamsShow),
                               ('/api/v1/events/show', ApiEventsShow),
                               ('/api/v1/events/list', ApiEventList),
                               ('/api/v1/event/details', ApiEventDetails),
                               ],
                               debug=tba_config.DEBUG)
