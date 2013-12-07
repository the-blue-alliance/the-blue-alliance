#!/usr/bin/env python
import os
import webapp2

import tba_config

from controllers.account_controller import AccountEdit, AccountLogout, AccountOverview, AccountRegister
from controllers.ajax_controller import TypeaheadHandler, WebcastHandler
from controllers.event_controller import EventList, EventDetail, EventRss
from controllers.gameday2_controller import Gameday2Controller
from controllers.insights_controller import InsightsOverview, InsightsDetail
from controllers.main_controller import ContactHandler, HashtagsHandler, \
      MainKickoffHandler, MainBuildseasonHandler, MainCompetitionseasonHandler, \
      MainInsightsHandler, MainOffseasonHandler, OprHandler, SearchHandler, \
      AboutHandler, ThanksHandler, PageNotFoundHandler, \
      GamedayHandler, WebcastsHandler, RecordHandler
from controllers.match_controller import MatchDetail
from controllers.suggestions.suggest_match_video_controller import SuggestMatchVideoController
from controllers.suggestions.suggest_event_webcast_controller import SuggestEventWebcastController
from controllers.team_controller import TeamList, TeamDetail, TeamHistory

from google.appengine.ext.webapp import template
template.register_template_library('common.my_filters')

landing_handler = {tba_config.KICKOFF: MainKickoffHandler,
                   tba_config.BUILDSEASON: MainBuildseasonHandler,
                   tba_config.COMPETITIONSEASON: MainCompetitionseasonHandler,
                   tba_config.OFFSEASON: MainOffseasonHandler,
                   tba_config.INSIGHTS: MainInsightsHandler,
                   }

app = webapp2.WSGIApplication([('/', landing_handler[tba_config.CONFIG['landing_handler']]),
                               ('/about', AboutHandler),
                               ('/account', AccountOverview),
                               ('/account/edit', AccountEdit),
                               ('/account/register', AccountRegister),
                               ('/contact', ContactHandler),
                               ('/events', EventList),
                               ('/events/([0-9]*)', EventList),
                               ('/event/(.*)/feed', EventRss),
                               ('/event/(.*)', EventDetail),
                               ('/gameday', GamedayHandler),
                               ('/gameday2', Gameday2Controller),
                               ('/hashtags', HashtagsHandler),
                               ('/insights', InsightsOverview),
                               ('/insights/(.*)', InsightsDetail),
                               ('/logout', AccountLogout),
                               ('/match/(.*)', MatchDetail),
                               ('/opr', OprHandler),
                               ('/search', SearchHandler),
                               ('/suggest/event/webcast', SuggestEventWebcastController),
                               ('/suggest/match/video', SuggestMatchVideoController),
                               ('/teams', TeamList),
                               ('/teams/([0-9]*)', TeamList),
                               ('/team/([0-9]*)', TeamDetail),
                               ('/team/([0-9]*)/history', TeamHistory),
                               ('/team/([0-9]*)/([0-9]*)', TeamDetail),
                               ('/thanks', ThanksHandler),
                               ('/webcasts', WebcastsHandler),
                               ('/record', RecordHandler),
                               ('/_/typeahead/(.+)', TypeaheadHandler),
                               ('/_/webcast/(.*)/(.*)', WebcastHandler),
                               ('/.*', PageNotFoundHandler),
                               ],
                              debug=tba_config.DEBUG)
