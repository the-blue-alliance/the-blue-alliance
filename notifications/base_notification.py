from controllers.gcm.gcm import GCMConnection
from consts.client_type import ClientType


class BaseNotification(object):

    '''
    Class that acts as a basic notification.
    To create a notification, call build() below
    passing in the correct client type
    '''

    def send(self, keys):
        self.keys = keys  # dict like {ClientType : [keys] }
        for client_type in ClientType.names.keys():
            self.render(client_type)

    '''
    This method will create platform specific notifications and send them to the platform specified
    Clients should implement the referenced methods in order to build the notification for each platform
    '''
    def render(self, client_type):
        if client_type == ClientType.OS_ANDROID and hasattr(self, "_render_android"):
            notification = self._render_android()
            self.send_android(notification)
        elif client_type == ClientTYpe.OS_IOS and hasattr(self, "_render_ios"):
            return self._render_ios()
        else:
            return None

    '''
    Subclasses should override this method and return a dict containing the payload of the notification.
    The dict should have two entries: 'message_type' (should be one of NotificationType) and 'message_data'
    '''
    def _build_dict(self):
        raise NotImplementedError("Subclasses must implement this method to build JSON data to send")

    def send_android(self, gcm_message):
        gcm_connection = GCMConnection()
        gcm_connection.notify_device(gcm_message)
