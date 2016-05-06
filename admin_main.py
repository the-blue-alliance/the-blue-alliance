#!/usr/bin/env python
import os
import webapp2

import tba_config

from controllers.admin.admin_api_controller import AdminApiAuthAdd, AdminApiAuthDelete, AdminApiAuthEdit, AdminApiAuthManage
from controllers.admin.admin_apistatus_controller import AdminApiStatus
from controllers.admin.admin_event_controller import AdminEventAddAllianceSelections, AdminEventAddTeams, AdminEventRemapTeams, AdminEventAddWebcast, AdminEventCreate, AdminEventCreateTest, AdminEventDelete, AdminEventDetail, AdminEventEdit, AdminEventList
from controllers.admin.admin_main_controller import AdminDebugHandler, AdminMain, AdminTasksHandler
from controllers.admin.admin_award_controller import AdminAwardDashboard, AdminAwardEdit, AdminAwardAdd
from controllers.admin.admin_match_controller import AdminVideosAdd, AdminMatchCleanup, AdminMatchDashboard, AdminMatchDelete, AdminMatchDetail, AdminMatchAdd, AdminMatchEdit
from controllers.admin.admin_media_controller import AdminMediaDashboard, AdminMediaDeleteReference, AdminMediaMakePreferred, AdminMediaRemovePreferred, AdminMediaAdd
from controllers.admin.admin_memcache_controller import AdminMemcacheMain
from controllers.admin.admin_migration_controller import AdminMigration, AdminMigrationCreateEventDetails
from controllers.admin.admin_mobile_controller import AdminMobile, AdminBroadcast
from controllers.admin.admin_offseason_scraper_controller import AdminOffseasonScraperController
from controllers.admin.admin_offseason_spreadsheet_controller import AdminOffseasonSpreadsheetController
from controllers.admin.admin_sitevar_controller import AdminSitevarCreate, AdminSitevarEdit, AdminSitevarList
from controllers.admin.admin_suggestion_controller import AdminCreateTestSuggestions
from controllers.admin.admin_team_controller import AdminTeamCreateTest, AdminTeamDetail, AdminTeamList
from controllers.admin.admin_user_controller import AdminUserDetail, AdminUserEdit, AdminUserTestSetup, AdminUserList

app = webapp2.WSGIApplication([('/admin/', AdminMain),
                               ('/admin/api_auth/add', AdminApiAuthAdd),
                               ('/admin/api_auth/delete/(.*)', AdminApiAuthDelete),
                               ('/admin/api_auth/edit/(.*)', AdminApiAuthEdit),
                               ('/admin/api_auth/manage', AdminApiAuthManage),
                               ('/admin/apistatus', AdminApiStatus),
                               ('/admin/debug', AdminDebugHandler),
                               ('/admin/events', AdminEventList),
                               ('/admin/events/([0-9]*)', AdminEventList),
                               ('/admin/event/add_alliance_selections/(.*)', AdminEventAddAllianceSelections),
                               ('/admin/event/add_teams/(.*)', AdminEventAddTeams),
                               ('/admin/event/add_webcast/(.*)', AdminEventAddWebcast),
                               ('/admin/event/remap_teams/(.*)', AdminEventRemapTeams),
                               ('/admin/event/create', AdminEventCreate),
                               ('/admin/event/create/test', AdminEventCreateTest),
                               ('/admin/event/delete/(.*)', AdminEventDelete),
                               ('/admin/event/edit/(.*)', AdminEventEdit),
                               ('/admin/event/(.*)', AdminEventDetail),
                               ('/admin/awards', AdminAwardDashboard),
                               ('/admin/award/add', AdminAwardAdd),
                               ('/admin/award/edit/(.*)', AdminAwardEdit),
                               ('/admin/matches', AdminMatchDashboard),
                               ('/admin/match/add', AdminMatchAdd),
                               ('/admin/match/cleanup', AdminMatchCleanup),
                               ('/admin/match/delete/(.*)', AdminMatchDelete),
                               ('/admin/match/edit/(.*)', AdminMatchEdit),
                               ('/admin/match/(.*)', AdminMatchDetail),
                               ('/admin/media', AdminMediaDashboard),
                               ('/admin/media/add_media', AdminMediaAdd),
                               ('/admin/media/delete_reference/(.*)', AdminMediaDeleteReference),
                               ('/admin/media/make_preferred/(.*)', AdminMediaMakePreferred),
                               ('/admin/media/remove_preferred/(.*)', AdminMediaRemovePreferred),
                               ('/admin/memcache', AdminMemcacheMain),
                               ('/admin/migration', AdminMigration),
                               ('/admin/migration/create_event_details', AdminMigrationCreateEventDetails),
                               ('/admin/offseasons', AdminOffseasonScraperController),
                               ('/admin/offseasons/spreadsheet', AdminOffseasonSpreadsheetController),
                               ('/admin/sitevars', AdminSitevarList),
                               ('/admin/sitevar/create', AdminSitevarCreate),
                               ('/admin/sitevar/edit/(.*)', AdminSitevarEdit),
                               ('/admin/suggestions/create/test', AdminCreateTestSuggestions),
                               ('/admin/tasks', AdminTasksHandler),
                               ('/admin/teams', AdminTeamList),
                               ('/admin/team/create/test', AdminTeamCreateTest),
                               ('/admin/team/(.*)', AdminTeamDetail),
                               ('/admin/users', AdminUserList),
                               ('/admin/user/edit/(.*)', AdminUserEdit),
                               ('/admin/user/create/test', AdminUserTestSetup),
                               ('/admin/user/(.*)', AdminUserDetail),
                               ('/admin/videos/add', AdminVideosAdd),
                               ('/admin/mobile', AdminMobile),
                               ('/admin/mobile/broadcast', AdminBroadcast),
                               ],
                              debug=tba_config.DEBUG)
