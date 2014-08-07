#!/usr/bin/python

import logging

from protorpc import messages

class BaseResponse(messages.Message):
    code = messages.IntegerField(1, default=200)
    message = messages.StringField(2, default='')

class RegistrationRequest(messages.Message):
    operating_system = messages.StringField(1, required=True)
    mobile_id = messages.StringField(2, required=True)
