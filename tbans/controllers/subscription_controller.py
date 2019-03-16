import logging

from google.appengine.ext import ndb

from models.account import Account
from models.mobile_client import MobileClient


class SubscriptionController(object):

    @classmethod
    def update_token(cls, user_id, token):
        """
        Conditionally register/unregister from all notifications for a user_id/token pair.

        Args:
            user_id (string): User ID the device registration token belongs to.
            token (string): A device registration token.

        Returns:
            bool: If the subscribes/unsubscribes were all successful for the token.
        """
        from tbans.utils.validation_utils import validate_is_string
        validate_is_string(user_id=user_id, token=token)

        # Attempt to fetch the account for the user/token - if it doesn't exist, we should unsubscribe.
        moblie_client_count = MobileClient.query(MobileClient.messaging_id == token, ancestor=ndb.Key(Account, user_id)).count()

        if moblie_client_count == 0:
            logging.info('Unsubscribing {}'.format(token))
            # Unsubscribe token from all subscribed topics.
            return cls._unsubscribe(token)
        else:
            logging.info('Subscribing {} {}'.format(user_id, token))
            # Subscribe the token to all subscriptions.
            return cls._subscribe(user_id, token)

    @staticmethod
    def update_subscriptions(user_id):
        """
        Sync all subscriptions for all devices for a user. This is a two-part process of
        subscribing each device token for a user to local subscriptions and unsubscribing
        them from upstream subscriptions that are not longer valid.

        Args:
            user_id (string): User ID to fetch moblie clients/subscriptions for.

        Returns:
            bool: If all status/subscribe/unsubscribe requests completed successfully.
        """
        from tbans.utils.validation_utils import validate_is_string
        validate_is_string(user_id=user_id)

        tokens = MobileClient.device_push_tokens(user_id)

        from tbans.models.subscriptions.subscription_topic import SubscriptionTopic
        local_topics = SubscriptionTopic.user_subscription_topics(user_id)

        token_successes = []
        for token in tokens:
            # Fetch what topics we're subscribed to upstream - used to figure out if we need to unsubscribe
            status_response = SubscriptionController._make_status_request(token)
            if not status_response:
                # If our status request failed, chances are all other status
                # requests will fail - we'll queue this for later.
                return False

            # Topics that exist locally but not upstream we should dispatch subscribes for
            subscribe_topics = set(local_topics) - set(status_response.subscriptions)
            # Topics that exist upstream but not locally we should dispatch unsubscribes for
            unsubscribe_topics = set(status_response.subscriptions) - set(local_topics)

            from tbans.consts.subscription_action_type import SubscriptionActionType
            actions = ((subscribe_topics, SubscriptionActionType.ADD), (unsubscribe_topics, SubscriptionActionType.REMOVE))
            for (topics, method) in actions:
                token_successes.append(SubscriptionController._make_batch_requests(token, topics, method))

        return all(token_successes)

    @classmethod
    def _subscribe(cls, user_id, token):
        """
        Subscribe a device token to all subscriptions for a user.

        Args:
            user_id (string): User ID to fetch subscriptions for.
            token (string): A device registration token.

        Note:
            This method is NOT a resync - it's a very very very dumb sync that does not resolve
            upstream state (unsubscribes).

        Returns:
            bool: If all subscribe requests completed successfully.
        """
        from tbans.models.subscriptions.subscription_topic import SubscriptionTopic
        # Fetch what we should be subscribed to locally.
        local_topics = SubscriptionTopic.user_subscription_topics(user_id)

        from tbans.consts.subscription_action_type import SubscriptionActionType
        return SubscriptionController._make_batch_requests(token, local_topics, SubscriptionActionType.ADD)

    @classmethod
    def _unsubscribe(cls, token):
        """
        Unsubscribe a device token from all upstream subscriptions.

        Args:
            token (string): A device registration token.

        Returns:
            bool: If the status and all unsubscribe requests completed successfully.
        """
        # Fetch what topics we're subscribed to upstream - will need to unsubscribe from all of them.
        status_response = SubscriptionController._make_status_request(token)
        if not status_response:
            # If our status request failed, chances are all other status requests will fail - we'll queue this for later.
            return False

        from tbans.consts.subscription_action_type import SubscriptionActionType
        return SubscriptionController._make_batch_requests(token, status_response.subscriptions, SubscriptionActionType.REMOVE)

    @staticmethod
    def _make_batch_requests(tokens, topics, method):
        """
        Make a batch request to the Instance ID API and handle it's response. This
        method handles logging and deleting invalid tokens.

        Attributes:
            tokens (list, string): List of device registration tokens.
            topics (list, string): List of topics to make requests for.
            method (int): SubscriptionActionType constant relating to batch request type.

        Returns:
            bool: If all batch requests completed successfully for all tokens.
        """
        success = True
        for topic in topics:
            # If for some reason during our execution ALL of our tokens were invalid and we don't have any more tokens
            # to retry, we should just go ahead and return. In this case we acted correctly and don't need to retry.
            if len(tokens) == 0:
                return True

            from tbans.models.requests.subscriptions.subscription_batch_request import SubscriptionBatchRequest
            request = SubscriptionBatchRequest(tokens, topic, method)
            logging.info(str(request))

            response = request.send(api_key=SubscriptionController._fcm_api_key())
            logging.info(str(response))

            local_success, tokens = SubscriptionController._handle_batch_request(response, tokens)
            if not local_success:
                success = local_success

        return success

    @staticmethod
    def _handle_batch_request(response, tokens):
        """
        Args:
            response (SubscriptionBatchResponse): The SubscriptionBatchResponse to handle.
            tokens (list, string): The device tokens the request was made for.

        Returns:
            (bool, list): If we handled the response/all of the subscribers properly. Additionally, the updated list of
                tokens we should use if the response was True.
        """
        if response.error:
            logging.error(response.error)
            return (False, tokens)
        elif response.subscribers:
            for subscriber in response.subscribers:
                # If there's no error - we're good! Keep moving on.
                if not subscriber.error:
                    continue

                # Handle our errors
                from tbans.consts.subscriber_error import SubscriberError
                if subscriber.error in [SubscriberError.INVALID_ARGUMENT, SubscriberError.NOT_FOUND]:
                    # These two errors both mean the token is invalid - we'll delete this client.
                    logging.warning("Deleting MobileClient for FCM token: {}".format(subscriber.token))
                    MobileClient.delete_for_token(subscriber.token)

                    # We need to make sure we don't make anymore requets for this token.
                    tokens.remove(subscriber.token)
                else:
                    logging.error('Error for token {}: {}'.format(subscriber.token, subscriber.error))
                    # We need to try this request again later - this probably means subsequent requests will fail.
                    return (False, tokens)
        else:
            logging.error('Unexpected response for {}/{}'.format(user_id, token))
            return (False, tokens)

        return (True, tokens)

    @staticmethod
    def _make_status_request(token):
        """
        Fetch the subscription status for a device token. This method handles logging
        and deleting an invalid token.

        Attributes:
            token (string): The device registration token to fetch the subscriptions for.

        Returns:
            SubscriptionStatus: The SubscriptionStatus for the SubscriptionStatusRequest - will be None if request failed.
        """
        from tbans.models.requests.subscriptions.subscription_status_request import SubscriptionStatusRequest
        status_request = SubscriptionStatusRequest(token)
        logging.info(status_request)

        status_response = status_request.send(api_key=SubscriptionController._fcm_api_key())
        logging.info(status_response)

        status_response_error = SubscriptionController._handle_status_response(status_response, token)
        if status_response_error:
            return status_response
        else:
            return None

    @staticmethod
    def _handle_status_response(status_response, token):
        """
        Args:
            status_response (SubscriptionStatusResponse): The SubscriptionStatusResponse to handle.
            token (string): The device token the request was made for.

        Returns:
            boolean: Returns True if status response was handled appropriately. False otherwise.
        """
        if status_response.error:
            from tbans.consts.iid_error import IIDError
            if status_response.iid_error == IIDError.INVALID_ARGUMENT:
                # Bad token - we should remove.
                logging.warning("Deleting MobileClient for FCM token: {}".format(token))
                MobileClient.delete_for_token(token)
            else:
                # We should consider this request to have failed and not return a response
                logging.error(status_response.error)
                return False

        return True

    @staticmethod
    def _fcm_api_key():
        from models.sitevar import Sitevar
        gcm_server_key_sitevar = Sitevar.get_by_id('gcm.serverKey')
        # TODO: Convert this to be a TBANS-specific Sitevar
        if gcm_server_key_sitevar is None:
            raise Exception("Missing sitevar: gcm.serverKey. Can't send FCM messages.")

        gcm_key = gcm_server_key_sitevar.contents['gcm_key']
        if not gcm_key:
            raise Exception("Missing gcm_key in gcm.serverKey. Can't send FCM messages.")

        return gcm_key
