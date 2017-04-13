#!/usr/bin/env python
import webapp2
from webapp2_extras.routes import RedirectRoute

import tba_config

from controllers.account_controller import AccountEdit, AccountLoginRequired, AccountLogin, AccountLogout, \
AccountOverview, AccountRegister, MyTBAController, myTBAAddHotMatchesController, MyTBAEventController, \
MyTBAMatchController, MyTBATeamController, AccountAPIReadKeyAdd, AccountAPIReadKeyDelete
from controllers.advanced_search_controller import AdvancedSearchController
from controllers.ajax_controller import AccountInfoHandler, AccountRegisterFCMToken, AccountFavoritesHandler, AccountFavoritesAddHandler, AccountFavoritesDeleteHandler, \
      YouTubePlaylistHandler, AllowedApiWriteEventsHandler
from controllers.ajax_controller import LiveEventHandler, TypeaheadHandler, WebcastHandler
from controllers.event_controller import EventList, EventDetail, EventInsights, EventRss
from controllers.event_wizard_controller import EventWizardHandler
from controllers.gameday_controller import Gameday2Controller, GamedayHandler, GamedayRedirectHandler
from controllers.insights_controller import InsightsOverview, InsightsDetail
from controllers.main_controller import TwoChampsHandler, ContactHandler, HashtagsHandler, \
    MainKickoffHandler, MainBuildseasonHandler, MainChampsHandler, MainCompetitionseasonHandler, \
    MainInsightsHandler, MainOffseasonHandler, OprHandler, PredictionsHandler, SearchHandler, \
    AboutHandler, ThanksHandler, handle_404, handle_500, \
    WebcastsHandler, RecordHandler, ApiDocumentationHandler, ApiWriteHandler, MatchInputHandler, WebhookDocumentationHandler, \
      AddDataHandler
from controllers.match_controller import MatchDetail
from controllers.match_suggestion_controller import MatchSuggestionHandler
from controllers.match_timeline_controller import MatchTimelineHandler
from controllers.mytba_controller import MyTBALiveController
from controllers.nearby_controller import NearbyController
from controllers.nightbot_controller import NightbotTeamNextmatchHandler, NightbotTeamStatuskHandler
from controllers.notification_controller import UserNotificationBroadcast
from controllers.district_controller import DistrictDetail
from controllers.suggestions.suggest_apiwrite_controller import SuggestApiWriteController
from controllers.suggestions.suggest_apiwrite_review_controller import \
      SuggestApiWriteReviewController
from controllers.suggestions.suggest_designs_review_controller import SuggestDesignsReviewController
from controllers.suggestions.suggest_event_media_controller import SuggestEventMediaController
from controllers.suggestions.suggest_event_media_review_controller import \
      SuggestEventMediaReviewController
from controllers.suggestions.suggest_match_video_controller import SuggestMatchVideoController, \
      SuggestMatchVideoPlaylistController
from controllers.suggestions.suggest_match_video_review_controller import SuggestMatchVideoReviewController
from controllers.suggestions.suggest_event_webcast_controller import SuggestEventWebcastController
from controllers.suggestions.suggest_event_webcast_review_controller import SuggestEventWebcastReviewController
from controllers.suggestions.suggest_offseason_event_controller import \
      SuggestOffseasonEventController
from controllers.suggestions.suggest_offseason_event_review_controller import \
      SuggestOffseasonEventReviewController
from controllers.suggestions.suggest_review_home_controller import SuggestReviewHomeController
from controllers.suggestions.suggest_social_media_review_controller import \
      SuggestSocialMediaReviewController
from controllers.suggestions.suggest_team_media_controller import SuggestTeamMediaController, SuggestTeamSocialMediaController
from controllers.suggestions.suggest_team_media_review_controller import SuggestTeamMediaReviewController
from controllers.test_notification_controller import TestNotificationController
from controllers.team_controller import TeamList, TeamCanonical, TeamDetail, TeamHistory
from controllers.webhook_controller import WebhookAdd, WebhookDelete, WebhookVerify, WebhookVerificationSend

