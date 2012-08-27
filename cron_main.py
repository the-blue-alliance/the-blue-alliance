#!/usr/bin/env python
import os
import webapp2

import tba_config

from controllers.datafeed_controller import TbaVideosGet, TbaVideosGetEnqueue
from controllers.datafeed_controller import FmsTeamListGet
from controllers.datafeed_controller import UsfirstEventDetailsEnqueue, UsfirstEventDetailsGet, UsfirstEventListGet
from controllers.datafeed_controller import UsfirstMatchesEnqueue, UsfirstMatchesGet, UsfirstRankingsGetEnqueue, UsfirstRankingsGet
from controllers.datafeed_controller import UsfirstTeamGetEnqueue, UsfirstTeamGet, UsfirstTeamsInstantiate

from controllers.datafeed_controller import OprGet, OprGetEnqueue

from controllers.cron_controller import EventTeamUpdate, EventTeamUpdateEnqueue

app = webapp2.WSGIApplication([('/tasks/enqueue/usfirst_event_details/([0-9]*)', UsfirstEventDetailsEnqueue),
                               ('/tasks/enqueue/usfirst_matches/(.*)', UsfirstMatchesEnqueue),
                               ('/tasks/get/fms_team_list', FmsTeamListGet),
                               ('/tasks/get/usfirst_event_list/([0-9]*)', UsfirstEventListGet),
                               ('/tasks/get/usfirst_event_details/([0-9]*)/([0-9]*)', UsfirstEventDetailsGet),
                               ('/tasks/get/usfirst_matches/(.*)', UsfirstMatchesGet),
                               ('/tasks/eventteam_update_enqueue', EventTeamUpdateEnqueue),
                               ('/tasks/eventteam_update/(.*)', EventTeamUpdate),
                               ('/tasks/tba_videos_get/(.*)', TbaVideosGet),
                               ('/tasks/tba_videos_get_enqueue', TbaVideosGetEnqueue),
                               ('/tasks/usfirst_rankings_get_enqueue', UsfirstRankingsGetEnqueue),
                               ('/tasks/usfirst_rankings_get/(.*)', UsfirstRankingsGet),
                               ('/tasks/usfirst_team_get_enqueue', UsfirstTeamGetEnqueue),
                               ('/tasks/usfirst_team_get/(.*)', UsfirstTeamGet),
                               ('/tasks/usfirst_teams_instantiate', UsfirstTeamsInstantiate),
                               ('/tasks/event_opr_get_enqueue', OprGetEnqueue),
                               ('/tasks/event_opr_get/(.*)', OprGet)
                               ],
                              debug=tba_config.DEBUG)
