#!/usr/bin/python

import logging

from protorpc import messages

class BaseResponse(messages.Message):
    code = messages.IntegerField(1, default=200)
    message = messages.StringField(2, default='')

class RegistrationRequest(messages.Message):
    operating_system = messages.StringField(1, required=True)
    mobile_id = messages.StringField(2, required=True)

class FavoriteMessage(messages.Message):
    model_key = messages.StringField(1, required=True)

class FavoriteCollection(messages.Message):
    favorites = messages.MessageField(FavoriteMessage, 1, repeated=True)

class SubscriptionMessage(messages.Message):
    model_key = messages.StringField(1, required=True)

class SubscriptionCollection(messages.Message):
    subscriptions = messages.MessageField(SubscriptionMessage, 1, repeated=True)
