#!/usr/bin/env python
import os
import webapp2

import tba_config

from controllers.admin.admin_event_controller import AdminEventDetail, AdminEventEdit, AdminEventList
from controllers.admin.admin_main_controller import AdminDebugHandler, AdminMain
from controllers.admin.admin_match_controller import AdminVideosAdd, AdminMatchCleanup, AdminMatchDashboard, AdminMatchDetail, AdminMatchEdit
from controllers.admin.admin_memcache_controller import AdminMemcacheMain
from controllers.admin.admin_team_controller import AdminTeamDetail, AdminTeamList

app = webapp2.WSGIApplication([('/admin/', AdminMain),
                               ('/admin/debug', AdminDebugHandler),
                               ('/admin/events', AdminEventList),
                               ('/admin/event/edit/(.*)', AdminEventEdit),
                               ('/admin/event/(.*)', AdminEventDetail),
                               ('/admin/matches', AdminMatchDashboard),
                               ('/admin/match/cleanup', AdminMatchCleanup),
                               ('/admin/match/edit/(.*)', AdminMatchEdit),
                               ('/admin/match/(.*)', AdminMatchDetail),
                               ('/admin/memcache', AdminMemcacheMain),
                               ('/admin/teams', AdminTeamList),
                               ('/admin/team/(.*)', AdminTeamDetail),
                               ('/admin/videos/add', AdminVideosAdd),
                               ],
                              debug=tba_config.DEBUG)
