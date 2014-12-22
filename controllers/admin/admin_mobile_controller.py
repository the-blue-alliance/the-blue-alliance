import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from consts.client_type import ClientType
from controllers.base_controller import LoggedInHandler
from models.mobile_client import MobileClient


class AdminMobile(LoggedInHandler):
    """
    Administrate connected mobile clients
    """
    def get(self):
        self._require_admin()

        all_clients = MobileClient.query()
        android = all_clients.filter(MobileClient.client_type == ClientType.OS_ANDROID).count()
        ios = all_clients.filter(MobileClient.client_type == ClientType.OS_IOS).count()
        webhook = all_clients.filter(MobileClient.client_type == ClientType.WEBHOOK).count()

        self.template_values.update({
            'mobile_users': all_clients.count(),
            'android_users': android,
            'ios_users': ios,
            'webhooks': webhook,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/mobile_dashboard.html')
        self.response.out.write(template.render(path, self.template_values))
