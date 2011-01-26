#!/usr/bin/env python
import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from controllers.api_controller import ApiEventsShow, ApiTeamsShow


def main():
    application = webapp.WSGIApplication([('/api/v1/teams/show', ApiTeams),
                                          ('/api/v1/events/show', ApiEvents),
                                          ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
