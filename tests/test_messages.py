import unittest2

from tbans.models.service.messages import FCM, Webhook, TBANSResponse, PingRequest, VerificationRequest, VerificationResponse


class TestFCM(unittest2.TestCase):

    def test_fcm_empty(self):
        fcm_empty = FCM()
        self.assertTrue(fcm_empty.is_initialized())

    def test_fcm_token(self):
        fcm = FCM(token='abcd')
        self.assertTrue(fcm.is_initialized())

    def test_fcm_topic(self):
        fcm = FCM(topic='abcd')
        self.assertTrue(fcm.is_initialized())

    def test_fcm_condition(self):
        fcm = FCM(condition='abcd')
        self.assertTrue(fcm.is_initialized())

    def test_fcm_mutli(self):
        fcm = FCM(token='abc', topic='def', condition='ghi')
        self.assertTrue(fcm.is_initialized())


class TestWebhook(unittest2.TestCase):

    def test_webhook_empty(self):
        webhook = Webhook()
        self.assertFalse(webhook.is_initialized())

    def test_webhook_url(self):
        webhook = Webhook(url='abcd')
        self.assertFalse(webhook.is_initialized())

    def test_webhook_secret(self):
        webhook = Webhook(secret='abcd')
        self.assertFalse(webhook.is_initialized())

    def test_webhook(self):
        webhook = Webhook(url='abc', secret='def')
        self.assertTrue(webhook.is_initialized())


class TestTBANSResponse(unittest2.TestCase):

    def test_tbans_response_default(self):
        response = TBANSResponse()
        self.assertTrue(response.is_initialized())
        self.assertEqual(response.code, 200)
        self.assertEqual(response.message, None)

    def test_tbans_response_code(self):
        response = TBANSResponse(code=500)
        self.assertTrue(response.is_initialized())
        self.assertEqual(response.code, 500)
        self.assertEqual(response.message, None)

    def test_tbans_response_message(self):
        message = 'Some message here'
        response = TBANSResponse(message=message)
        self.assertTrue(response.is_initialized())
        self.assertEqual(response.code, 200)
        self.assertEqual(response.message, message)


class TestPingRequest(unittest2.TestCase):

    def test_ping_request_empty(self):
        request = PingRequest()
        self.assertTrue(request.is_initialized())

    def test_ping_request_fcm(self):
        request = PingRequest(fcm=FCM())
        self.assertTrue(request.is_initialized())

    def test_ping_request_webhook(self):
        request = PingRequest(webhook=Webhook(url='abc', secret='def'))
        self.assertTrue(request.is_initialized())

    def test_ping_request(self):
        request = PingRequest(fcm=FCM(), webhook=Webhook(url='abc', secret='def'))
        self.assertTrue(request.is_initialized())


class TestVerificationRequest(unittest2.TestCase):

    def test_verification_request_empty(self):
        request = VerificationRequest()
        self.assertFalse(request.is_initialized())

    def test_verification_request(self):
        request = VerificationRequest(webhook=Webhook(url='abc', secret='def'))
        self.assertTrue(request.is_initialized())


class TestVerificationResponse(unittest2.TestCase):

    def test_verification_response_empty(self):
        response = VerificationResponse()
        self.assertFalse(response.is_initialized())

    def test_verification_response_default(self):
        response = VerificationResponse(verification_key='abc')
        self.assertTrue(response.is_initialized())
        self.assertEqual(response.code, 200)
        self.assertEqual(response.message, None)
        self.assertEqual(response.verification_key, 'abc')

    def test_verification_response_code(self):
        response = VerificationResponse(code=500, verification_key='abc')
        self.assertTrue(response.is_initialized())
        self.assertEqual(response.code, 500)
        self.assertEqual(response.message, None)
        self.assertEqual(response.verification_key, 'abc')

    def test_verification_response_message(self):
        message = 'Some message here'
        response = VerificationResponse(message=message, verification_key='abc')
        self.assertTrue(response.is_initialized())
        self.assertEqual(response.code, 200)
        self.assertEqual(response.message, message)
        self.assertEqual(response.verification_key, 'abc')
