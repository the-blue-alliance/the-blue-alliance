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

from controllers.api_controller import ApiEventsShow, ApiTeamDetails, ApiTeamsShow, ApiEventList, ApiEventDetails


def main():
    application = webapp.WSGIApplication([('/api/v1/team/details', ApiTeamDetails),
                                          ('/api/v1/teams/show', ApiTeamsShow),
                                          ('/api/v1/events/show', ApiEventsShow),
                                          ('/api/v1/events/list', ApiEventList),
                                          ('/api/v1/event/details', ApiEventDetails),
                                          ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
