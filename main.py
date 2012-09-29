#!/usr/bin/env python
import os
import webapp2

import tba_config

from controllers.event_controller import EventList, EventDetail, EventRss
from controllers.main_controller import ContactHandler, HashtagsHandler, \
      MainHandler, OprHandler, SearchHandler, AboutHandler, ThanksHandler, \
      PageNotFoundHandler, KickoffHandler, ChannelHandler, GamedayHandler
from controllers.match_controller import MatchList, MatchDetail
from controllers.team_controller import TeamList, TeamDetail
from controllers.ajax_controller import TypeaheadHandler, WebcastHandler


landing_handler = {False: MainHandler,
                   True: KickoffHandler}
app = webapp2.WSGIApplication([('/', landing_handler[tba_config.CONFIG['kickoff']]),
                               ('/gameday', GamedayHandler),
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
                               ('/about', AboutHandler),
                               ('/thanks', ThanksHandler),
                               ('/opr', OprHandler),
                               ('/channel', ChannelHandler),
                               ('/_/typeahead', TypeaheadHandler),
                               ('/_/webcast', WebcastHandler),
                               ('/.*', PageNotFoundHandler),
                               ],
                              debug=tba_config.DEBUG)
