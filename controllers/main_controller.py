import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util


class MainHandler(webapp.RequestHandler):
    def get(self):
        template_values = {
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/index.html')
        self.response.out.write(template.render(path, template_values))
