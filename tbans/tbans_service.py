import logging

from protorpc import remote
from protorpc.wsgi import service

from tba.consts.notification_type import NotificationType

from tbans.consts.vertical_type import VerticalType
from tbans.models.service.messages import TBANSResponse, PingRequest, \
    UpdateMyTBARequest, VerificationRequest, VerificationResponse


package = 'tbans'


class TBANSService(remote.Service):
    """ The Blue Alliance Notification Service.... Service """

    def __init__(self):
        import firebase_admin
        try:
            self._firebase_app = firebase_admin.get_app('tbans')
        except ValueError:
            self._firebase_app = firebase_admin.initialize_app(name='tbans')

    def _validate_authentication(self):
        import tba_config
        # Allow all requests in debug mode
        if tba_config.DEBUG:
            return

        incoming_app_id = self.request_state.headers.get('X-Appengine-Inbound-Appid', None)
        if incoming_app_id is None:
            raise remote.ApplicationError('Unauthenticated')

        from google.appengine.api.app_identity import app_identity
        if not app_identity.get_application_id() == incoming_app_id:
            raise remote.ApplicationError('Unauthenticated')

    def _application_error(self, message):
        """ Helper method to log and return a 400 TBANSResponse """
        # TODO: Monitor these
        logging.error(message)
        return TBANSResponse(code=400, message=message)

    @remote.method(PingRequest, TBANSResponse)
    def ping(self, request):
        """ Immediately dispatch a Ping to either FCM or a webhook """
        self._validate_authentication()

        if request.fcm and request.webhook:
            return self._application_error('Cannot ping both FCM and webhook')

        from tbans.models.notifications.ping import PingNotification
        notification = PingNotification()

        if request.fcm:
            # An FCM request can still exist, I believe. It can take some notification and delivery options
            from tbans.requests.fcm_request import FCMRequest
            fcm_request = FCMRequest(self._firebase_app, notification, tokens=[request.fcm.token])
            logging.info('Ping - {}'.format(str(fcm_request)))

            fcm_request.send()
            logging.info('Ping Sent')

            return TBANSResponse(code=200)
        elif request.webhook:
            from tbans.requests.webhook_request import WebhookRequest
            webhook_request = WebhookRequest(notification, request.webhook.url, request.webhook.secret)
            logging.info('Ping - {}'.format(str(webhook_request)))

            webhook_request.send()
            logging.info('Ping Sent')

            return TBANSResponse(code=200)
        else:
            return self._application_error('Did not specify FCM or webhook to ping')

    @remote.method(UpdateMyTBARequest, TBANSResponse)
    def update_favorites(self, request):
        """ Send a notification to all mobile clients for a user to update myTBA favorites """
        return self._update_mytba(request, NotificationType.UPDATE_FAVORITES)

    @remote.method(UpdateMyTBARequest, TBANSResponse)
    def update_subscriptions(self, request):
        """ Send a notification to all mobile clients for a user to update myTBA favorites """
        return self._update_mytba(request, NotificationType.UPDATE_SUBSCRIPTIONS)

    @remote.method(VerificationRequest, VerificationResponse)
    def verification(self, request):
        """ Immediately dispatch a Verification to a webhook """
        self._validate_authentication()

        from tbans.models.notifications.verification import VerificationNotification
        notification = VerificationNotification(request.webhook.url, request.webhook.secret)

        from tbans.requests.webhook_request import WebhookRequest
        webhook_request = WebhookRequest(notification, request.webhook.url, request.webhook.secret)
        logging.info('Verification - {}'.format(str(webhook_request)))

        webhook_request.send()
        logging.info('Verification Key - {}'.format(notification.verification_key))

        return VerificationResponse(code=200, verification_key=notification.verification_key)

    def _update_mytba(self, request, notification_type):
        """ Shared method to queue a myTBA notification """
        self._validate_authentication()

        payload = {
            'user_id': request.user_id,
            'notification_type': notification_type
        }

        if request.sending_device_key:
            payload['sending_device_key'] = request.sending_device_key

        TBANSService._add_to_tbans_queue(payload, vertical_types=[VerticalType.FCM])
        return TBANSResponse(code=200)

    @staticmethod
    def _add_to_tbans_queue(payload, vertical_types=VerticalType.ENABLED_VERTICALS):
        from google.appengine.api import taskqueue
        for vertical_type in vertical_types:
            payload['vertical_type'] = vertical_type
            taskqueue.add(
                queue_name='tbans-notifications',
                url='/notify',
                params=payload,
                target='tbans'
            )


app = service.service_mappings([('/tbans.*', TBANSService)])
