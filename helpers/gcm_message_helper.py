
from consts.gcm import GCM
from consts.notification_type import NotificationType
from controllers.gcm.gcm import GCMMessage, GCMConnection
from helpers.gcm_helper import GCMHelper
from helpers.model_to_dict import ModelToDict
from models.event import Event

class GCMMessageHelper(object):
   
    @classmethod 
    def send_match_score_update(cls, match):
        users = GCMHelper.get_users_subscribed_to_match(match, NotificationType.MATCH_SCORE)
        
        gcm_keys = GCMHelper.get_client_ids_for_users(GCM.OS_ANDROID, users)

        data = {}
        data['message_type'] = 'score_update'
        data['message_data'] = {}
        data['message_data']['event_name'] = match.event.get().name
        data['message_data']['match'] = ModelToDict.matchConverter(match)

        message = GCMMessage(gcm_keys, data)
        if not self.gcm_connection:
            self.gcm_connection = GCMConnection()
        gcm_connection.notify_device(message)


    @classmethod
    def send_favorite_update(cls, user_id, client_ids):

        user_collapse_key = "{}_favorite_update".format(user_id)        

        data = {}
        data['message_type'] = "update_favorites"
        message = GCMMessage(client_ids, data, collapse_key=user_collapse_key)
        if not self.gcm_connection:
            self.gcm_connection = GCMConnection()
        self.gcm_connection.notify_device(message)

    @classmethod
    def send_subscription_update(cls, user_id, client_ids):

        user_collapse_key = "{}_subscription_update".format(user_id)

        data = {}
        data['message_type'] = "update_subscriptions"
        message = GCMMessage(client_ids, data, collapse_key=user_collapse_key)
        if not self.gcm_connection:
            self.gcm_connection = GCMConnection()
        self.gcm_connection.notify_device(message)
