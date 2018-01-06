import os

from google.appengine.ext.webapp import template

from consts.landing_type import LandingType
from controllers.base_controller import LoggedInHandler
from models.sitevar import Sitevar


class AdminMainLandingEdit(LoggedInHandler):

    def get(self):
        self._require_admin()
        config = Sitevar.get_by_id('landing_config')
        config_data = config.contents if config else {}
        self.template_values['current_config'] = config_data
        self.template_values['current_landing'] = config_data.get('current_landing', '')
        self.template_values['landing_types'] = LandingType.NAMES
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/main_landing.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_admin()

        config = Sitevar.get_or_insert('landing_config')
        props = config.contents if config else {}
        new_props = {
            'current_landing': int(self.request.get('landing_type', LandingType.BUILDSEASON)),
        }
        for key in props.keys():
            if key == 'current_landing':
                continue
            val = self.request.get('prop_{}'.format(key), '')
            new_props[key] = val

        new_key = self.request.get('new_key', '')
        new_val = self.request.get('new_value', '')
        if new_key:
            new_props[new_key] = new_val

        config.contents = new_props
        config.put()

        self.redirect('/admin/main_landing')
