#!/usr/bin/env python
import webapp2

import tba_config

from controllers.admin.admin_cron_controller import AdminPostEventTasksDo, AdminCreateDistrictTeamsEnqueue, AdminCreateDistrictTeamsDo
from controllers.cron_controller import YearInsightsEnqueue, YearInsightsDo, OverallInsightsEnqueue, OverallInsightsDo, TypeaheadCalcEnqueue, TypeaheadCalcDo
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
                               ('/backend-tasks/math/enqueue/overallinsights/(.*)', OverallInsightsEnqueue),
                               ('/backend-tasks/math/do/overallinsights/(.*)', OverallInsightsDo),
                               ('/backend-tasks/math/enqueue/insights/(.*)/([0-9]*)', YearInsightsEnqueue),
                               ('/backend-tasks/math/do/insights/(.*)/([0-9]*)', YearInsightsDo),
                               ('/backend-tasks/math/enqueue/typeaheadcalc', TypeaheadCalcEnqueue),
                               ('/backend-tasks/math/do/typeaheadcalc', TypeaheadCalcDo),
                               ],
                              debug=tba_config.DEBUG)
