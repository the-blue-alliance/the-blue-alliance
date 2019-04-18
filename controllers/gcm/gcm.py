################################################################################
# gae_python_gcm/gcm.py
#
# In Python, for Google App Engine
# Originally ported from https://github.com/Instagram/node2dm
# Extended to support new GCM API.
# Greg Bayer <greg@gbayer.com>
#
# From: https://github.com/gregbayer/gae-python-gcm
#
###############################################################################
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################################

from datetime import datetime, timedelta
import logging
import re
import json
import importlib

from google.appengine.api import taskqueue  # Google App Engine specific

from helpers.push_helper import PushHelper

from models.sitevar import Sitevar


class GCMMessage:
    device_tokens = None
    notification = None
    collapse_key = None
    delay_while_idle = None
    time_to_live = None
    priority = None

    def __init__(self, device_tokens, notification, collapse_key=None, delay_while_idle=None, time_to_live=None, priority=None):
        if isinstance(device_tokens, list):
            self.device_tokens = device_tokens
        else:
            self.device_tokens = [device_tokens]

        self.notification = notification
        self.collapse_key = collapse_key
        self.delay_while_idle = delay_while_idle
        self.time_to_live = time_to_live
        self.priority = priority

    def __unicode__(self):
        return "%s:%s:%s:%s:%s" % (repr(self.device_tokens), repr(self.notification), repr(self.collapse_key), repr(self.delay_while_idle), repr(self.time_to_live))

    def json_string(self):

        if not self.device_tokens or not isinstance(self.device_tokens, list):
            logging.error('FCMMessage generate_json_string error. Invalid device tokens: ' + repr(self))
            raise Exception('FCMMessage generate_json_string error. Invalid device tokens.')

        json_dict = {}
        json_dict['registration_ids'] = self.device_tokens

        # If message is a dict, send each key individually
        # Else, send entire message under data key
        if isinstance(self.notification, dict):
            json_dict['data'] = self.notification
        else:
            json_dict['data'] = {'data': self.notification}

        if self.collapse_key:
            json_dict['collapse_key'] = self.collapse_key
        if self.delay_while_idle:
            json_dict['delay_while_idle'] = self.delay_while_idle
        if self.time_to_live:
            json_dict['time_to_live'] = self.time_to_live
        if self.priority:
            json_dict['priority'] = self.priority

        json_str = json.dumps(json_dict)
        return json_str


# Instantiate to send GCM message. No initialization required.
class GCMConnection:

    ################################     Config     ###############################
    # settings.py
    #
    #     GCM_CONFIG = {'gcm_api_key': '',
    #                   'delete_bad_token_callback_func': lambda x: x,
    #                   'update_token_callback_func': lambda x: x}
    ##############################################################################

    def __init__(self):
        self.LOCALHOST = False
        self.SERVER_KEY = Sitevar.get_by_id('gcm.serverKey')
        if self.SERVER_KEY is None:
            raise Exception("Missing sitevar: gcm.serverKey. Can't send FCM messages.")
        self.GCM_CONFIG = {'gcm_api_key': self.SERVER_KEY.contents['gcm_key']}
        self.GOOGLE_LOGIN_URL = 'https://www.google.com/accounts/ClientLogin'
        # Can't use https on localhost due to Google cert bug
        self.GOOGLE_GCM_SEND_URL = 'https://fcm.googleapis.com/fcm/send'

        self.GCM_QUEUE_NAME = 'gcm-retries'
        self.GCM_QUEUE_CALLBACK_URL = '/gae_python_gcm/send_request'

    # Call this to send a push notification
    def notify_device(self, message, deferred=False):
        self._submit_message(message, deferred=deferred)

    ##### Public Utils #####
    def debug(self, option):
        if option == "help":
            return "Commands: help stats\n"

        elif option == "stats":
            output = ''