from google.appengine.ext.webapp import template
template.register_template_library('common.my_filters')

landing_handler = {tba_config.KICKOFF: MainKickoffHandler,
                   tba_config.BUILDSEASON: MainBuildseasonHandler,
                   tba_config.CHAMPS: MainChampsHandler,
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
      RedirectRoute(r'/', landing_handler[tba_config.CONFIG['landing_handler']], 'landing', strict_slash=True),
      RedirectRoute(r'/2champs', TwoChampsHandler, '2champs', strict_slash=True),
      RedirectRoute(r'/about', AboutHandler, 'about', strict_slash=True),
      RedirectRoute(r'/account', AccountOverview, 'account-overview', strict_slash=True),
      RedirectRoute(r'/account/api/read_key_add', AccountAPIReadKeyAdd, 'account-api-read-key-add', strict_slash=True),
      RedirectRoute(r'/account/api/read_key_delete', AccountAPIReadKeyDelete, 'account-api-read-key-delete', strict_slash=True),
      RedirectRoute(r'/account/edit', AccountEdit, 'account-edit', strict_slash=True),
      RedirectRoute(r'/account/register', AccountRegister, 'account-register', strict_slash=True),
      RedirectRoute(r'/account/login_required', AccountLoginRequired, 'account-login-required', strict_slash=True),
      RedirectRoute(r'/account/mytba', MyTBAController, 'account-mytba', strict_slash=True),
      RedirectRoute(r'/account/mytba/add_hot_matches/<event_key>', myTBAAddHotMatchesController, 'account-mytba-add-hot-matches', strict_slash=True),
      RedirectRoute(r'/account/mytba/add_hot_matches', myTBAAddHotMatchesController, 'account-mytba-add-hot-matches', strict_slash=True),
      RedirectRoute(r'/account/mytba/event/<event_key>', MyTBAEventController, 'account-mytba-event', strict_slash=True),
      RedirectRoute(r'/account/mytba/match/<match_key>', MyTBAMatchController, 'account-mytba-match', strict_slash=True),
      RedirectRoute(r'/account/mytba/team/<team_number:[0-9]+>', MyTBATeamController, 'account-mytba-team', strict_slash=True),
      RedirectRoute(r'/add-data', AddDataHandler, 'add-data', strict_slash=True),
      RedirectRoute(r'/advanced_team_search', AdvancedSearchController, 'advanced_team_search', strict_slash=True),
      RedirectRoute(r'/apidocs', ApiDocumentationHandler, 'api-documentation', strict_slash=True),
      RedirectRoute(r'/apidocs/webhooks', WebhookDocumentationHandler, 'webhook-documentation', strict_slash=True),
      RedirectRoute(r'/apiwrite', ApiWriteHandler, 'api-write', strict_slash=True),
      RedirectRoute(r'/contact', ContactHandler, 'contact', strict_slash=True),
      RedirectRoute(r'/event/<event_key>', EventDetail, 'event-detail', strict_slash=True),
      RedirectRoute(r'/event/<event_key>/insights', EventInsights, 'event-insights', strict_slash=True),
      RedirectRoute(r'/event/<event_key>/feed', EventRss, 'event-rss', strict_slash=True),
      RedirectRoute(r'/events/<year:[0-9]+>', EventList, 'event-list-year', strict_slash=True),
      RedirectRoute(r'/events/<district_abbrev:[a-z]+>/<year:[0-9]+>', DistrictDetail, 'district-detail', strict_slash=True),
      RedirectRoute(r'/events/<district_abbrev:[a-z]+>', DistrictDetail, 'district-canonical', strict_slash=True),
      RedirectRoute(r'/events', EventList, 'event-list', strict_slash=True),
      RedirectRoute(r'/eventwizard', EventWizardHandler, 'event-wizard', strict_slash=True),
      RedirectRoute(r'/oldgameday', GamedayHandler, 'gameday', strict_slash=True),
      RedirectRoute(r'/gameday/<alias>', GamedayRedirectHandler, 'gameday-alias', strict_slash=True),
      RedirectRoute(r'/gameday', Gameday2Controller, 'gameday2', strict_slash=True),
      RedirectRoute(r'/hashtags', HashtagsHandler, 'hashtags', strict_slash=True),
      RedirectRoute(r'/insights/<year:[0-9]+>', InsightsDetail, 'insights-detail', strict_slash=True),
      RedirectRoute(r'/insights', InsightsOverview, 'insights', strict_slash=True),
      RedirectRoute(r'/login', AccountLogin, 'account-login', strict_slash=True),
      RedirectRoute(r'/logout', AccountLogout, 'account-logout', strict_slash=True),
      RedirectRoute(r'/match/<match_key>', MatchDetail, 'match-detail', strict_slash=True),
      RedirectRoute(r'/match_suggestion', MatchSuggestionHandler, 'match-suggestion', strict_slash=True),
      RedirectRoute(r'/match_timeline', MatchTimelineHandler, 'match-timeline', strict_slash=True),
      RedirectRoute(r'/matchinput', MatchInputHandler, 'match-input', strict_slash=True),
      RedirectRoute(r'/mytba', MyTBALiveController, 'mytba-live', strict_slash=True),
      RedirectRoute(r'/nearby', NearbyController, 'nearby', strict_slash=True),
      RedirectRoute(r'/notifications/broadcast', UserNotificationBroadcast, 'notification-broadcast', strict_slash=True),
      RedirectRoute(r'/notifications/test/<type:[0-9]+>', TestNotificationController, 'test-notifications', strict_slash=True),
      RedirectRoute(r'/opr', OprHandler, 'opr', strict_slash=True),
      RedirectRoute(r'/predictions', PredictionsHandler, 'predictions', strict_slash=True),
      RedirectRoute(r'/record', RecordHandler, 'record', strict_slash=True),
      RedirectRoute(r'/request/apiwrite', SuggestApiWriteController, 'request-apiwrite', strict_slash=True),
      RedirectRoute(r'/search', SearchHandler, 'search', strict_slash=True),
      RedirectRoute(r'/suggest/apiwrite/review', SuggestApiWriteReviewController, 'request-apiwrite-review', strict_slash=True),
      RedirectRoute(r'/suggest/cad/review', SuggestDesignsReviewController, 'suggest-designs-review', strict_slash=True),
      RedirectRoute(r'/suggest/event/webcast', SuggestEventWebcastController, 'suggest-event-webcast', strict_slash=True),
      RedirectRoute(r'/suggest/event/webcast/review', SuggestEventWebcastReviewController, 'suggest-event-webcast-review', strict_slash=True),
      RedirectRoute(r'/suggest/event/media', SuggestEventMediaController, 'suggest-event-media', strict_slash=True),
      RedirectRoute(r'/suggest/event/video', SuggestMatchVideoPlaylistController, 'suggest-matches-playlist', strict_slash=True),
      RedirectRoute(r'/suggest/match/video', SuggestMatchVideoController, 'suggest-match-video', strict_slash=True),
      RedirectRoute(r'/suggest/match/video/review', SuggestMatchVideoReviewController, 'suggest-match-video-review', strict_slash=True),
      RedirectRoute(r'/suggest/review', SuggestReviewHomeController, 'suggest-review-home', strict_slash=True),
      RedirectRoute(r'/suggest/event/media/review', SuggestEventMediaReviewController, 'suggest-event-media-review', strict_slash=True),
      RedirectRoute(r'/suggest/team/media', SuggestTeamMediaController, 'suggest-team-media', strict_slash=True),
      RedirectRoute(r'/suggest/team/social_media', SuggestTeamSocialMediaController, 'suggest-team-social-media', strict_slash=True),
      RedirectRoute(r'/suggest/team/social/review', SuggestSocialMediaReviewController, 'suggest-team-social-media-review', strict_slash=True),
      RedirectRoute(r'/suggest/team/media/review', SuggestTeamMediaReviewController, 'suggest-team-media-review', strict_slash=True),
      RedirectRoute(r'/suggest/offseason', SuggestOffseasonEventController, 'suggest-offseason-event', strict_slash=True),
      RedirectRoute(r'/suggest/offseason/review', SuggestOffseasonEventReviewController, 'suggest-offseason-event-review', strict_slash=True),
      RedirectRoute(r'/team/<team_number:[0-9]+>', TeamCanonical, 'team-canonical', strict_slash=True),
      RedirectRoute(r'/team/<team_number:[0-9]+>/<year:[0-9]+>', TeamDetail, 'team-detail', strict_slash=True),
      RedirectRoute(r'/team/<team_number:[0-9]+>/history', TeamHistory, 'team-history', strict_slash=True),
      RedirectRoute(r'/teams/<page:[0-9]+>', TeamList, 'team-list-year', strict_slash=True),
      RedirectRoute(r'/teams', TeamList, 'team-list', strict_slash=True),
      RedirectRoute(r'/thanks', ThanksHandler, 'thanks', strict_slash=True),
      RedirectRoute(r'/watch/<alias>', GamedayRedirectHandler, 'gameday-watch', strict_slash=True),
      RedirectRoute(r'/webcasts', WebcastsHandler, 'webcasts', strict_slash=True),
      RedirectRoute(r'/webhooks/add', WebhookAdd, 'webhook-add', strict_slash=True),
      RedirectRoute(r'/webhooks/delete', WebhookDelete, 'webhook-delete', strict_slash=True),
      RedirectRoute(r'/webhooks/verify/<client_id:[0-9]+>', WebhookVerify, 'webhook-verify', strict_slash=True),
      RedirectRoute(r'/webhooks/send_verification', WebhookVerificationSend, 'webhook-send-verification', strict_slash=True),
      RedirectRoute(r'/_/account/apiwrite_events', AllowedApiWriteEventsHandler, 'allowed-apiwrite-events', strict_slash=True),
      RedirectRoute(r'/_/account/info', AccountInfoHandler, 'account-info', strict_slash=True),
      RedirectRoute(r'/_/account/register_fcm_token', AccountRegisterFCMToken, 'account-register-web-client', strict_slash=True),
      RedirectRoute(r'/_/account/favorites/<model_type:[0-9]+>', AccountFavoritesHandler, 'ajax-account-favorites', strict_slash=True),
      RedirectRoute(r'/_/account/favorites/add', AccountFavoritesAddHandler, 'ajax-account-favorites-add', strict_slash=True),
      RedirectRoute(r'/_/account/favorites/delete', AccountFavoritesDeleteHandler, 'ajax-account-favorites-delete', strict_slash=True),
      RedirectRoute(r'/_/live-event/<event_key>/<timestamp:[0-9]+>', LiveEventHandler, 'ajax-live-event', strict_slash=True),
      RedirectRoute(r'/_/nightbot/nextmatch/<arg_str:(.*)>', NightbotTeamNextmatchHandler, 'nightbot-team-nextmatch', strict_slash=True),
      RedirectRoute(r'/_/nightbot/status/<team_number:[0-9]+>', NightbotTeamStatuskHandler, 'nightbot-team-status', strict_slash=True),
      RedirectRoute(r'/_/typeahead/<search_key>', TypeaheadHandler, 'ajax-typeahead', strict_slash=True),
      RedirectRoute(r'/_/webcast/<event_key>/<webcast_number>', WebcastHandler, 'ajax-webcast', strict_slash=True),
      RedirectRoute(r'/_/yt/playlist/videos', YouTubePlaylistHandler, 'ajex-yt-playlist', strict_slash=True),
      ],
      debug=tba_config.DEBUG)
app.error_handlers[404] = handle_404
app.error_handlers[500] = handle_500
