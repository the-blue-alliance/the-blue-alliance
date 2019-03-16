import json

from google.appengine.api import urlfetch

from tbans.consts.subscription_action_type import SubscriptionActionType
from tbans.consts.iid_error import IIDError
from tbans.models.requests.subscriptions.subscription_batch_response import SubscriptionBatchResponse
from tbans.utils.auth_utils import get_firebase_messaging_access_token


class SubscriptionBatchRequest:
    """ Represents a batch API request to the Instance ID API.

    https://developers.google.com/instance-id/reference/server#manage_relationship_maps_for_multiple_app_instances

    Attributes:
        tokens (list, string): List of device registration tokens.
        topic (string): Name of the topic for the request.
    """
    def __init__(self, tokens, topic, action_type):
        """
        Args:
            tokens (list, string): A non-empty list of device registration tokens. Also accepts a single device token as a string.
                List may not have more than 1000 elements.
            topic (string): Name of the topic for the request. May contain the ``/topics/`` prefix.
            action (SubscriptionActionType, int): Action to execute via the request - should be a SubscriptionActionType const
        """
        # Ensure our tokens are right - non-empty strings, in a list
        if isinstance(tokens, basestring):
            tokens = [tokens]
        if not isinstance(tokens, list) or not tokens:
            raise ValueError('SubscriptionBatchRequest tokens must be a string or a non-empty list of strings.')
        invalid_str = [t for t in tokens if not isinstance(t, basestring) or not t]
        if invalid_str:
            raise ValueError('SubscriptionBatchRequest tokens must be non-empty strings.')
        if len(tokens) > 1000:
            raise ValueError('SubscriptionBatchRequest tokens must have no more than 1000 tokens.')

        # Ensure our topic is right - format like `/topics/something`
        if not isinstance(topic, basestring) or not topic:
            raise ValueError('SubscriptionBatchRequest topic must be a non-empty string.')
        if not topic.startswith('/topics/'):
            topic = '/topics/{0}'.format(topic)

        if action_type not in SubscriptionActionType.batch_actions:
            raise ValueError('SubscriptionBatchRequest unsupported action {}.'.format(action_type))

        self.tokens = tokens
        self.topic = topic
        self._action_type = action_type

    def __str__(self):
        method = SubscriptionActionType.BATCH_METHODS[self._action_type]
        return 'SubscriptionBatchRequest(tokens={}, topic={}, method={})'.format(self.tokens, self.topic, method)

    @property
    def _json_string(self):
        """ JSON string representation of an SubscriptionBatchRequest object

        JSON for Subscription will look like...
        {
            "to": "/topics/{topic}",
            "registration_tokens": ["token1", "token2", ...],
        }

        Returns:
            string: JSON representation of the SubscriptionBatchRequest
        """
        return json.dumps({'to': self.topic, 'registration_tokens': self.tokens})

    @property
    def _batch_url(self):
        method = SubscriptionActionType.BATCH_METHODS[self._action_type]
        return 'https://iid.googleapis.com/iid/{}'.format(method)

    def send(self):
        """ Attempt to send SubscriptionBatchRequest

        Returns:
            SubscriptionBatchResponse
        """
        headers = {
            'Authorization': 'Bearer ' + get_firebase_messaging_access_token(),
            'Content-Type': 'application/json'
        }
        try:
            response = urlfetch.fetch(
                url=self._batch_url,
                payload=self._json_string,
                method='POST',
                headers=headers
            )
            return SubscriptionBatchResponse(tokens=self.tokens, response=response)
        except Exception, e:
            # https://cloud.google.com/appengine/docs/standard/python/refdocs/google.appengine.api.urlfetch_errors
            return SubscriptionBatchResponse(tokens=self.tokens, error=str(e))
