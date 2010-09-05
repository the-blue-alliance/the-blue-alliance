#!/usr/bin/env python
#

import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

from controllers.main_controller import MainHandler

from controllers.event_controller import EventList, EventDetail
from controllers.match_controller import MatchList, MatchDetail
from controllers.team_controller import TeamList, TeamDetail

def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/event/list', EventList),
                                          ('/events/(.*)/(.*)', EventDetail),
                                          ('/match/list', MatchList),
                                          ('/match/(.*)', MatchDetail),
                                          ('/team/list', TeamList),
                                          ('/team/(.*)/(.*)', TeamDetail),
                                          ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
