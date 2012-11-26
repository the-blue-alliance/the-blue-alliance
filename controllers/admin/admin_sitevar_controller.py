import os
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from models.sitevar import Sitevar

class AdminSitevarList(webapp.RequestHandler):
    """
    List all Sitevars.
    """
    def get(self):
        sitevars = Sitevar.query().fetch(10000)
        
        template_values = {
            "sitevars": sitevars,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/sitevar_list.html')
        self.response.out.write(template.render(path, template_values))
        
class AdminSitevarCreate(webapp.RequestHandler):
    """
    Create an Sitevar. POSTs to AdminSitevarEdit.
    """
    def get(self):
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/sitevar_create.html')
        self.response.out.write(template.render(path, {}))

class AdminSitevarEdit(webapp.RequestHandler):
    """
    Edit a Sitevar.
    """
    def get(self, sitevar_key):
        sitevar = Sitevar.get_by_id(sitevar_key)

        success = self.request.get("success")
        
        template_values = {
            "sitevar": sitevar,
            "success": success,
        }

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/sitevar_edit.html')
        self.response.out.write(template.render(path, template_values))
    
    def post(self, sitevar_key):
        #note, we don't use sitevar_key

        sitevar = Sitevar(
            id = self.request.get("key"),
            description = self.request.get("description"),
            values_json = self.request.get("values_json"),
        )
        sitevar.put()
        
        self.redirect("/admin/sitevar/edit/" + sitevar.key.id() + "?success=true")
