class SubscriptionStatusRequest:
    """
    Represents a request to Firebase's Instance ID API to get the subscription status for a subscriber.

    https://developers.google.com/instance-id/reference/server#get_information_about_app_instances

    Attributes:
        token (string): The Instance ID token for the subscriber.
    """

    def __init__(self, token):
        """
        Args:
            token (string): The Instance ID token for the subscriber - this is the same token as FCM tokens.
        """
        from tbans.utils.validation_utils import validate_is_string

        validate_is_string(token=token)
        self.token = token

    def __str__(self):
        return 'SubscriptionStatusRequest(token={})'.format(self.token)

    @property
    def _iid_info_url(self):
        return "https://iid.googleapis.com/iid/info/{}?details=true".format(self.token)

    def send(self, api_key):
        """ Attempt to send SubscriptionStatusRequest.

        Args:
            api_key (string): FCM API key to use for authorization.

        Return:
            SubscriptionStatusResponse
        """
        from google.appengine.api import urlfetch
        from tbans.models.requests.subscriptions.subscription_status_response import SubscriptionStatusResponse
        from tbans.utils.validation_utils import validate_is_string

        validate_is_string(api_key=api_key)

        headers = {
            'Authorization': 'key=' + api_key
        }
        try:
            response = urlfetch.fetch(
                url=self._iid_info_url,
                method='GET',
                headers=headers
            )
            return SubscriptionStatusResponse(response=response)
        except Exception, e:
            # https://cloud.google.com/appengine/docs/standard/python/refdocs/google.appengine.api.urlfetch_errors
            return SubscriptionStatusResponse(error=str(e))
