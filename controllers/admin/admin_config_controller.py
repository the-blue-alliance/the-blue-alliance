import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from models.vars import Vars, LEGAL_VALUES


class AdminConfigHandler(webapp.RequestHandler):
    def get(self):
        all_vars = Vars.get_all_cached()
        
        var_list = []
        for var in all_vars:
            key_name = var.key().name()
            var_list.append((key_name, var.value, LEGAL_VALUES[key_name]))
        
        template_values = {'var_list': var_list}
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/config.html')
        html = template.render(path, template_values)
        self.response.out.write(html)

    def post(self):
        var = Vars(key_name = self.request.get('var_name'),
                   value = self.request.get('value'))
        var.put_cached()
        self.redirect('/admin/config')
