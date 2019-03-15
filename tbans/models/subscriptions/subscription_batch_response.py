from tbans.models.subscriptions.subscriber import Subscriber
from tbans.models.subscriptions.subscription_response import SubscriptionResponse
from tbans.utils.json_utils import json_string_to_dict


class SubscriptionBatchResponse(SubscriptionResponse):
    """ Response for a SubscriptionBatchRequest object.

    Attributes:
        subscribers (list, Subscriber): List of Subscriber objects (token, errror) for request.
    """
    def __init__(self, tokens, response=None, error=None):
        """
        Error JSON from FCM will look like...
        {"error":"MissingAuthorization"}

        Success JSON from FCM will look like...
        {
          "results":[...]
        }

        We can mix/match error and success, such as...
        {
          "results":[
            {},
            {"error":"NOT_FOUND"},
            {},
          ]
        }

        Note: These come back in a particular order, so we'll need to match up the results with the sent tokens + errors

        https://github.com/firebase/firebase-admin-python/blob/47345a1ecaf51611c07a7414d7e8afe50ea9decc/firebase_admin/messaging.py#L323

        Args:
            tokens (list, string): A non-empty list of device registration tokens.
        """
        super(SubscriptionBatchResponse, self).__init__(response=response, error=error)

        # Ensure our tokens are right - non-empty strings, in a list
        if not isinstance(tokens, list) or not tokens:
            raise ValueError('SubscriptionBatchResponse tokens must be a non-empty list of strings.')
        invalid_str = [t for t in tokens if not isinstance(t, basestring) or not t]
        if invalid_str:
            raise ValueError('SubscriptionBatchResponse tokens must be non-empty strings.')

        results = self.data.get('results', [])
        if not isinstance(results, list) or (not results and not self.error):
            raise ValueError('SubscriptionBatchResponse results must be a non-empty list.')

        self.subscribers = [Subscriber(token, result) for token, result in zip(tokens, results)]

    def __str__(self):
        return 'SubscriptionResponse(subscribers={})'.format([str(s) for s in self.subscribers])
