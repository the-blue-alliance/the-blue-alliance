#!/usr/bin/env python
import webapp2

import tba_config

from controllers.backup_controller import TbaCSVBackupTeamsDo
from controllers.cron_controller import YearInsightsEnqueue, YearInsightsDo, OverallInsightsEnqueue, OverallInsightsDo, TypeaheadCalcEnqueue, TypeaheadCalcDo


app = webapp2.WSGIApplication([('/backend-tasks-b2/math/enqueue/overallinsights/(.*)', OverallInsightsEnqueue),
                               ('/backend-tasks-b2/math/do/overallinsights/(.*)', OverallInsightsDo),
                               ('/backend-tasks-b2/math/enqueue/insights/(.*)/([0-9]*)', YearInsightsEnqueue),
                               ('/backend-tasks-b2/math/do/insights/(.*)/([0-9]*)', YearInsightsDo),
                               ('/backend-tasks-b2/math/enqueue/typeaheadcalc', TypeaheadCalcEnqueue),
                               ('/backend-tasks-b2/math/do/typeaheadcalc', TypeaheadCalcDo),
                               ('/backend-tasks-b2/do/csv_backup_teams', TbaCSVBackupTeamsDo),
                               ],
                              debug=tba_config.DEBUG)
