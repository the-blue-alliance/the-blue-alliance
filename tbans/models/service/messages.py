from protorpc import messages


class FCM(messages.Message):
    """ FCM delivery option - should only pass one field, token, topic, or condition """
    token = messages.StringField(1)
    topic = messages.StringField(2)
    condition = messages.StringField(3)


class Webhook(messages.Message):
    """ A webhook object - a url/secret pair """
    url = messages.StringField(1, required=True)
    secret = messages.StringField(2, required=True)


class TBANSResponse(messages.Message):
    """ Base TBANSResponse Messages - other Response Messages should have code/message as well """
    code = messages.IntegerField(1, default=200, required=True)
    message = messages.StringField(2)


class PingRequest(messages.Message):
    """ Ping - send to FCM *or* webhook - not both """
    fcm = messages.MessageField(FCM, 1)
    webhook = messages.MessageField(Webhook, 2)


class VerificationRequest(messages.Message):
    """ Verification - only send to a webhook """
    webhook = messages.MessageField(Webhook, 1, required=True)


class VerificationResponse(messages.Message):
    code = messages.IntegerField(1, default=200, required=True)
    message = messages.StringField(2)
    verification_key = messages.StringField(3, required=True)
