import logging

from protorpc import remote
from protorpc.wsgi import service

from tbans.models.service.messages import TBANSResponse, PingRequest, UpdateClientRequest, UpdateSubscriptionsRequest, VerificationRequest, VerificationResponse


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

    @remote.method(UpdateClientRequest, TBANSResponse)
    def update_client(self, request):
        """ Queue a task to update the subscription status for a user's device token. """
        self._validate_authentication()

        user_id = request.user_id
        token = request.token

        tag = "{}_{}".format(user_id, token)
        payload = {'user_id': user_id, 'token': token}
        TBANSService._add_to_tbans_queues(payload, tag)

        return TBANSResponse(code=200)

    @remote.method(UpdateSubscriptionsRequest, TBANSResponse)
    def update_subscriptions(self, request):
        """ Queue a task to update the subscription status for a user. """
        self._validate_authentication()

        user_id = request.user_id
        payload = {'user_id': user_id}
        TBANSService._add_to_tbans_queues(payload, user_id)

        return TBANSResponse(code=200)

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

    @staticmethod
    def _add_to_tbans_queues(payload, tag):
        from tbans.workers.subscription_worker import SubscriptionWorkerHandler
        pull_queue = SubscriptionWorkerHandler.task_queue()

        import json
        json_payload = json.dumps(payload)

        from google.appengine.api import taskqueue
        # Add task to our pull queue - we'll pull these off and de-dupe retries.
        pull_queue.add(taskqueue.Task(payload=json_payload, method='PULL', tag=tag))

        # Notify a worker to check the appropriate queue for tasks.
        taskqueue.add(
            queue_name='tbans-notify-worker',
            url='/notify_subscription_worker',
            params={'tag': tag},
            target='tbans'
        )


app = service.service_mappings([('/tbans.*', TBANSService)])
