from google.appengine.ext import ndb

from base_controller import LoggedInHandler
from models.account import Account
from models.mobile_client import MobileClient


class UserNotificationBroadcast(LoggedInHandler):

    """
    Allows a user to ping a single one of their clients
    """

    def post(self):
        self._require_registration()

        # Check to make sure that they aren't trying to edit another user
        current_user_account_id = self.user_bundle.account.key.id()
        target_account_id = self.request.get('account_id')
        if target_account_id == current_user_account_id:
            client_id = self.request.get('client_id')

            client = MobileClient.get_by_id(int(client_id), parent=ndb.Key(Account, current_user_account_id))
            if client is not None:
                from helpers.tbans_helper import TBANSHelper
                success = TBANSHelper.ping(client)
                if success:
                    return self.redirect('/account?ping_sent=1')
                else:
                    return self.redirect('/account?ping_sent=0')

        self.redirect('/')
