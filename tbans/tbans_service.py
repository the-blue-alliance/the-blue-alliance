import logging
import tba_config

from google.appengine.api.app_identity import app_identity

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
        # Allow all requests in debug mode
        if tba_config.DEBUG:
            return

        # Ignore auth check during tests
        if self.testing:
            return

        incoming_app_id = self.request_state.headers.get('X-Appengine-Inbound-Appid', None)
        if incoming_app_id is None:
            raise remote.ApplicationError('Unauthenticated')

        if not app_identity.get_application_id() == incoming_app_id:
            raise remote.ApplicationError('Unauthenticated')

    @remote.method(PingRequest, TBANSResponse)
    def ping(self, request):
        """ Immediately dispatch a Ping to either FCM or a webhook """
        self._validate_authentication()

        if request.fcm and request.webhook:
            return TBANSResponse(code=400, message='Cannot ping both FCM and webhook')

        from tbans.models.notifications.ping import PingNotification
        notification = PingNotification()

        if request.fcm:
            from tbans.models.messages.fcm_message import FCMMessage
            message = FCMMessage(notification, token=request.fcm.token, topic=request.fcm.topic, condition=request.fcm.condition)
            logging.info('Ping - {}'.format(str(message)))

            response = message.send()
            logging.info('Ping Response - {}'.format(str(response)))
            return TBANSResponse(code=response.status_code, message=response.content)
        elif request.webhook:
            from tbans.models.messages.webhook_message import WebhookMessage
            message = WebhookMessage(notification, request.webhook.url, request.webhook.secret)
            logging.info('Ping - {}'.format(str(message)))

            response = message.send()
            logging.info('Ping Response - {}'.format(str(response)))
            return TBANSResponse(code=response.status_code, message=response.content)
        else:
            return TBANSResponse(code=400, message='Did not specify FCM or webhook to ping')

    @remote.method(VerificationRequest, VerificationResponse)
    def verification(self, request):
        """ Immediately dispatch a Verification to a webhook """
        self._validate_authentication()

        from tbans.models.notifications.verification import VerificationNotification
        notification = VerificationNotification(request.webhook.url, request.webhook.secret)

        from tbans.models.messages.webhook_message import WebhookMessage
        message = WebhookMessage(notification, request.webhook.url, request.webhook.secret)
        logging.info('Verification - {}'.format(str(message)))

        response = message.send()
        logging.info('Verification Response - {}'.format(str(response)))
        return VerificationResponse(code=response.status_code, message=response.content, verification_key=notification.verification_key)


app = service.service_mappings([('/tbans.*', TBANSService)])
