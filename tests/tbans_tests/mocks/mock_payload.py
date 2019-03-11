from tbans.models.notifications.payloads.payload import Payload


class MockPayload(Payload):

    def __init__(self, payload_dict=None):
        self._payload_dict = payload_dict

    @property
    def payload_dict(self):
        return self._payload_dict
