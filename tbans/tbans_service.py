import logging

from protorpc import remote
from protorpc.wsgi import service

from tbans.models.service.messages import TBANSResponse, PingRequest, VerificationRequest, VerificationResponse


package = 'tbans'


class TBANSService(remote.Service):
    """ The Blue Alliance Notification Service.... Service """

    def __init__(self, testing=False):
        super(TBANSService, self).__init__()
        self.testing = testing

    def _validate_authentication(self):
        import tba_config
        # Allow all requests in debug mode
        if tba_config.DEBUG:
            return

        # Ignore auth check during tests
        if self.testing:
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
            from tbans.models.requests.notifications.fcm_request import FCMRequest
            fcm_request = FCMRequest(notification, token=request.fcm.token, topic=request.fcm.topic, condition=request.fcm.condition)
            logging.info('Ping - {}'.format(str(fcm_request)))

            response = fcm_request.send()
            logging.info('Ping Response - {}'.format(str(response)))
            return TBANSResponse(code=response.status_code, message=response.content)
        elif request.webhook:
            from tbans.models.requests.notifications.webhook_request import WebhookRequest
            webhook_request = WebhookRequest(notification, request.webhook.url, request.webhook.secret)
            logging.info('Ping - {}'.format(str(webhook_request)))

            response = webhook_request.send()
            logging.info('Ping Response - {}'.format(str(response)))
            return TBANSResponse(code=response.status_code, message=response.content)
        else:
            return self._application_error('Did not specify FCM or webhook to ping')

    @remote.method(VerificationRequest, VerificationResponse)
    def verification(self, request):
        """ Immediately dispatch a Verification to a webhook """
        self._validate_authentication()

        from tbans.models.notifications.verification import VerificationNotification
        notification = VerificationNotification(request.webhook.url, request.webhook.secret)

        from tbans.models.requests.notifications.webhook_request import WebhookRequest
        webhook_request = WebhookRequest(notification, request.webhook.url, request.webhook.secret)
        logging.info('Verification - {}'.format(str(webhook_request)))

        response = webhook_request.send()
        logging.info('Verification Response - {}'.format(str(response)))
        return VerificationResponse(code=response.status_code, message=response.content, verification_key=notification.verification_key)


app = service.service_mappings([('/tbans.*', TBANSService)])
