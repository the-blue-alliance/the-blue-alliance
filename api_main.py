#!/usr/bin/env python
import webapp2

import tba_config

from controllers.api_controller import ApiDeprecatedController, CsvTeamsAll
from controllers.api.api_base_controller import Apiv2DecommissionedController
from controllers.api.api_trusted_controller import ApiTrustedEventAllianceSelectionsUpdate, ApiTrustedEventAwardsUpdate, \
                                                   ApiTrustedEventMatchesUpdate, ApiTrustedEventMatchesDelete, ApiTrustedEventMatchesDeleteAll, ApiTrustedEventRankingsUpdate, \
                                                   ApiTrustedEventTeamListUpdate, ApiTrustedAddMatchYoutubeVideo, \
                                                   ApiTrustedAddEventMedia, ApiTrustedUpdateEventInfo

# Ensure that APIv2 routes include OPTIONS method for CORS preflight compatibility
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Access_control_CORS#Preflighted_requests
app = webapp2.WSGIApplication([webapp2.Route(r'/api/v1/<:.*>',
                                             ApiDeprecatedController,
                                             methods=['GET']),
                               ('/api/csv/teams/all', CsvTeamsAll),
                               webapp2.Route(r'/api/v2/<:.*>',
                                             Apiv2DecommissionedController,
                                             methods=['GET']),
                               webapp2.Route(r'/api/trusted/v1/event/<event_key:>/alliance_selections/update',
                                             ApiTrustedEventAllianceSelectionsUpdate,
                                             methods=['POST', 'OPTIONS']),
                               webapp2.Route(r'/api/trusted/v1/event/<event_key:>/awards/update',
                                             ApiTrustedEventAwardsUpdate,
                                             methods=['POST', 'OPTIONS']),
                               webapp2.Route(r'/api/trusted/v1/event/<event_key:>/matches/update',
                                             ApiTrustedEventMatchesUpdate,
                                             methods=['POST', 'OPTIONS']),
                               webapp2.Route(r'/api/trusted/v1/event/<event_key:>/matches/delete',
                                             ApiTrustedEventMatchesDelete,
                                             methods=['POST', 'OPTIONS']),
                               webapp2.Route(r'/api/trusted/v1/event/<event_key:>/matches/delete_all',
                                             ApiTrustedEventMatchesDeleteAll,
                                             methods=['POST', 'OPTIONS']),
                               webapp2.Route(r'/api/trusted/v1/event/<event_key:>/rankings/update',
                                             ApiTrustedEventRankingsUpdate,
                                             methods=['POST', 'OPTIONS']),
                               webapp2.Route(r'/api/trusted/v1/event/<event_key:>/team_list/update',
                                             ApiTrustedEventTeamListUpdate,
                                             methods=['POST', 'OPTIONS']),
                               webapp2.Route(r'/api/trusted/v1/event/<event_key:>/match_videos/add',
                                             ApiTrustedAddMatchYoutubeVideo,
                                             methods=['POST', 'OPTIONS']),
                               webapp2.Route(r'/api/trusted/v1/event/<event_key:>/media/add',
                                             ApiTrustedAddEventMedia,
                                             methods=['POST', 'OPTIONS']),
                               webapp2.Route(r'/api/trusted/v1/event/<event_key:>/info/update',
                                             ApiTrustedUpdateEventInfo,
                                             methods=['POST', 'OPTIONS']),
                               ], debug=tba_config.DEBUG)
