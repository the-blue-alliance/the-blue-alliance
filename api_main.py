#!/usr/bin/env python
import webapp2

import tba_config

from controllers.api_controller import ApiEventsShow, ApiTeamDetails, ApiTeamsShow,\
                                       ApiEventList, ApiEventDetails, ApiMatchDetails,\
                                       CsvTeamsAll
from controllers.api.api_team_controller import ApiTeamController
from controllers.api.api_event_controller import ApiEventController, ApiEventTeamsController,\
                                                 ApiEventMatchesController


app = webapp2.WSGIApplication([('/api/v1/team/details', ApiTeamDetails),
                               ('/api/v1/teams/show', ApiTeamsShow),
                               ('/api/v1/events/show', ApiEventsShow),
                               ('/api/v1/events/list', ApiEventList),
                               ('/api/v1/event/details', ApiEventDetails),
                               ('/api/v1/match/details', ApiMatchDetails),
                               ('/api/csv/teams/all', CsvTeamsAll),
                               webapp2.Route(r'/api/v2/team/<team_key:>',
                                             ApiTeamController, 
                                             methods=['GET']),
                               webapp2.Route(r'/api/v2/team/<team_key:>/<year:([0-9]*)>',
                                             ApiTeamController,
                                             methods=['GET']),
                               webapp2.Route(r'/api/v2/event/<event_key:>',
                                             ApiEventController,
                                             methods=['GET']),
                               webapp2.Route(r'/api/v2/event/<event_key:>/teams',
                                             ApiEventTeamsController,
                                             methods=['GET']),
                               webapp2.Route(r'/api/v2/event/<event_key:>/matches',
                                             ApiEventMatchesController,
                                             methods=['GET']),
                               ], debug=tba_config.DEBUG)
