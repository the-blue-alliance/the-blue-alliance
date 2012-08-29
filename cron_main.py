#!/usr/bin/env python
import os
import webapp2

import tba_config

from controllers.datafeed_controller import TbaVideosGet, TbaVideosEnqueue
from controllers.datafeed_controller import FmsTeamListGet
from controllers.datafeed_controller import UsfirstEventDetailsEnqueue, UsfirstEventDetailsGet, UsfirstEventListGet
from controllers.datafeed_controller import UsfirstMatchesEnqueue, UsfirstMatchesGet, UsfirstEventRankingsEnqueue, UsfirstEventRankingsGet
from controllers.datafeed_controller import UsfirstAwardsGetEnqueue, UsfirstAwardsGet
from controllers.datafeed_controller import UsfirstTeamGetEnqueue, UsfirstTeamGet, UsfirstTeamsInstantiate

from controllers.datafeed_controller import OprGet, OprGetEnqueue

from controllers.cron_controller import EventTeamUpdate, EventTeamUpdateEnqueue

app = webapp2.WSGIApplication([('/tasks/enqueue/tba_videos', TbaVideosEnqueue),
                               ('/tasks/enqueue/usfirst_event_details/([0-9]*)', UsfirstEventDetailsEnqueue),
                               ('/tasks/enqueue/usfirst_event_rankings/(.*)', UsfirstEventRankingsEnqueue),
                               ('/tasks/enqueue/usfirst_matches/(.*)', UsfirstMatchesEnqueue),
                               ('/tasks/enqueue/usfirst_team_details', UsfirstTeamDetailsEnqueue),
                               ('/tasks/get/fms_team_list', FmsTeamListGet),
                               ('/tasks/get/tba_videos/(.*)', TbaVideosGet),
                               ('/tasks/get/usfirst_event_list/([0-9]*)', UsfirstEventListGet),
                               ('/tasks/get/usfirst_event_details/([0-9]*)/([0-9]*)', UsfirstEventDetailsGet),
                               ('/tasks/get/usfirst_event_rankings/(.*)', UsfirstEventRankingsGet),
                               ('/tasks/get/usfirst_matches/(.*)', UsfirstMatchesGet),
                               ('/tasks/get/usfirst_team_details/(.*)', UsfirstTeamDetailsGet),
                               ('/tasks/get/usfirst_teams_tpids/([0-9]*)', UsfirstTeamsTpidsGet),
                               ('/tasks/eventteam_update_enqueue', EventTeamUpdateEnqueue),
                               ('/tasks/eventteam_update/(.*)', EventTeamUpdate),
                               ('/tasks/tba_videos_get/(.*)', TbaVideosGet),
                               ('/tasks/tba_videos_get_enqueue', TbaVideosGetEnqueue),
                               ('/tasks/usfirst_event_get_enqueue', UsfirstEventGetEnqueue),
                               ('/tasks/usfirst_event_get/(.*)/(.*)', UsfirstEventGet),
                               ('/tasks/usfirst_events_instantiate', UsfirstEventsInstantiate),
                               ('/tasks/usfirst_matches_get_enqueue', UsfirstMatchesGetEnqueue),
                               ('/tasks/usfirst_matches_get/(.*)', UsfirstMatchesGet),
                               ('/tasks/usfirst_awards_get_enqueue', UsfirstAwardsGetEnqueue),
                               ('/tasks/usfirst_awards_get/(.*)', UsfirstAwardsGet),
                               ('/tasks/usfirst_teams_fast_get', UsfirstTeamsFastGet),
                               ('/tasks/usfirst_team_get_enqueue', UsfirstTeamGetEnqueue),
                               ('/tasks/usfirst_team_get/(.*)', UsfirstTeamGet),
                               ('/tasks/usfirst_teams_instantiate', UsfirstTeamsInstantiate),
                               ('/tasks/event_opr_get_enqueue', OprGetEnqueue),
                               ('/tasks/event_opr_get/(.*)', OprGet)
                               ],
                              debug=tba_config.DEBUG)
