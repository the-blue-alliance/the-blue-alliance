import os
import logging

from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from models.sitevar import Sitevar


class AdminSitevarList(LoggedInHandler):
    """
    List all Sitevars.
    """
    def get(self):
        self._require_admin()
        sitevars = Sitevar.query().fetch(10000)

        self.template_values.update({
            "sitevars": sitevars,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/sitevar_list.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminSitevarCreate(LoggedInHandler):
    """
    Create an Sitevar. POSTs to AdminSitevarEdit.
    """
    def get(self):
        self._require_admin()

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/sitevar_create.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminSitevarEdit(LoggedInHandler):
    """
    Edit a Sitevar.
    """
    def get(self, sitevar_key):
        self._require_admin()
        sitevar = Sitevar.get_by_id(sitevar_key)

        success = self.request.get("success")

        self.template_values.update({
            "sitevar": sitevar,
            "success": success,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/sitevar_edit.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self, sitevar_key):
        self._require_admin()

        # note, we don't use sitevar_key

        sitevar = Sitevar(
            id=self.request.get("key"),
            description=self.request.get("description"),
            values_json=self.request.get("values_json"),
        )
        sitevar.put()

        self.redirect("/admin/sitevar/edit/" + sitevar.key.id() + "?success=true")
