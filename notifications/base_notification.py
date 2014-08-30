from consts.client_type import ClientType


class BaseNotification(object):

    '''
    Class that acts as a basic notification.
    To create a notification, call build() below
    passing in the correct client type
    '''

    def build(self, client_type, keys):
        self.keys = keys
        if client_type == ClientType.OS_ANDROID:
            return self._render_android()
        elif client_type == ClientTYpe.OS_IOS:
            return self._render_ios()
        else:
            return None

    def _render_android(self):
        raise NotImplementedError("Subclasses must override this method if they wish to send Android notifications")

    def _render_ios(self):
        raise NotImplementedError("Subclasses must override this method if they wish to send iOS notifications")

