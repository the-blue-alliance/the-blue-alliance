#!/usr/bin/env python
import os
import webapp2

import tba_config

from controllers.datafeed_controller import TbaVideosGet, TbaVideosEnqueue
from controllers.datafeed_controller import FmsEventListGet, FmsTeamListGet
from controllers.datafeed_controller import OffseasonMatchesGet
from controllers.datafeed_controller import UsfirstEventDetailsEnqueue, UsfirstEventDetailsGet, UsfirstEventListGet
from controllers.datafeed_controller import UsfirstAwardsEnqueue, UsfirstAwardsGet
from controllers.datafeed_controller import UsfirstMatchesEnqueue, UsfirstMatchesGet, UsfirstEventRankingsEnqueue, UsfirstEventRankingsGet
from controllers.datafeed_controller import UsfirstTeamDetailsEnqueue, UsfirstTeamDetailsGet, UsfirstTeamsTpidsGet

from controllers.cron_controller import EventTeamUpdate, EventTeamUpdateEnqueue
from controllers.cron_controller import EventOprDo, EventOprEnqueue

app = webapp2.WSGIApplication([('/tasks/enqueue/tba_videos', TbaVideosEnqueue),
                               ('/tasks/enqueue/usfirst_event_details/([0-9]*)', UsfirstEventDetailsEnqueue),
                               ('/tasks/enqueue/usfirst_event_rankings/(.*)', UsfirstEventRankingsEnqueue),
                               ('/tasks/enqueue/usfirst_awards/(.*)', UsfirstAwardsEnqueue),
                               ('/tasks/enqueue/usfirst_matches/(.*)', UsfirstMatchesEnqueue),
                               ('/tasks/enqueue/usfirst_team_details', UsfirstTeamDetailsEnqueue),
                               ('/tasks/get/fms_event_list', FmsEventListGet),
                               ('/tasks/get/fms_team_list', FmsTeamListGet),
                               ('/tasks/get/offseason_event/(.*)', OffseasonMatchesGet),
                               ('/tasks/get/tba_videos/(.*)', TbaVideosGet),
                               ('/tasks/get/usfirst_event_list/([0-9]*)', UsfirstEventListGet),
                               ('/tasks/get/usfirst_event_details/([0-9]*)/([0-9]*)', UsfirstEventDetailsGet),
                               ('/tasks/get/usfirst_event_rankings/(.*)', UsfirstEventRankingsGet),
                               ('/tasks/get/usfirst_awards/(.*)', UsfirstAwardsGet),
                               ('/tasks/get/usfirst_matches/(.*)', UsfirstMatchesGet),
                               ('/tasks/get/usfirst_team_details/(.*)', UsfirstTeamDetailsGet),
                               ('/tasks/get/usfirst_teams_tpids/([0-9]*)', UsfirstTeamsTpidsGet),
                               ('/tasks/math/enqueue/event_opr/(.*)', EventOprEnqueue),
                               ('/tasks/math/enqueue/eventteam_update', EventTeamUpdateEnqueue),
                               ('/tasks/math/do/event_opr/(.*)', EventOprDo),
                               ('/tasks/math/do/eventteam_update/(.*)', EventTeamUpdate),
                               ],
                              debug=tba_config.DEBUG)
