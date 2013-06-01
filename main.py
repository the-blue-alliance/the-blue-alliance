#!/usr/bin/env python
import os
import webapp2

import tba_config

from controllers.event_controller import EventList, EventDetail, EventRss
from controllers.insights_controller import InsightsOverview, InsightsDetail
from controllers.main_controller import ContactHandler, HashtagsHandler, \
      MainKickoffHandler, MainBuildseasonHandler, MainCompetitionseasonHandler, \
      MainOffseasonHandler, OprHandler, SearchHandler, AboutHandler, ThanksHandler, \
      PageNotFoundHandler, ChannelHandler, GamedayHandler, \
      WebcastsHandler, RecordHandler, AuthHandler, AccountHandler
from controllers.match_controller import MatchDetail
from controllers.team_controller import TeamList, TeamDetail
from controllers.ajax_controller import TypeaheadHandler, WebcastHandler

from google.appengine.ext.webapp import template
template.register_template_library('common.my_filters')

landing_handler = {tba_config.KICKOFF: MainKickoffHandler,
                   tba_config.BUILDSEASON: MainBuildseasonHandler,
                   tba_config.COMPETITIONSEASON: MainCompetitionseasonHandler,
                   tba_config.OFFSEASON: MainOffseasonHandler,
                   }

app = webapp2.WSGIApplication([('/', landing_handler[tba_config.CONFIG['landing_handler']]),
                               ('/about', AboutHandler),
                               ('/account', AccountHandler),
                               webapp2.Route('/logout', handler='controllers.main_controller.AuthHandler:logout', name='logout'),
                               webapp2.Route('/auth/<provider>/callback', handler='controllers.main_controller.AuthHandler:_auth_callback', name='auth_callback'),
                               webapp2.Route('/auth/<provider>', handler='controllers.main_controller.AuthHandler:_simple_auth', name='auth_login'),
                               ('/channel', ChannelHandler),
                               ('/contact', ContactHandler),
                               ('/events', EventList),
                               ('/event/(.*)/feed', EventRss),
                               ('/events/(.*)', EventList),
                               ('/event/(.*)', EventDetail),
                               ('/gameday', GamedayHandler),
                               ('/hashtags', HashtagsHandler),
                               ('/insights', InsightsOverview),
                               ('/insights/(.*)', InsightsDetail),
                               ('/match/(.*)', MatchDetail),
                               ('/opr', OprHandler),
                               ('/search', SearchHandler),
                               ('/teams', TeamList),
                               ('/teams/([0-9]*)', TeamList),
                               ('/team/([0-9]*)', TeamDetail),
                               ('/team/([0-9]*)/([0-9]*)', TeamDetail),
                               ('/thanks', ThanksHandler),
                               ('/webcasts', WebcastsHandler),
                               ('/record', RecordHandler),
                               ('/_/typeahead', TypeaheadHandler),
                               ('/_/webcast/(.*)/(.*)', WebcastHandler),
                               ('/.*', PageNotFoundHandler),
                               ],
                              debug=tba_config.DEBUG,
                              config=tba_config.CONFIG)
