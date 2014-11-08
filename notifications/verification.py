import hashlib
import time

from consts.notification_type import NotificationType
from notifications.base_notification import BaseNotification


class VerificationNotification(BaseNotification):

    def __init__(self, url, secret):
        self.url = url
        self.secret = secret
        self.generate_key()

    def generate_key(self):
        ch = hashlib.sha1()
        ch.update(str(time.time()))
        ch.update(self.url)
        ch.update(self.secret)
        self.verification_key = ch.hexdigest()

    def _build_dict(self):
        data = {}
        data['message_type'] = NotificationType.type_names[NotificationType.VERIFICATION]
        data['message_data'] = {'verification_key': self.verification_key}
        return data
