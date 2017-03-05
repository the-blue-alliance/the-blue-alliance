from controllers.base_controller import LoggedInHandler
from template_engine import jinja2_engine


class BlueZoneDebugHandler(LoggedInHandler):
    def get(self):
        self._require_admin()

        self.template_values.update({})

        self.response.out.write(jinja2_engine.render('bluezone_debug.html', self.template_values))
