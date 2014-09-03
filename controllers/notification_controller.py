import logging

from base_controller import LoggedInHandler
from consts.client_type import ClientType
from models.mobile_client import MobileClient
from notifications.ping import PingNotification


class UserNotificationBroadcast(LoggedInHandler):

    '''
    Allows a user to ping a single one of their devices
    '''

    def post(self):
        self._require_login('/account/register')

        if not self.user_bundle.account.registered:
            self.redirect('/account/register')
            return None

        # Check to make sure that they aren't trying to edit another user
        real_account_id = self.user_bundle.account.key.id()
        check_account_id = self.request.get('account_id')
        if check_account_id == real_account_id:
            messaging_id = self.request.get('messaging_id')
            to_ping = MobileClient.query(MobileClient.user_id == real_account_id, MobileClient.messaging_id == messaging_id).fetch()
            if to_ping is not None:
                device = to_ping[0]
                # This makes sure that the client actually exists and that this user owns it
                if device.client_type == ClientType.WEBHOOK:
                    keys = {device.client_type: [(device.messaging_id, device.secret)]}
                else:
                    keys = {device.client_type: [device.messaging_id]}
                logging.info("url: "+str(messaging_id))
                logging.info("keys: "+str(keys))
                notification = PingNotification()
                notification.send(keys)
            self.redirect('/account')
        else:
            self.redirect('/')
