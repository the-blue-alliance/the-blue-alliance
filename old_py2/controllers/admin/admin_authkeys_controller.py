import json
import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from models.sitevar import Sitevar


class AdminAuthKeys(LoggedInHandler):
    """
    A place to see all the connected API keys
    """
    def get(self):
        self._require_admin()
        google_secrets = Sitevar.get_or_insert('google.secrets')
        firebase_secrets = Sitevar.get_or_insert('firebase.secrets')
        fmsapi_secrets = Sitevar.get_or_insert('fmsapi.secrets')
        mobile_clientIds = Sitevar.get_or_insert('mobile.clientIds')
        gcm_serverKey = Sitevar.get_or_insert('gcm.serverKey')
        twitch_secrets = Sitevar.get_or_insert('twitch.secrets')
        livestream_secrets = Sitevar.get_or_insert('livestream.secrets')

        fmsapi_keys = fmsapi_secrets.contents if fmsapi_secrets and isinstance(fmsapi_secrets.contents, dict) else {}
        clientIds = mobile_clientIds.contents if mobile_clientIds and isinstance(mobile_clientIds.contents, dict) else {}
        self.template_values.update({
            'google_secret': google_secrets.contents.get('api_key', "") if google_secrets else "",
            'firebase_secret': firebase_secrets.contents.get('FIREBASE_SECRET', "") if firebase_secrets else "",
            'fmsapi_user': fmsapi_keys.get('username', ''),
            'fmsapi_secret': fmsapi_keys.get('authkey', ''),
            'web_client_id': clientIds.get('web', ''),
            'android_client_id': clientIds.get('android', ''),
            'ios_client_id': clientIds.get('ios', ''),
            'gcm_key': gcm_serverKey.contents.get("gcm_key", "") if gcm_serverKey else "",
            'twitch_secret': twitch_secrets.contents.get('client_id', "") if twitch_secrets else "",
            'livestream_secret': livestream_secrets.contents.get('api_key', "") if livestream_secrets else "",
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/authkeys.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_admin()

        google_secrets = Sitevar.get_or_insert('google.secrets')
        firebase_secrets = Sitevar.get_or_insert('firebase.secrets')
        fmsapi_secrets = Sitevar.get_or_insert('fmsapi.secrets')
        mobile_clientIds = Sitevar.get_or_insert('mobile.clientIds')
        gcm_serverKey = Sitevar.get_or_insert('gcm.serverKey')
        twitch_secrets = Sitevar.get_or_insert('twitch.secrets')
        livestream_secrets = Sitevar.get_or_insert('livestream.secrets')

        google_key = self.request.get("google_secret")
        firebase_key = self.request.get("firebase_secret")
        fmsapi_user = self.request.get("fmsapi_user")
        fmsapi_secret = self.request.get("fmsapi_secret")
        web_client_id = self.request.get("web_client_id")
        android_client_id = self.request.get("android_client_id")
        ios_client_id = self.request.get("ios_client_id")
        gcm_key = self.request.get("gcm_key")
        twitch_client_id = self.request.get("twitch_secret")
        livestream_key = self.request.get("livestream_secret")

        google_secrets.contents = {'api_key': google_key}
        firebase_secrets.contents = {'FIREBASE_SECRET': firebase_key}
        fmsapi_secrets.contents = {'username': fmsapi_user, 'authkey': fmsapi_secret}
        mobile_clientIds.contents = {'web': web_client_id, 'android': android_client_id,
                                     'ios': ios_client_id}
        gcm_serverKey.contents = {'gcm_key': gcm_key}
        twitch_secrets.contents = {'client_id': twitch_client_id}
        livestream_secrets.contents = {'api_key': livestream_key}

        google_secrets.put()
        firebase_secrets.put()
        fmsapi_secrets.put()
        mobile_clientIds.put()
        gcm_serverKey.put()
        twitch_secrets.put()
        livestream_secrets.put()

        self.redirect('/admin/authkeys')
