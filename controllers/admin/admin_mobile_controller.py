import logging
import os
import traceback

from google.appengine.ext import deferred
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from consts.client_type import ClientType
from controllers.base_controller import LoggedInHandler
from helpers.notification_helper import NotificationHelper
from models.mobile_client import MobileClient
from models.sitevar import Sitevar


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

        var = Sitevar.get_by_id('notifications.enable')
        if var is None or not var.values_json == "true":
            push_enabled = False
        else:
            push_enabled = True

        self.template_values.update({
            'mobile_users': all_clients.count(),
            'android_users': android,
            'ios_users': ios,
            'webhooks': webhook,
            'broadcast_success': self.request.get('broadcast_success'),
            'push_enabled': push_enabled,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/mobile_dashboard.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_admin()

        user_id = self.user_bundle.account.key.id()
        action = self.request.get('enable')
        sitevar = Sitevar.get_or_insert('notifications.enable')
        if action == "true":
            sitevar.values_json = "true"
            logging.info("User {} enabled push notificatios".format(user_id))
        else:
            sitevar.values_json = "false"
            logging.info("User {} disabled push notification".format(user_id))
        sitevar.put()

        self.redirect('/admin/mobile')


class AdminMobileWebhooks(LoggedInHandler):
    """
    Details on webhooks
    """
    def get(self):
        self._require_admin()

        webhooks = MobileClient.query(MobileClient.client_type == ClientType.WEBHOOK).fetch()

        self.template_values.update({
            'webhooks': webhooks,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/mobile_webhooks_dashboard.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminBroadcast(LoggedInHandler):
    """
    Send a push notification to all connected users
    """
    def get(self):
        self._require_admin()

        error = ""
        if self.request.get('error') == "clients":
            error = "You must select at least one client type"
        elif self.request.get('error') == "title":
            error = "You must supply a title"
        elif self.request.get('error') == "message":
            error = "You must supply a message"
        elif self.request.get('error') == "sending":
            error = "A backed error occured sending the broadcast. Check the logs for details"

        self.template_values.update({
            'OS_ANDROID': ClientType.OS_ANDROID,
            'OS_IOS': ClientType.OS_IOS,
            'WEBHOOK': ClientType.WEBHOOK,
            'error': error,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/send_broadcast.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_admin()

        user_id = self.user_bundle.account.key.id()
        clients = self.request.get_all('client_types')
        title = self.request.get('title')
        message = self.request.get('message')
        url = self.request.get('url')
        app_version = self.request.get('app_version')

        error = ""
        if not clients:
            error = "clients"
        elif not title:
            error = "title"
        elif not message:
            error = "message"
        if error:
            self.redirect('/admin/mobile/broadcast?error={}'.format(error))
            return

        try:
            clients = [int(c) for c in clients]
            deferred.defer(NotificationHelper.send_broadcast, clients, title, message, url, app_version, _queue="admin")
            logging.info('User {} sent broadcast'.format(user_id))
        except Exception, e:
            logging.error("Error sending broadcast: {}".format(str(e)))
            logging.error("Trace: {}".format(traceback.format_exc()))
            self.redirect('/admin/mobile/broadcast?error=sending')
            return
        self.redirect('/admin/mobile?broadcast_success=1')