#            resp += "uptime: " + elapsed + " seconds\n"

            return output

        else:
            return "Invalid command\nCommands: help stats\n"

    # Hooks - Override to change functionality #####

    def delete_bad_token(self, bad_device_token):
        PushHelper.delete_bad_gcm_token(bad_device_token)

    def update_token(self, old_device_token, new_device_token):
        PushHelper.update_token(old_device_token, new_device_token)

    # Currently unused
    def login_complete(self):
        # Retries are handled by the gae task queue
        # self.retry_pending_messages()
        pass

    # Add message to queue
    def _requeue_message(self, message):
        taskqueue.add(queue_name=self.GCM_QUEUE_NAME, url=self.GCM_QUEUE_CALLBACK_URL, params={'device_token': message.device_tokens, 'collapse_key': message.collapse_key, 'notification': message.notification})

    # If send message now or add it to the queue
    def _submit_message(self, message, deferred=False):
        if deferred:
            self._requeue_message(message)
        else:
            self._send_request(message)

    # Try sending message now
    def _send_request(self, message):
        import urllib2
        if message.device_tokens is None or message.notification is None:
            logging.error('Message must contain device_tokens and notification.')
            return False

        # Check for resend_after
        retry_after = None
        if retry_after is not None and retry_after > datetime.now():
            logging.warning('RETRY_AFTER: ' + repr(retry_after) + ', requeueing message: ' + repr(message))
            self._requeue_message(message)
            return

        # Build request
        headers = {
                   'Authorization': 'key=' + self.GCM_CONFIG['gcm_api_key'],
                   'Content-Type': 'application/json'
                   }

        gcm_post_json_str = ''
        try:
            gcm_post_json_str = message.json_string()
        except:
            logging.exception('Error generating json string for message: ' + repr(message))
            return

        logging.info('Sending gcm_post_body: ' + repr(gcm_post_json_str))

        request = urllib2.Request(self.GOOGLE_GCM_SEND_URL, gcm_post_json_str, headers)

        # Post
        try:
            resp = urllib2.urlopen(request)
            resp_json_str = resp.read()
            resp_json = json.loads(resp_json_str)
            logging.info('_send_request() resp_json: ' + repr(resp_json))

#            multicast_id = resp_json['multicast_id']
#            success = resp_json['success']
            failure = resp_json['failure']
            canonical_ids = resp_json['canonical_ids']
            results = resp_json['results']

            # If the value of failure and canonical_ids is 0, it's not necessary to parse the remainder of the response.
            if failure == 0 and canonical_ids == 0:
                # Success, nothing to do
                return
            else:
                # Process result messages for each token (result index matches original token index from message)
                result_index = 0
                for result in results:

                    if 'message_id' in result and 'registration_id' in result:
                        # Update device token
                        try:
                            old_device_token = message.device_tokens[result_index]
                            new_device_token = result['registration_id']
                            self.update_token(old_device_token, new_device_token)
                        except:
                            logging.exception('Error updating device token')

                    elif 'error' in result:
                        # Handle GCM error
                        error_msg = result.get('error')
                        try:
                            device_token = message.device_tokens[result_index]
                            self._on_error(device_token, error_msg, message)
                        except:
                            logging.exception('Error handling GCM error: ' + repr(error_msg))

                    result_index += 1

        except urllib2.HTTPError, e:

            if e.code == 400:
                logging.error('400, Invalid GCM JSON message: ' + repr(gcm_post_json_str))
                logging.exception(str(e.code) + " " + e.msg + " " + e.read())
            elif e.code == 401:
                logging.error('401, Error authenticating with GCM. Retrying message. Might need to fix auth key!')
                self._requeue_message(message)
            elif e.code == 500:
                logging.error('500, Internal error in the GCM server while trying to send message: ' + repr(gcm_post_json_str))
            elif e.code == 503:
                retry_seconds = int(resp.headers.get('Retry-After')) or 10
                logging.error('503, Throttled. Retry after delay. Requeuing message. Delay in seconds: ' + str(retry_seconds))
                retry_timestamp = datetime.now() + timedelta(seconds=retry_seconds)
                self._requeue_message(message)
            else:
                logging.exception('Unexpected HTTPError: ' + str(e.code) + " " + e.msg + " " + e.read())

    def _on_error(self, device_token, error_msg, message):

        if error_msg == "MissingRegistration":
            logging.error('ERROR: GCM message sent without device token. This should not happen!')

        elif error_msg == "InvalidRegistration":
            self.delete_bad_token(device_token)

        elif error_msg == "MismatchSenderId":
            logging.error('ERROR: Device token is tied to a different sender id: ' + repr(device_token))
            self.delete_bad_token(device_token)

        elif error_msg == "NotRegistered":
            self.delete_bad_token(device_token)

        elif error_msg == "MessageTooBig":
            logging.error("ERROR: GCM message too big (max 4096 bytes).")

        elif error_msg == "InvalidTtl":
            logging.error("ERROR: GCM Time to Live field must be an integer representing a duration in seconds between 0 and 2,419,200 (4 weeks).")

        elif error_msg == "MessageTooBig":
            logging.error("ERROR: GCM message too big (max 4096 bytes).")

        elif error_msg == "Unavailable":
            retry_seconds = 10
            logging.error('ERROR: GCM Unavailable. Retry after delay. Requeuing message. Delay in seconds: ' + str(retry_seconds))
            retry_timestamp = datetime.now() + timedelta(seconds=retry_seconds)
            self._requeue_message(message)

        elif error_msg == "InternalServerError":
            logging.error("ERROR: Internal error in the GCM server while trying to send message: " + repr(message))

        else:
            logging.error("Unknown error: %s for device token: %s" % (repr(error_msg), repr(device_token)))
