import logging

from protorpc import remote
from protorpc.wsgi import service

from tbans.models.service.messages import TBANSResponse, PingRequest, VerificationRequest, VerificationResponse


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
            fcm_request = FCMRequest(self._firebase_app, notification, token=request.fcm.token, topic=request.fcm.topic, condition=request.fcm.condition)
            logging.info('Ping - {}'.format(str(fcm_request)))

            message_id = fcm_request.send()
            logging.info('Ping Sent - {}'.format(str(message_id)))
            return TBANSResponse(code=200, message=message_id)
        elif request.webhook:
            from tbans.requests.webhook_request import WebhookRequest
            webhook_request = WebhookRequest(notification, request.webhook.url, request.webhook.secret)
            logging.info('Ping - {}'.format(str(webhook_request)))

            webhook_request.send()
            logging.info('Ping Sent')

            return TBANSResponse(code=200)
        else:
            return self._application_error('Did not specify FCM or webhook to ping')

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


app = service.service_mappings([('/tbans.*', TBANSService)])
