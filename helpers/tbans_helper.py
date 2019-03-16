from consts.client_type import ClientType


class TBANSHelper(object):
    """
    Helper class for sending push notifications.
    Methods here should call the TBANS API to dispatch/queue notifications.
    Will always return a TBANSResponse-like object (code/message).
    """

    @staticmethod
    def _create_service():
        from google.appengine.api.app_identity import app_identity
        url = 'https://{}/tbans/tbans'.format(app_identity.get_default_version_hostname())

        from protorpc.transport import HttpTransport
        from tbans.tbans_service import TBANSService
        return TBANSService.Stub(HttpTransport(url))

    @staticmethod
    def ping(client):
        if client.client_type == ClientType.WEBHOOK:
            return TBANSHelper.ping_webhook(client)
        else:
            return TBANSHelper.ping_client(client)

    @staticmethod
    def ping_client(client):
        service = TBANSHelper._create_service()

        from tbans.models.service.messages import FCM
        return service.ping(fcm=FCM(token=client.messaging_id))

    @staticmethod
    def ping_webhook(client):
        service = TBANSHelper._create_service()

        from tbans.models.service.messages import Webhook
        return service.ping(webhook=Webhook(url=client.messaging_id, secret=client.secret))

    @staticmethod
    def update_client(client):
        if client.client_type not in ClientType.FCM_CLIENTS:
            return

        service = TBANSHelper._create_service()
        return service.update_client(user_id=client.user_id, token=client.messaging_id)

    @staticmethod
    def update_subscriptions(user_id):
        service = TBANSHelper._create_service()
        return service.update_subscriptions(user_id=user_id)

    @staticmethod
    def verify_webhook(url, secret):
        service = TBANSHelper._create_service()

        from tbans.models.service.messages import Webhook
        return service.verification(webhook=Webhook(url=url, secret=secret))
