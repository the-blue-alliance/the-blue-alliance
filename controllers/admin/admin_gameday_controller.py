import logging
import os

from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from models.sitevar import Sitevar


class AdminGamedayDashboard(LoggedInHandler):
    """
    Configure things about gameday
    """
    def get(self):
        self._require_admin()
        gd_sitevar = Sitevar.get_by_id("gameday.special_webcasts")
        special_webcasts = gd_sitevar.contents.get("webcasts", []) if gd_sitevar else []
        path_aliases = gd_sitevar.contents.get("aliases", {}) if gd_sitevar else {}
        default_chat = gd_sitevar.contents.get("default_chat", "") if gd_sitevar else ""

        self.template_values.update({
            "webcasts": special_webcasts,
            "aliases": path_aliases,
            "default_chat": default_chat,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/gameday_dashboard.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_admin()
        gd_sitevar = Sitevar.get_or_insert("gameday.special_webcasts")

        action = self.request.get("action")
        item = self.request.get("item")

        if action == "add" and item == "webcast":
            self.add_special_webcast(gd_sitevar)
        elif action == "delete" and item == "webcast":
            self.delete_special_webcast(gd_sitevar)
        elif action == "add" and item == "alias":
            self.add_alias(gd_sitevar)
        elif action == "delete" and item == "alias":
            self.delete_alias(gd_sitevar)
        elif action == "defaultChat":
            self.set_default_chat(gd_sitevar)

        self.redirect("/admin/gameday")
        return

    def add_special_webcast(self, gd_sitevar):
        name = self.request.get("webcast_name")
        type = self.request.get("webcast_type")
        channel = self.request.get("webcast_channel")
        file = self.request.get("webcast_file")
        urlkey = self.request.get("webcast_urlkey")
        if not name or not type or not channel or not urlkey:
            return

        sitevar_contents = gd_sitevar.contents
        if 'webcasts' not in sitevar_contents:
            sitevar_contents['webcasts'] = []
        sitevar_contents['webcasts'].append({
            'type': type,
            'channel': channel,
            'file': file,
            'name': name,
            'key_name': urlkey,
        })
        gd_sitevar.contents = sitevar_contents
        gd_sitevar.put()

    def delete_special_webcast(self, gd_sitevar):
        key_to_delete = self.request.get("webcast_key")
        if not key_to_delete:
            return

        sitevar_contents = gd_sitevar.contents
        sitevar_contents['webcasts'] = [x for x in sitevar_contents.get("webcasts", []) if x['key_name'] != key_to_delete]
        gd_sitevar.contents = sitevar_contents
        gd_sitevar.put()

    def add_alias(self, gd_sitevar):
        name = self.request.get("alias_name")
        args = self.request.get("alias_args")
        if not name or not args:
            return

        sitevar_contents = gd_sitevar.contents
        if 'aliases' not in sitevar_contents:
            sitevar_contents['aliases'] = {}
        sitevar_contents['aliases'][name] = args
        gd_sitevar.contents = sitevar_contents
        gd_sitevar.put()

    def delete_alias(self, gd_sitevar):
        key_to_delete = self.request.get("alias_key")
        sitevar_contents = gd_sitevar.contents
        if not key_to_delete or key_to_delete not in sitevar_contents['aliases']:
            return

        del sitevar_contents['aliases'][key_to_delete]
        gd_sitevar.contents = sitevar_contents
        gd_sitevar.put()

    def set_default_chat(self, gd_sitevar):
        new_channel = self.request.get('defaultChat', 'tbagameday')
        sitevar_contents = gd_sitevar.contents
        sitevar_contents['default_chat'] = new_channel
        gd_sitevar.contents = sitevar_contents
        gd_sitevar.put()
