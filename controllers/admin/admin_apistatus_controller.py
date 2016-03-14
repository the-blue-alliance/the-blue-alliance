import json
import os

from google.appengine.ext.webapp import template

from controllers.api.api_status_controller import ApiStatusController
from controllers.base_controller import LoggedInHandler
from models.sitevar import Sitevar


class AdminApiStatus(LoggedInHandler):
    """
    Administrate connected mobile clients
    """
    def get(self):
        self._require_admin()

        status_sitevar = Sitevar.get_or_insert('apistatus', values_json="{}")
        status = status_sitevar.contents
        android_status = status.get('android', None)
        ios_status = status.get('ios', None)

        self.template_values.update({
            'max_year': status.get('max_season', 2016),
            'android_latest_version': android_status.get('latest_app_version', -1) if android_status else -1,
            'android_min_version': android_status.get('min_app_version', -1) if android_status else -1,
            'ios_latest_version': ios_status.get('latest_app_version', -1) if ios_status else -1,
            'ios_min_version': ios_status.get('min_app_version', -1) if ios_status else -1,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/apistatus.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_admin()

        sitevar = Sitevar.get_or_insert('apistatus')
        old_value = sitevar.contents

        status = {}
        status['android'] = {}
        status['ios'] = {}
        status['max_season'] = int(self.request.get('max_year'))
        status['android']['latest_app_version'] = int(self.request.get('android_latest_version'))
        status['android']['min_app_version'] = int(self.request.get('android_min_version'))
        status['ios']['latest_app_version'] = int(self.request.get('ios_latest_version'))
        status['ios']['min_app_version'] = int(self.request.get('ios_min_version'))
        sitevar.contents = status
        sitevar.put()

        ApiStatusController.clear_cache_if_needed(old_value, status)

        self.redirect('/admin/apistatus')
