#!/usr/bin/env python
import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from controllers.admin.admin_event_controller import AdminEventList, AdminEventDetail, AdminEventEdit
from controllers.admin.admin_main_controller import AdminMain
from controllers.admin.admin_match_controller import AdminMatchDashboard, AdminMatchDetail, AdminMatchEdit
from controllers.admin.admin_team_controller import AdminTeamList, AdminTeamDetail


def main():
    application = webapp.WSGIApplication([('/admin/', AdminMain),
                                          ('/admin/event/', AdminEventList),
                                          ('/admin/event/edit/(.*)', AdminEventEdit),
                                          ('/admin/event/(.*)', AdminEventDetail),
                                          ('/admin/match/', AdminMatchDashboard),
                                          ('/admin/match/edit/(.*)', AdminMatchEdit),
                                          ('/admin/match/(.*)', AdminMatchDetail),
                                          ('/admin/team/', AdminTeamList),
                                          ('/admin/team/(.*)', AdminTeamDetail),
                                          ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
