from protorpc import transport

from tba.consts.client_type import ClientType

from google.appengine.api.app_identity import app_identity

from tbans.models.service.messages import FCM, Webhook
from tbans.tbans_service import TBANSService


# Will always return a TBANSResponse-like object (code/message)
class TBANSHelper(object):

    """
    Helper class for sending push notifications.
    Methods here should call the TBANS API to dispatch/queue notifications
    """

    @staticmethod
    def _create_service():
        url = 'https://{}/tbans/tbans'.format(app_identity.get_default_version_hostname())
        return TBANSService.Stub(transport.HttpTransport(url))

    @staticmethod
    def ping(client):
        if client.client_type == ClientType.WEBHOOK:
            return TBANSHelper.ping_webhook(client)
        else:
            return TBANSHelper.ping_client(client)

    @staticmethod
    def ping_client(client):
        service = TBANSHelper._create_service()
        return service.ping(fcm=FCM(token=client.messaging_id))

    @staticmethod
    def update_favorites(user_id, sending_device_key=None):
        service = TBANSHelper._create_service()
        return service.update_favorites(user_id=user_id, sending_device_key=sending_device_key)

    @staticmethod
    def update_subscriptions(user_id, sending_device_key=None):
        service = TBANSHelper._create_service()
        return service.update_subscriptions(user_id=user_id, sending_device_key=sending_device_key)

    @staticmethod
    def ping_webhook(client):
        service = TBANSHelper._create_service()
        return service.ping(webhook=Webhook(url=client.messaging_id, secret=client.secret))

    @staticmethod
    def verify_webhook(url, secret):
        service = TBANSHelper._create_service()
        return service.verification(webhook=Webhook(url=url, secret=secret))
