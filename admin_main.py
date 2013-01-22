#!/usr/bin/env python
import os
import webapp2

import tba_config

from controllers.admin.admin_event_controller import AdminEventCreate, AdminEventDelete, AdminEventDetail, AdminEventEdit, AdminEventList, AdminAwardEdit
from controllers.admin.admin_main_controller import AdminDebugHandler, AdminMain, AdminTasksHandler
from controllers.admin.admin_match_controller import AdminVideosAdd, AdminMatchCleanup, AdminMatchDashboard, AdminMatchDetail, AdminMatchAdd, AdminMatchEdit
from controllers.admin.admin_memcache_controller import AdminMemcacheMain
from controllers.admin.admin_sitevar_controller import AdminSitevarCreate, AdminSitevarEdit, AdminSitevarList
from controllers.admin.admin_team_controller import AdminTeamDetail, AdminTeamList

app = webapp2.WSGIApplication([('/admin/', AdminMain),
                               ('/admin/debug', AdminDebugHandler),
                               ('/admin/events', AdminEventList),
                               ('/admin/event/create', AdminEventCreate),
                               ('/admin/event/delete/(.*)', AdminEventDelete),
                               ('/admin/event/edit/(.*)', AdminEventEdit),
                               ('/admin/event/(.*)', AdminEventDetail),
                               ('/admin/award/edit/(.*)', AdminAwardEdit),
                               ('/admin/matches', AdminMatchDashboard),
                               ('/admin/match/add', AdminMatchAdd),
                               ('/admin/match/cleanup', AdminMatchCleanup),
                               ('/admin/match/edit/(.*)', AdminMatchEdit),
                               ('/admin/match/(.*)', AdminMatchDetail),
                               ('/admin/memcache', AdminMemcacheMain),
                               ('/admin/sitevars', AdminSitevarList),
                               ('/admin/sitevar/create', AdminSitevarCreate),
                               ('/admin/sitevar/edit/(.*)', AdminSitevarEdit),
                               ('/admin/tasks', AdminTasksHandler),
                               ('/admin/teams', AdminTeamList),
                               ('/admin/team/(.*)', AdminTeamDetail),
                               ('/admin/videos/add', AdminVideosAdd),
                               ],
                              debug=tba_config.DEBUG)
