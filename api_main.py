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

from controllers.api.api_base_controller import ApiBaseController
from controllers.api.api_team_controller import ApiTeamController

app = webapp2.WSGIApplication([
                                webapp2.Route(r'/api/v2/team/<team_key:>', ApiTeamController, methods=['GET']),
                                webapp2.Route(r'/api/v2/team/<team_key:>/<year:([0-9]*)>', ApiTeamController, methods=['GET']),
                               ],
                               debug=tba_config.DEBUG)
