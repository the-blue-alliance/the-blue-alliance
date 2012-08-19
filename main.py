#!/usr/bin/env python
import os
import webapp2

import tba_config

from controllers.event_controller import EventList, EventDetail, EventRss
from controllers.main_controller import ContactHandler, HashtagsHandler, \
      MainHandler, OprHandler, SearchHandler, ThanksHandler, \
      TypeaheadHandler, PageNotFoundHandler 
from controllers.match_controller import MatchList, MatchDetail
from controllers.team_controller import TeamList, TeamDetail


app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/contact', ContactHandler),
                               ('/events', EventList),
                               ('/event/(.*)/feed', EventRss),
                               ('/events/(.*)', EventList),
                               ('/event/(.*)', EventDetail),
                               ('/hashtags', HashtagsHandler),
                               ('/match/list', MatchList),
                               ('/match/(.*)', MatchDetail),
                               ('/search', SearchHandler),
                               ('/teams', TeamList),
                               ('/team/([0-9]*)', TeamDetail),
                               ('/team/([0-9]*)/(.*)', TeamDetail),
                               ('/thanks', ThanksHandler),
                               ('/opr', OprHandler),
                               ('/.*', PageNotFoundHandler),
                               ('/_/typeahead', TypeaheadHandler),
                               ],
                              debug=tba_config.DEBUG)
