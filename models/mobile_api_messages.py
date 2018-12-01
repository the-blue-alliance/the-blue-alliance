#!/usr/bin/python

from protorpc import messages


class BaseResponse(messages.Message):
    code = messages.IntegerField(1, default=200, variant=messages.Variant.INT32)
    message = messages.StringField(2, default='')


class RegistrationRequest(messages.Message):
    operating_system = messages.StringField(1, required=True)
    mobile_id = messages.StringField(2, required=True)
    name = messages.StringField(3, required=False, default='Unnamed Device')
    device_uuid = messages.StringField(4, required=True)


class PingRequest(messages.Message):
    mobile_id = messages.StringField(1, required=True)


class FavoriteMessage(messages.Message):
    model_key = messages.StringField(1, required=True)
    device_key = messages.StringField(2)  # So we know which device NOT to push sync notification to
    model_type = messages.IntegerField(3, required=True, variant=messages.Variant.INT32)


class FavoriteCollection(messages.Message):
    favorites = messages.MessageField(FavoriteMessage, 1, repeated=True)


class SubscriptionMessage(messages.Message):
    model_key = messages.StringField(1, required=True)
    notifications = messages.StringField(2, repeated=True)
    device_key = messages.StringField(3)  # So we know which device NOT to push sync notifications to
    model_type = messages.IntegerField(4, required=True, variant=messages.Variant.INT32)


class SubscriptionCollection(messages.Message):
    subscriptions = messages.MessageField(SubscriptionMessage, 1, repeated=True)


class ModelPreferenceMessage(messages.Message):
    model_key = messages.StringField(1, required=True)
    notifications = messages.StringField(2, repeated=True)
    device_key = messages.StringField(3)  # So we know which device NOT to push sync notifications to
    favorite = messages.BooleanField(4, required=True)
    model_type = messages.IntegerField(5, required=True, variant=messages.Variant.INT32)


class MediaSuggestionMessage(messages.Message):
    reference_key = messages.StringField(1, required=True)
    reference_type = messages.StringField(2, required=True)
    year = messages.IntegerField(3, required=True, variant=messages.Variant.INT32)
    media_url = messages.StringField(4, required=True)
    details_json = messages.StringField(5, default="")
