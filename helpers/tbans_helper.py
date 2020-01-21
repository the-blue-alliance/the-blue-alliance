import firebase_admin
import logging

from consts.client_type import ClientType

from google.appengine.ext import deferred

from models.mobile_client import MobileClient


MAXIMUM_BACKOFF = 32


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

    @classmethod
    def broadcast(cls, client_types, title, message, url=None, app_version=None):
        from models.notifications.broadcast import BroadcastNotification
        notification = BroadcastNotification(title, message, url, app_version)

        # Send to FCM clients
        fcm_client_types = [ct for ct in client_types if ct in ClientType.FCM_CLIENTS]
        if fcm_client_types:
            clients = MobileClient.query(MobileClient.client_type.IN(fcm_client_types)).fetch()
            if clients:
                deferred.defer(
                    cls._send_fcm,
                    clients,
                    notification,
                    _queue="push-notifications",
                    _url='/_ah/queue/deferred_notification_send'
                )

        # Send to webhooks
        if ClientType.WEBHOOK in client_types:
            clients = MobileClient.query(MobileClient.client_type == ClientType.WEBHOOK).fetch()
            if clients:
                deferred.defer(
                    cls._send_webhook,
                    clients,
                    notification,
                    _queue="push-notifications",
                    _url='/_ah/queue/deferred_notification_send'
                )

        if ClientType.OS_ANDROID in client_types:
            from helpers.push_helper import PushHelper
            users = PushHelper.get_all_mobile_clients([ClientType.OS_ANDROID])
            keys = PushHelper.get_client_ids_for_users(users)

            from notifications.broadcast import BroadcastNotification
            notification = BroadcastNotification(title, message, url, app_version)
            notification.send(keys)

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

    @classmethod
    def _send_fcm(cls, clients, notification, backoff_iteration=0):
        # Only send to FCM clients if notifications are enabled
        if not cls._notifications_enabled():
            return 1

        # Only allow so many retries
        backoff_time = 2 ** backoff_iteration
        if backoff_time > MAXIMUM_BACKOFF:
            return 2

        # Make sure we're only sending to FCM clients
        clients = [client for client in clients if client.client_type in ClientType.FCM_CLIENTS]

        from models.notifications.requests.fcm_request import FCMRequest, MAXIMUM_TOKENS
        # We can only send to so many FCM clients at a time - send to our clients across several requests
        for subclients in [clients[i:i + MAXIMUM_TOKENS] for i in range(0, len(clients), MAXIMUM_TOKENS)]:
            fcm_request = FCMRequest(firebase_app, notification, tokens=[client.messaging_id for client in subclients])
            logging.info(str(fcm_request))

            batch_response = fcm_request.send()
            retry_clients = []

            # Handle our failed sends - this might include logging/alerting, removing old clients, or retrying sends
            from firebase_admin.exceptions import InvalidArgumentError, InternalError, UnavailableError
            from firebase_admin.messaging import QuotaExceededError, SenderIdMismatchError, ThirdPartyAuthError, UnregisteredError
            for index, response in enumerate([response for response in batch_response.responses if not response.success]):
                client = subclients[index]
                if isinstance(response.exception, UnregisteredError):
                    logging.info('Deleting unregistered client with ID: {}'.format(client.messaging_id))
                    MobileClient.delete_for_messaging_id(client.messaging_id)
                elif isinstance(response.exception, SenderIdMismatchError):
                    logging.info('Deleting mismatched client with ID: {}'.format(client.messaging_id))
                    MobileClient.delete_for_messaging_id(client.messaging_id)
                elif isinstance(response.exception, QuotaExceededError):
                    logging.error('Qutoa exceeded - retrying client...')
                    retry_clients.append(client)
                elif isinstance(response.exception, ThirdPartyAuthError):
                    logging.critical('Third party error sending to FCM - {}'.format(response.exception))
                elif isinstance(response.exception, InvalidArgumentError):
                    logging.critical('Invalid argument when sending to FCM - {}'.format(response.exception))
                elif isinstance(response.exception, InternalError):
                    logging.error('Interal FCM error - retrying client...')
                    retry_clients.append(client)
                elif isinstance(response.exception, UnavailableError):
                    logging.error('FCM unavailable - retrying client...')
                    retry_clients.append(client)
                else:
                    debug_string = cls._debug_string(response.exception)
                    logging.error('Unhandled FCM error for {} - {}'.format(client.messaging_id, debug_string))

            if retry_clients:
                # Try again, with exponential backoff
                deferred.defer(
                    cls._send_fcm,
                    retry_clients,
                    notification,
                    backoff_iteration + 1,
                    _countdown=backoff_time,
                    _queue="push-notifications",
                    _url='/_ah/queue/deferred_notification_send'
                )

        return 0

    @classmethod
    def _send_webhook(cls, clients, notification):
        # Only send to webhooks if notifications are enabled
        if not cls._notifications_enabled():
            return 1

        # Make sure we're only sending to webhook clients
        clients = [client for client in clients if client.client_type == ClientType.WEBHOOK]
        # Only send to verified webhooks
        clients = [client for client in clients if client.verified]

        from models.notifications.requests.webhook_request import WebhookRequest
        for client in clients:
            webhook_request = WebhookRequest(notification, client.messaging_id, client.secret)
            logging.info(str(webhook_request))

            webhook_request.send()

        return 0

    # Returns a list of debug strings for a FirebaseException
    @classmethod
    def _debug_string(cls, exception):
        debug_strings = [exception.code, exception.message]
        if exception.http_response:
            debug_strings.append(str(exception.http_response.json()))
        return ' / '.join(debug_strings)

    @classmethod
    def _notifications_enabled(cls):
        from sitevars.notifications_enable import NotificationsEnable
        return NotificationsEnable.notifications_enabled()
