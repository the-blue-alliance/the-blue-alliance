#!/usr/bin/env python
import os
import webapp2

import tba_config

from controllers.admin.admin_event_controller import AdminEventDetail, AdminEventEdit, AdminEventList
from controllers.admin.admin_main_controller import AdminDebugHandler, AdminMain
from controllers.admin.admin_match_controller import AdminMatchAddVideos, AdminMatchCleanup, AdminMatchDashboard, AdminMatchDetail, AdminMatchEdit
from controllers.admin.admin_memcache_controller import AdminMemcacheMain, AdminMemcacheFlush
from controllers.admin.admin_team_controller import AdminTeamDetail, AdminTeamList

app = webapp2.WSGIApplication([('/admin/', AdminMain),
                               ('/admin/debug/', AdminDebugHandler),
                               ('/admin/event/', AdminEventList),
                               ('/admin/event/edit/(.*)', AdminEventEdit),
                               ('/admin/event/(.*)', AdminEventDetail),
                               ('/admin/match/', AdminMatchDashboard),
                               ('/admin/match/addvideos', AdminMatchAddVideos),
                               ('/admin/match/cleanup', AdminMatchCleanup),
                               ('/admin/match/edit/(.*)', AdminMatchEdit),
                               ('/admin/match/(.*)', AdminMatchDetail),
                               ('/admin/memcache/', AdminMemcacheMain),
                               ('/admin/memcache/flush', AdminMemcacheFlush),
                               ('/admin/team/', AdminTeamList),
                               ('/admin/team/(.*)', AdminTeamDetail),
                               ],
                              debug=tba_config.DEBUG)
