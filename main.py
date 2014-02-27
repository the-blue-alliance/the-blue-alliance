#!/usr/bin/env python
import webapp2

import tba_config

from controllers.account_controller import AccountEdit, AccountLogout, AccountOverview, AccountRegister
from controllers.ajax_controller import LiveEventHandler, TypeaheadHandler, WebcastHandler
from controllers.event_controller import EventList, EventDetail, EventRss
from controllers.gameday2_controller import Gameday2Controller
from controllers.insights_controller import InsightsOverview, InsightsDetail
from controllers.main_controller import ContactHandler, HashtagsHandler, \
      MainKickoffHandler, MainBuildseasonHandler, MainCompetitionseasonHandler, \
      MainInsightsHandler, MainOffseasonHandler, OprHandler, SearchHandler, \
      AboutHandler, ThanksHandler, PageNotFoundHandler, \
      GamedayHandler, WebcastsHandler, RecordHandler, ApiDocumentationHandler
from controllers.match_controller import MatchDetail
from controllers.suggestions.suggest_match_video_controller import SuggestMatchVideoController
from controllers.suggestions.suggest_event_webcast_controller import SuggestEventWebcastController
from controllers.suggestions.suggest_team_media_controller import SuggestTeamMediaController
from controllers.team_controller import TeamList, TeamCanonical, TeamDetail, TeamHistory

from google.appengine.ext.webapp import template
template.register_template_library('common.my_filters')

landing_handler = {tba_config.KICKOFF: MainKickoffHandler,
                   tba_config.BUILDSEASON: MainBuildseasonHandler,
                   tba_config.COMPETITIONSEASON: MainCompetitionseasonHandler,
                   tba_config.OFFSEASON: MainOffseasonHandler,
                   tba_config.INSIGHTS: MainInsightsHandler,
                   }


class Webapp2HandlerAdapter(webapp2.BaseHandlerAdapter):
    def __call__(self, request, response, exception):
        request.route_args = {}
        request.route_args['exception'] = exception
        handler = self.handler(request, response)
        return handler.get()

app = webapp2.WSGIApplication([
      webapp2.Route(r'/', landing_handler[tba_config.CONFIG['landing_handler']], 'landing'),
      webapp2.Route(r'/about', AboutHandler, 'about'),
      webapp2.Route(r'/account', AccountOverview, 'account-overview'),
      webapp2.Route(r'/account/edit', AccountEdit, 'account-edit'),
      webapp2.Route(r'/account/register', AccountRegister, 'account-register'),
      webapp2.Route(r'/apidocs', ApiDocumentationHandler, 'api-documentation'),
      webapp2.Route(r'/contact', ContactHandler, 'contact'),
      webapp2.Route(r'/event/<event_key>', EventDetail, 'event-detail'),
      webapp2.Route(r'/event/<event_key>/feed', EventRss, 'event-rss'),
      webapp2.Route(r'/events', EventList, 'event-list'),
      webapp2.Route(r'/events/<year:[0-9]+>', EventList, 'event-list'),
      webapp2.Route(r'/gameday', GamedayHandler, 'gameday'),
      webapp2.Route(r'/gameday2', Gameday2Controller, 'gameday2'),
      webapp2.Route(r'/hashtags', HashtagsHandler, 'hashtags'),
      webapp2.Route(r'/insights', InsightsOverview, 'insights'),
      webapp2.Route(r'/insights/<year:[0-9]+>', InsightsDetail, 'insights-detail'),
      webapp2.Route(r'/logout', AccountLogout, 'account-logout'),
      webapp2.Route(r'/match/<match_key>', MatchDetail, 'match-detail'),
      webapp2.Route(r'/opr', OprHandler, 'opr'),
      webapp2.Route(r'/record', RecordHandler, 'record'),
      webapp2.Route(r'/search', SearchHandler, 'search'),
      webapp2.Route(r'/suggest/event/webcast', SuggestEventWebcastController, 'suggest-event-webcast'),
      webapp2.Route(r'/suggest/match/video', SuggestMatchVideoController, 'suggest-match-video'),
      webapp2.Route(r'/suggest/team/media', SuggestTeamMediaController, 'suggest-team-media'),
      webapp2.Route(r'/team/<team_number:[0-9]+>', TeamCanonical, 'team-canonical'),
      webapp2.Route(r'/team/<team_number:[0-9]+>/<year:[0-9]+>', TeamDetail, 'team-detail'),
      webapp2.Route(r'/team/<team_number:[0-9]+>/history', TeamHistory, 'team-history'),
      webapp2.Route(r'/teams', TeamList, 'team-list'),
      webapp2.Route(r'/teams/<page:[0-9]+>', TeamList, 'team-list'),
      webapp2.Route(r'/thanks', ThanksHandler, 'thanks'),
      webapp2.Route(r'/webcasts', WebcastsHandler, 'webcasts'),
      webapp2.Route(r'/_/live-event/<event_key>/<timestamp:[0-9]+>', LiveEventHandler, 'ajax-live-event'),
      webapp2.Route(r'/_/typeahead/<search_key>', TypeaheadHandler, 'ajax-typeahead'),
      webapp2.Route(r'/_/webcast/<event_key>/<webcast_number>', WebcastHandler, 'ajax-webcast'),
      webapp2.Route(r'/<:.*>', PageNotFoundHandler, 'page-not-found'),
      ],
      debug=tba_config.DEBUG)
app.error_handlers[404] = Webapp2HandlerAdapter(PageNotFoundHandler)
