import hashlib
import json
import logging
import urllib2

from controllers.gcm.gcm import GCMConnection


class NotificationSender(object):

    @classmethod
    def send_gcm(cls, notification):
        gcm_connection = GCMConnection()
        gcm_connection.notify_device(notification)

    @classmethod
    def send_ios(cls, notification):
        pass

    @classmethod
    def send_webhook(cls, message, keys):
        payload = json.dumps(message, ensure_ascii=True)

        for client in keys:

            url = client[0]
            secret = client[1]

            ch = hashlib.sha1()
            ch.update(secret)
            ch.update(payload)
            checksum = ch.hexdigest()

            request = urllib2.Request(url, payload)
            request.add_header("X-TBA-Checksum", checksum)
            try:
                resp = urllib2.urlopen(request)
            except urllib2.HTTPError, e:
                if e.code == 400:
                    logging.error('400, Invalid message: ' + repr(gcm_post_json_str))
                elif e.code == 401:
                    logging.error('401, Webhook unauthorized')
                elif e.code == 500:
                    logging.error('500, Internal error on server sending message')
                else:
                    logging.exception('Unexpected HTTPError: ' + str(e.code) + " " + e.msg + " " + e.read())
            except Exception, ex:
                logging.error("Other Exception: "+str(ex))
