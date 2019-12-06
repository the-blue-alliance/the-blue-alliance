import hashlib
import hmac
import json
import logging


class NotificationSender(object):

    WEBHOOK_VERSION = 1

    @classmethod
    def send_gcm(cls, notification):
        from controllers.gcm.gcm import GCMConnection
        gcm_connection = GCMConnection()
        gcm_connection.notify_device(notification)

    @classmethod
    def send_webhook(cls, message, keys):
        import urllib2
        payload = json.dumps(message, ensure_ascii=True)

        invalid_urls = []
        for client in keys:

            url = client[0]
            secret = client[1]

            # This checksum is insecure and has been deprecated in favor of an HMAC
            ch = hashlib.sha1()
            ch.update(secret)
            ch.update(payload)
            checksum = ch.hexdigest()

            mac = hmac.new(str(secret), str(payload), hashlib.sha256).hexdigest()

            request = urllib2.Request(url, payload)
            request.add_header("Content-Type", 'application/json; charset="utf-8"')
            request.add_header("X-TBA-Checksum", checksum)
            request.add_header("X-TBA-HMAC", mac)
            request.add_header("X-TBA-Version", '{}'.format(cls.WEBHOOK_VERSION))

            try:
                resp = urllib2.urlopen(request)
            except urllib2.HTTPError, e:
                if e.code == 400:
                    logging.warning('400, Bad request for URL: {}'.format(url))
                elif e.code == 401:
                    logging.warning('401, Webhook unauthorized for URL: {}'.format(url))
                elif e.code == 404:
                    invalid_urls.append(url)
                elif e.code == 500:
                    logging.warning('500, Internal error on server sending message')
                else:
                    logging.warning('Unexpected HTTPError: ' + str(e.code) + " " + e.msg + " " + e.read())
            except urllib2.URLError, e:
                invalid_urls.append(url)
                logging.warning('URLError: ' + str(e.code) + " " + e.msg + " " + e.read())
            except Exception, ex:
                logging.warning("Other Exception: {}".format(str(ex)))

        if invalid_urls:
            logging.warning("Invalid urls while sending webhook: {}".format(str(invalid_urls)))
            return False
        return True
