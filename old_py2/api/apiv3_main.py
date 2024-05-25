#!/usr/bin/env python
import tba_config
import webapp2

from api.apiv3.api_admin_controller import ApiAdminSetBuildInfo
from api.apiv3.api_base_controller import handle_404
from api.apiv3 import api_realtime_controller as arc
from api.apiv3 import api_suggest_controller as asgc

# Ensure that APIv3 routes include OPTIONS method for CORS preflight compatibility
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Access_control_CORS#Preflighted_requests
app = webapp2.WSGIApplication([
    # Team Media Suggestions
    webapp2.Route(r'/api/v3/suggest/media/team/<team_key:>/<year:([0-9]+)>',
        asgc.ApiSuggestTeamMediaController, methods=['POST', 'OPTIONS']),
    # Event
    webapp2.Route(r'/api/v3/event/<event_key:>/matches/timeseries',
        arc.ApiRealtimeEventMatchesController, methods=['GET', 'OPTIONS']),
    # Match
    webapp2.Route(r'/api/v3/match/<match_key:>/timeseries',
        arc.ApiRealtimeMatchController, methods=['GET', 'OPTOINS']),
    # "Internal" Admin API
    webapp2.Route(r'/api/v3/_/build', ApiAdminSetBuildInfo, methods=['POST', 'OPTIONS'])
], debug=tba_config.DEBUG)
app.error_handlers[404] = handle_404
