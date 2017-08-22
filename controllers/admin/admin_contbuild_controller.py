import tba_config
from controllers.base_controller import LoggedInHandler
from models.sitevar import Sitevar


class AdminContbuildController(LoggedInHandler):
    """
    Manage stuff regarding continuous deployment
    """
    def get(self, action):
        self._require_admin()
        # TODO only on prod
        if tba_config.DEBUG and False:
            # We only want to do this on prod
            self.abort(400)
            return
        if action == 'enable':
            self.enable_continuous_push()
            self.redirect('/admin/')
        elif action == 'disable':
            self.disable_continuous_push()
            self.redirect('/admin/')
        else:
            self.abort(404)

    @staticmethod
    def enable_continuous_push():
        status_sitevar = Sitevar.get_or_insert('apistatus', values_json="{}")
        status = status_sitevar.contents
        status['contbuild_enabled'] = True
        status_sitevar.contents = status
        status_sitevar.put()

    @staticmethod
    def disable_continuous_push():
        status_sitevar = Sitevar.get_or_insert('apistatus', values_json="{}")
        status = status_sitevar.contents
        status['contbuild_enabled'] = False
        status_sitevar.contents = status
        status_sitevar.put()
