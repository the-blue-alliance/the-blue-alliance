#!/usr/bin/env python
import os

from google.appengine.dist import use_library
use_library('django', '1.2')
from django.conf import settings
try:
    settings.configure(INSTALLED_APPS=('stub',))
except Exception, e:
    pass

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from controllers.admin.admin_event_controller import AdminEventDetail, AdminEventEdit, AdminEventList
from controllers.admin.admin_main_controller import AdminDebugHandler, AdminMain
from controllers.admin.admin_match_controller import AdminMatchAddVideos, AdminMatchDashboard, AdminMatchDetail, AdminMatchEdit
from controllers.admin.admin_memcache_controller import AdminMemcacheMain, AdminMemcacheFlush
from controllers.admin.admin_team_controller import AdminTeamDetail, AdminTeamList


def main():
    application = webapp.WSGIApplication([('/admin/', AdminMain),
                                          ('/admin/debug/', AdminDebugHandler),
                                          ('/admin/event/', AdminEventList),
                                          ('/admin/event/edit/(.*)', AdminEventEdit),
                                          ('/admin/event/(.*)', AdminEventDetail),
                                          ('/admin/match/', AdminMatchDashboard),
                                          ('/admin/match/addvideos', AdminMatchAddVideos),
                                          ('/admin/match/edit/(.*)', AdminMatchEdit),
                                          ('/admin/match/(.*)', AdminMatchDetail),
                                          ('/admin/memcache/', AdminMemcacheMain),
                                          ('/admin/memcache/flush', AdminMemcacheFlush),
                                          ('/admin/team/', AdminTeamList),
                                          ('/admin/team/(.*)', AdminTeamDetail),
                                          ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
