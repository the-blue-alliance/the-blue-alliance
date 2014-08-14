
from consts.gcm import GCM
from controllers.gcm.gcm import GCMMessage, GCMConnection
from helpers.gcm_helper import GCMHelper
from helpers.model_to_dict import ModelToDict
from models.event import Event

class GCMMessageHelper(object):
   
    @classmethod 
    def send_match_score_update(cls, match):
        users = GCMHelper.get_users_subscribed_to_match(match)
        
        gcm_keys = GCMHelper.get_client_ids_for_users(GCM.OS_ANDROID, users)

        data = {}
        data['message_type'] = 'score_update'
        data['message_data'] = {}
        data['message_data']['event_name'] = match.event.get().name
        data['message_data']['match'] = ModelToDict.matchConverter(match)

        message = GCMMessage(gcm_keys, data)
        connection = GCMConnection()
        connection.notify_device(message)
