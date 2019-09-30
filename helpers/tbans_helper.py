import firebase_admin
import logging

from consts.client_type import ClientType


def _firebase_app():
    try:
        return firebase_admin.get_app('tbans')
    except ValueError:
        return firebase_admin.initialize_app(name='tbans')


firebase_app = _firebase_app()


class TBANSHelper:

    """
    Helper class for sending push notifications via the FCM HTTPv1 API and sending data payloads to webhooks
    """

    @staticmethod
    def ping(client):
        """ Immediately dispatch a Ping to either FCM or a webhook """
        if client.client_type == ClientType.WEBHOOK:
            return TBANSHelper._ping_webhook(client)
        else:
            return TBANSHelper._ping_client(client)

    @staticmethod
    def _ping_client(client):
        client_type = client.client_type
        if client_type in ClientType.FCM_CLIENTS:
            from models.notifications.ping import PingNotification
            notification = PingNotification()

            from models.notifications.requests.fcm_request import FCMRequest
            fcm_request = FCMRequest(firebase_app, notification, tokens=[client.messaging_id])
            logging.info('Ping - {}'.format(str(fcm_request)))

            batch_response = fcm_request.send()
            if batch_response.failure_count > 0:
                response = batch_response.responses[0]
                logging.info('Error Sending Ping - {}'.format(response.exception))
                return False
            else:
                logging.info('Ping Sent')
        elif client_type == ClientType.OS_ANDROID:
            # Send old notifications to Android
            from notifications.ping import PingNotification
            notification = PingNotification()
            notification.send({client_type: [client.messaging_id]})
        else:
            raise Exception('Unsupported FCM client type: {}'.format(client_type))

        return True

    @staticmethod
    def _ping_webhook(client):
        from models.notifications.ping import PingNotification
        notification = PingNotification()

        from models.notifications.requests.webhook_request import WebhookRequest
        webhook_request = WebhookRequest(notification, client.messaging_id, client.secret)
        logging.info('Ping - {}'.format(str(webhook_request)))

        success = webhook_request.send()
        logging.info('Ping Sent')

        return success

    @staticmethod
    def verify_webhook(url, secret):
        """ Immediately dispatch a Verification to a webhook """
        from models.notifications.verification import VerificationNotification
        notification = VerificationNotification(url, secret)

        from models.notifications.requests.webhook_request import WebhookRequest
        webhook_request = WebhookRequest(notification, url, secret)
        logging.info('Verification - {}'.format(str(webhook_request)))

        webhook_request.send()
        logging.info('Verification Key - {}'.format(notification.verification_key))

        return notification.verification_key
