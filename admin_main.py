#!/usr/bin/env python
import os
import webapp2

import tba_config

from controllers.admin.admin_event_controller import AdminEventAddWebcast, AdminEventCreate, AdminEventCreateTest, AdminEventDelete, AdminEventDetail, AdminEventEdit, AdminEventList
from controllers.admin.admin_main_controller import AdminDebugHandler, AdminMain, AdminTasksHandler
from controllers.admin.admin_award_controller import AdminAwardDashboard, AdminAwardEdit, AdminAwardAdd
from controllers.admin.admin_match_controller import AdminVideosAdd, AdminMatchCleanup, AdminMatchDashboard, AdminMatchDetail, AdminMatchAdd, AdminMatchEdit
from controllers.admin.admin_memcache_controller import AdminMemcacheMain
from controllers.admin.admin_sitevar_controller import AdminSitevarCreate, AdminSitevarEdit, AdminSitevarList
from controllers.admin.suggestions.admin_suggestions_review_controller import AdminSuggestionsReviewController
from controllers.admin.admin_team_controller import AdminTeamDetail, AdminTeamList
from controllers.admin.admin_migration_controller import AdminMigration

app = webapp2.WSGIApplication([('/admin/', AdminMain),
                               ('/admin/debug', AdminDebugHandler),
                               ('/admin/events', AdminEventList),
                               ('/admin/event/add_webcast/(.*)', AdminEventAddWebcast),
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
                               ('/admin/match/edit/(.*)', AdminMatchEdit),
                               ('/admin/match/(.*)', AdminMatchDetail),
                               ('/admin/memcache', AdminMemcacheMain),
                               ('/admin/migration', AdminMigration),
                               ('/admin/sitevars', AdminSitevarList),
                               ('/admin/sitevar/create', AdminSitevarCreate),
                               ('/admin/sitevar/edit/(.*)', AdminSitevarEdit),
                               ('/admin/suggestions/review', AdminSuggestionsReviewController),
                               ('/admin/tasks', AdminTasksHandler),
                               ('/admin/teams', AdminTeamList),
                               ('/admin/team/(.*)', AdminTeamDetail),
                               ('/admin/videos/add', AdminVideosAdd),
                               ],
                              debug=tba_config.DEBUG)
