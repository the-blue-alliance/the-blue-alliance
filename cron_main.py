#!/usr/bin/env python

import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from controllers.datafeed_controller import TbaVideosGet, TbaVideosGetEnqueue
from controllers.datafeed_controller import UsfirstEventGetEnqueue, UsfirstEventGet, UsfirstEventsInstantiate
from controllers.datafeed_controller import UsfirstMatchesGetEnqueue, UsfirstMatchesGet
from controllers.datafeed_controller import UsfirstTeamsFastGet, UsfirstTeamGetEnqueue, UsfirstTeamGet, UsfirstTeamsInstantiate

from controllers.datafeed_controller import OprGet, OprGetEnqueue

from controllers.cron_controller import EventTeamUpdate, EventTeamUpdateEnqueue

def main():
    application = webapp.WSGIApplication([('/tasks/eventteam_update_enqueue', EventTeamUpdateEnqueue),
                                          ('/tasks/eventteam_update/(.*)', EventTeamUpdate),
                                          ('/tasks/tba_videos_get/(.*)', TbaVideosGet),
                                          ('/tasks/tba_videos_get_enqueue', TbaVideosGetEnqueue),
                                          ('/tasks/usfirst_event_get_enqueue', UsfirstEventGetEnqueue),
                                          ('/tasks/usfirst_event_get/(.*)/(.*)', UsfirstEventGet),
                                          ('/tasks/usfirst_events_instantiate', UsfirstEventsInstantiate),
                                          ('/tasks/usfirst_matches_get_enqueue', UsfirstMatchesGetEnqueue),
                                          ('/tasks/usfirst_matches_get/(.*)', UsfirstMatchesGet),
                                          ('/tasks/usfirst_teams_fast_get', UsfirstTeamsFastGet),
                                          ('/tasks/usfirst_team_get_enqueue', UsfirstTeamGetEnqueue),
                                          ('/tasks/usfirst_team_get/(.*)', UsfirstTeamGet),
                                          ('/tasks/usfirst_teams_instantiate', UsfirstTeamsInstantiate),
                                          ('/tasks/event_opr_get_enqueue', OprGetEnqueue),
                                          ('/tasks/event_opr_get/(.*)', OprGet)
                                          ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
