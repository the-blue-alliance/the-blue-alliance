#!/usr/bin/env python
import webapp2

import tba_config

from controllers.admin.admin_cron_controller import AdminPostEventTasksDo, AdminCreateDistrictTeamsEnqueue, AdminCreateDistrictTeamsDo, \
    AdminRebuildDivisionsDo, AdminRebuildDivisionsEnqueue, AdminBackfillPlayoffTypeDo, \
    AdminBackfillPlayoffTypeEnqueue
from controllers.datafeed_controller import EventListEnqueue, EventDetailsEnqueue
from controllers.datafeed_controller import EventListGet, EventDetailsGet, TeamDetailsGet


app = webapp2.WSGIApplication([('/backend-tasks/enqueue/event_list/([0-9]*)', EventListEnqueue),
                               ('/backend-tasks/enqueue/event_details/(.*)', EventDetailsEnqueue),
                               ('/backend-tasks/get/event_list/([0-9]*)', EventListGet),
                               ('/backend-tasks/get/event_details/(.*)', EventDetailsGet),
                               ('/backend-tasks/get/team_details/(.*)', TeamDetailsGet),
                               ('/backend-tasks/do/post_event_tasks/(.*)', AdminPostEventTasksDo),
                               ('/backend-tasks/enqueue/rebuild_district_teams/([0-9]+)', AdminCreateDistrictTeamsEnqueue),
                               ('/backend-tasks/do/rebuild_district_teams/([0-9]+)', AdminCreateDistrictTeamsDo),
                               ('/backend-tasks/enqueue/rebuild_divisions/([0-9]+)', AdminRebuildDivisionsEnqueue),
                               ('/backend-tasks/enqueue/backfill_playoff_type/([0-9]+)', AdminBackfillPlayoffTypeEnqueue),
                               ('/backend-tasks/do/backfill_playoff_type/([0-9]+)', AdminBackfillPlayoffTypeDo),
                               ('/backend-tasks/do/rebuild_divisions/([0-9]+)', AdminRebuildDivisionsDo)
                               ],
                              debug=tba_config.DEBUG)
