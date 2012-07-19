#!/usr/bin/env python
import os
import webapp2

import tba_config

from controllers.event_controller import EventList, EventDetail, EventRss
from controllers.main_controller import MainHandler, ContactHandler, ThanksHandler, SearchHandler, PageNotFoundHandler, OprHandler
from controllers.match_controller import MatchList, MatchDetail
from controllers.team_controller import TeamList, TeamDetail

app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/contact', ContactHandler),
                               ('/events', EventList),
                               ('/event/(.*)/feed', EventRss),
                               ('/events/(.*)', EventList),
                               ('/event/(.*)', EventDetail),
                               ('/match/list', MatchList),
                               ('/match/(.*)', MatchDetail),
                               ('/search', SearchHandler),
                               ('/teams', TeamList),
                               ('/team/([0-9]*)', TeamDetail),
                               ('/team/([0-9]*)/(.*)', TeamDetail),
                               ('/thanks', ThanksHandler),
                               ('/opr', OprHandler),
                               ('/.*', PageNotFoundHandler)
                               ],
                              debug=tba_config.DEBUG)
