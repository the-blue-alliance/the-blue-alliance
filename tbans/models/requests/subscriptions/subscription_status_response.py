from tbans.models.requests.subscriptions.subscription_response import SubscriptionResponse


class SubscriptionStatusResponse(SubscriptionResponse):
    """ Representation of a subscriber's status from the Instance ID status API.

    Attributes:
        subscriptions: (list, string): List of topics the user is subscribed to - may be empty.
    """
    def __init__(self, response=None, error=None):
        """
        Success JSON will look like...

        {
            "applicationVersion": "1.0.2",
            "application": "com.the-blue-alliance.zach-dev",
            "scope": "*",
            "authorizedEntity": "244307294958",
            "rel": {
                "topics": {
                    "broadcasts": {"addDate":"2019-02-15"}
                }
            },
            "platform":"IOS"
        }

        Error JSON will look like...
        {
            "error": "InvalidToken"
        }
        """
        super(SubscriptionStatusResponse, self).__init__(response=response, error=error)

        relations = self.data.get('rel', {})
        if not isinstance(relations, dict):
            raise ValueError('SubscriptionStatusResponse relations must be a dict.')

        topics = relations.get('topics', {})
        if not isinstance(topics, dict):
            raise ValueError('SubscriptionStatusResponse topics must be a dict.')

        self.subscriptions = [str(topic) for topic in topics]

    def __str__(self):
        return 'SubscriptionStatusResponse(subscriptions={}, iid_error={}, error={})'.format(self.subscriptions, self.iid_error, self.error)
