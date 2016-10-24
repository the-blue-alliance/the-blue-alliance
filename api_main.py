#!/usr/bin/env python
import webapp2

import tba_config

from controllers.api_controller import ApiDeprecatedController, CsvTeamsAll
from controllers.api.api_district_controller import ApiDistrictListController, ApiDistrictTeamsController, ApiDistrictRankingsController, \
     ApiDistrictEventsController
from controllers.api.api_team_controller import ApiTeamController, ApiTeamEventsController, ApiTeamEventAwardsController, \
                                                ApiTeamEventMatchesController, ApiTeamMediaController, ApiTeamListController, \
                                                ApiTeamYearsParticipatedController, ApiTeamHistoryEventsController, \
                                                ApiTeamHistoryAwardsController, ApiTeamHistoryRobotsController, \
    ApiTeamHistoryDistrictsController
from controllers.api.api_event_controller import ApiEventController, ApiEventTeamsController, \
                                                 ApiEventMatchesController, ApiEventStatsController, \
                                                 ApiEventRankingsController, ApiEventAwardsController, \
                                                 ApiEventDistrictPointsController, ApiEventListController
from controllers.api.api_match_controller import ApiMatchController
from controllers.api.api_status_controller import ApiStatusController
from controllers.api.api_trusted_controller import ApiTrustedEventAllianceSelectionsUpdate, ApiTrustedEventAwardsUpdate, \
                                                   ApiTrustedEventMatchesUpdate, ApiTrustedEventMatchesDelete, ApiTrustedEventMatchesDeleteAll, ApiTrustedEventRankingsUpdate, \
                                                   ApiTrustedEventTeamListUpdate, ApiTrustedAddMatchYoutubeVideo


# Ensure that APIv2 routes include OPTIONS method for CORS preflight compatibility
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Access_control_CORS#Preflighted_requests
app = webapp2.WSGIApplication([webapp2.Route(r'/api/v1/<:.*>',
                                             ApiDeprecatedController,
                                             methods=['GET']),
                               ('/api/csv/teams/all', CsvTeamsAll),
                               webapp2.Route(r'/api/v2/team/<team_key:>',
                                             ApiTeamController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/team/<team_key:>/events',
                                             ApiTeamEventsController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/team/<team_key:>/<year:([0-9]*)>/events',
                                             ApiTeamEventsController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/team/<team_key:>/event/<event_key:>/awards',
                                             ApiTeamEventAwardsController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/team/<team_key:>/event/<event_key:>/matches',
                                             ApiTeamEventMatchesController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/team/<team_key:>/media',
                                             ApiTeamMediaController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/team/<team_key:>/<year:([0-9]*)>/media',
                                             ApiTeamMediaController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/team/<team_key:>/history/events',
                                             ApiTeamHistoryEventsController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/team/<team_key:>/history/awards',
                                             ApiTeamHistoryAwardsController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/team/<team_key:>/history/robots',
                                             ApiTeamHistoryRobotsController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/team/<team_key:>/history/districts',
                                             ApiTeamHistoryDistrictsController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/team/<team_key:>/years_participated',
                                             ApiTeamYearsParticipatedController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/teams/<page_num:([0-9]+)>',
                                             ApiTeamListController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/event/<event_key:>',
                                             ApiEventController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/event/<event_key:>/teams',
                                             ApiEventTeamsController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/event/<event_key:>/matches',
                                             ApiEventMatchesController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/event/<event_key:>/stats',
                                             ApiEventStatsController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/event/<event_key:>/rankings',
                                             ApiEventRankingsController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/event/<event_key:>/awards',
                                            ApiEventAwardsController,
                                            methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/event/<event_key:>/district_points',
                                            ApiEventDistrictPointsController,
                                            methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/events/<year:([0-9]*)>',
                                             ApiEventListController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/match/<match_key:>',
                                             ApiMatchController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/districts/<year:([0-9]*)>',
                                             ApiDistrictListController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/district/<district_abbrev:>/<year:([0-9]*)>/events',
                                             ApiDistrictEventsController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/district/<district_abbrev:>/<year:([0-9]*)>/teams',
                                             ApiDistrictTeamsController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/district/<district_abbrev:>/<year:([0-9]*)>/rankings',
                                             ApiDistrictRankingsController,
                                             methods=['GET', 'OPTIONS']),
                               webapp2.Route(r'/api/v2/status',
                                             ApiStatusController,
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
                               ], debug=tba_config.DEBUG)
