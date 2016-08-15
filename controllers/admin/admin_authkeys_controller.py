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
        google_secrets = Sitevar.get_by_id('google.secrets')
        firebase_secrets = Sitevar.get_by_id('firebase.secrets')
        fmsapi_secrets = Sitevar.get_by_id('fmsapi.secrets')
        mobile_clientIds = Sitevar.get_by_id('mobile.clientIds')
        gcm_serverKey = Sitevar.get_by_id('gcm.serverKey')

        fmsapi_keys = fmsapi_secrets.contents if fmsapi_secrets else {}
        clientIds = mobile_clientIds.contents if mobile_clientIds else {}
        self.template_values.update({
            'google_secret': google_secrets.contents.get('api_key', "") if google_secrets else "",
            'firebase_secret': firebase_secrets.contents.get('FIREBASE_SECRET', "") if firebase_secrets else "",
            'fmsapi_user': fmsapi_keys.get('username', ''),
            'fmsapi_secret': fmsapi_keys.get('authkey', ''),
            'web_client_id': clientIds.get('web', ''),
            'android_client_id': clientIds.get('android', ''),
            'gcm_key': gcm_serverKey.contents if gcm_serverKey else "",
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

        google_key = self.request.get("google_secret")
        firebase_key = self.request.get("firebase_secret")
        fmsapi_user = self.request.get("fmsapi_user")
        fmsapi_secret = self.request.get("fmsapi_secret")
        web_client_id = self.request.get("web_client_id")
        android_client_id = self.request.get("android_client_id")
        gcm_key = self.request.get("gcm_key")

        google_secrets.contents = {'api_key': google_key}
        firebase_secrets.contents = {'FIREBASE_SECRET': firebase_key}
        fmsapi_secrets.contents = {'username': fmsapi_user, 'authkey': fmsapi_secret}
        mobile_clientIds.contents = {'web': web_client_id, 'android': android_client_id}
        gcm_serverKey.contents = gcm_key

        google_secrets.put()
        firebase_secrets.put()
        fmsapi_secrets.put()
        mobile_clientIds.put()
        gcm_serverKey.put()

        self.redirect('/admin/authkeys')
