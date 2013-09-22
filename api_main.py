#!/usr/bin/env python
import webapp2

import tba_config

from controllers.api_controller import ApiEventsShow, ApiTeamDetails, ApiTeamsShow,\
                                       ApiEventList, ApiEventDetails, ApiMatchDetails,\
                                       CsvTeamsAll

app = webapp2.WSGIApplication([('/api/v1/team/details', ApiTeamDetails),
                               ('/api/v1/teams/show', ApiTeamsShow),
                               ('/api/v1/events/show', ApiEventsShow),
                               ('/api/v1/events/list', ApiEventList),
                               ('/api/v1/event/details', ApiEventDetails),
                               ('/api/v1/match/details', ApiMatchDetails),
                               ('/api/csv/teams/all', CsvTeamsAll)
                               ],
                               debug=tba_config.DEBUG)

from controllers.api.api_controller import ApiController
from controllers.api.team_controller import TeamController

app = webapp2.WSGIApplication([
                                webapp2.Route(r'/api/v2/team/<team_key:>', TeamController, methods=['GET']),
                                webapp2.Route(r'/api/v2/team/<team_key:>/<year:([0-9]*)>', TeamController, methods=['GET']),
                               ],
                               debug=tba_config.DEBUG)

#app.router.set_dispatcher(ApiController.custom_dispatcher)
