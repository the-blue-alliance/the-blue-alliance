#!/usr/bin/python

from protorpc import messages

class BaseResponse(messages.Message):
    code = messages.IntegerField(1, default=200)
    message = messages.StringField(2, default='')

class RegistrationRequest(messages.Message):
    operating_system = messages.StringField(1, required=True)
    mobile_id = messages.StringField(2, required=True)

class FavoriteMessage(messages.Message):
    model_key = messages.StringField(1, required=True)
    device_key = messages.StringField(2) # So we know which device NOT to push sync notification to

class FavoriteCollection(messages.Message):
    favorites = messages.MessageField(FavoriteMessage, 1, repeated=True)

class SubscriptionMessage(messages.Message):
    model_key = messages.StringField(1, required=True)
    settings = messages.StringField(2, required=True) # json array of which individual notifications user is subscribed to
    device_key = messages.StringField(3) # So we know which device NOT to push sync notifications to

class SubscriptionCollection(messages.Message):
    subscriptions = messages.MessageField(SubscriptionMessage, 1, repeated=True)
