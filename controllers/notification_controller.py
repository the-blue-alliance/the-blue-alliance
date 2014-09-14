from base_controller import LoggedInHandler
from consts.client_type import ClientType
from models.mobile_client import MobileClient
from notifications.ping import PingNotification


class UserNotificationBroadcast(LoggedInHandler):

    """
    Allows a user to ping a single one of their clients
    """

    def post(self):
        self._require_login('/account/register')
        self._require_registration('/account/register')

        # Check to make sure that they aren't trying to edit another user
        current_user_account_id = self.user_bundle.account.key.id()
        target_account_id = self.request.get('account_id')
        if target_account_id == current_user_account_id:
            messaging_id = self.request.get('messaging_id')
            to_ping = MobileClient.query(MobileClient.user_id == current_user_account_id, MobileClient.messaging_id == messaging_id).fetch()
            if to_ping is not None:
                client = to_ping[0]
                # This makes sure that the client actually exists and that this user owns it
                if client.client_type == ClientType.WEBHOOK:
                    keys = {client.client_type: [(client.messaging_id, client.secret)]}
                else:
                    keys = {client.client_type: [client.messaging_id]}
                notification = PingNotification()
                notification.send(keys)
            self.redirect('/account')
        else:
            self.redirect('/')
