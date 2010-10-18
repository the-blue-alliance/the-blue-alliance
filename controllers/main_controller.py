import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util


class MainHandler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), '../templates/main/index.html')
        self.response.out.write(template.render(path, {}))

class MainDebugHandler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), '../templates/main/debug.html')
        self.response.out.write(template.render(path, {}))