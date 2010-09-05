#!/usr/bin/env python

import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from controllers.datafeed_controller import InstantiateUsfirstTeams
from controllers.datafeed_controller import EnqueueGetUsfirstEvents
from controllers.datafeed_controller import EnqueueGetUsfirstMatchResults
from controllers.datafeed_controller import EnqueueGetUsfirstTeams
from controllers.datafeed_controller import GetUsfirstEvent
from controllers.datafeed_controller import GetUsfirstMatchResults
from controllers.datafeed_controller import InstantiateRegionalEvents
from controllers.datafeed_controller import GetUsfirstTeam

from controllers.datafeed_controller import FlushTeams, FlushMatches, FlushEvents

def main():
    application = webapp.WSGIApplication([('/tasks/enqueue_usfirst_event_updates', EnqueueGetUsfirstEvents),
                                          ('/tasks/enqueue_usfirst_match_results', EnqueueGetUsfirstMatchResults),
                                          ('/tasks/enqueue_get_usfirst_teams', EnqueueGetUsfirstTeams),
                                          ('/tasks/instantiate_usfirst_teams', InstantiateUsfirstTeams),
                                          ('/tasks/update_usfirst_event', GetUsfirstEvent),
                                          ('/tasks/instantiate_usfirst_regional_events', InstantiateRegionalEvents),
                                          ('/tasks/get_usfirst_match_results/(.*)', GetUsfirstMatchResults),
                                          ('/tasks/get_usfirst_team/(.*)', GetUsfirstTeam),
                                          ('/tasks/flush/teams', FlushTeams), # Danger!
                                          ('/tasks/flush/matches', FlushMatches), # Danger!
                                          ('/tasks/flush/events', FlushEvents), # Danger!
                                          ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
