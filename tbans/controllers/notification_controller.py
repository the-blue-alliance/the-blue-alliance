import logging
import tba_config
import webapp2

from tba.consts.notification_type import NotificationType

from tbans.consts.vertical_type import VerticalType


class NotificationHandler(webapp2.RequestHandler):

    def post(self):
        notification_type = int(self.request.get('notification_type'))

        user_id = self.request.get('user_id', None)
        if user_id:
            sending_device_key = self.request.get('sending_device_key', None)
            notification = NotificationHandler._user_notification(user_id, notification_type)
            # We know if we're sending to users, we'll only be sending to mobile clients
            from tba.models.mobile_client import MobileClient
            tokens = MobileClient.device_push_tokens(user_id)
            # If we have a `sending_device_key` - remove it from our list of tokens
            # do we don't notify the client that dispatched an update to other clients
            if sending_device_key in tokens:
                tokens.remove(sending_device_key)
            # If we don't have any devices to send to - gracefully return
            if len(tokens) == 0:
                return
        else:
            # TODO: Handle notification types
            pass

        vertical_type = int(self.request.get('vertical_type'))
        if vertical_type == VerticalType.FCM:
            success = NotificationHandler._send_fcm(notification, tokens)
            # If our FCM send failed, requeue to try again
            if not success:
                self.response.set_status(500)
        elif vertical_type == VerticalType.WEBHOOK:
            # TODO: Dispatch to webhooks
            pass

    @staticmethod
    def _send_fcm(notification, tokens):
        # Our return for this function - should be false if we need to retry the FCM send
        success = True

        from tbans.requests.fcm_request import FCMRequest
        fcm_request = FCMRequest(NotificationHandler._firebase_app(), notification, tokens=tokens)
        logging.info('{} (FCM) - {}'.format(NotificationType.type_names[notification._type()], str(fcm_request)))

        batch_response = fcm_request.send()
        logging.info('{} (FCM) Sent - Success: {}, Failure: {}'.format(NotificationType.type_names[notification._type()], batch_response.success_count, batch_response.failure_count))

        # Handle any errors we got back from the FCM API
        failed_responses = [(token, response) for (token, response) in zip(tokens, batch_response.responses) if not response.success]
        for (token, response) in failed_responses:
            log_string = 'FCM Error {} - {} {} {}'.format(token, response.exception.code, response.exception.message, response.exception.detail)
            if response.exception.code in ['mismatched-credential', 'registration-token-not-registered']:
                logging.warning(log_string)
                logging.warning('Removing bad token - {}'.format(token))
                from tba.models.mobile_client import MobileClient
                MobileClient.delete_for_token(token)
            else:
                # Log and have this retry later
                logging.error(log_string)
                success = False
        return success

    @staticmethod
    def _firebase_app():
        import firebase_admin
        try:
            return firebase_admin.get_app('tbans')
        except ValueError:
            return firebase_admin.initialize_app(name='tbans')

    @staticmethod
    def _user_notification(user_id, notification_type):
        if notification_type == NotificationType.UPDATE_FAVORITES:
            from tbans.models.notifications.update_favorites import UpdateFavoritesNotification
            return UpdateFavoritesNotification(user_id=user_id)
        elif notification_type == NotificationType.UPDATE_SUBSCRIPTIONS:
            from tbans.models.notifications.update_subscriptions import UpdateSubscriptionsNotification
            return UpdateSubscriptionsNotification(user_id=user_id)


app = webapp2.WSGIApplication([
    ('/notify', NotificationHandler)
], debug=tba_config.DEBUG)
