class Payload(object):
    """
    Abstract class to be subclassed by payload parts for notifications.
    """
    @property
    def payload_dict(self):
        raise NotImplementedError("Payload subclass must implement payload_dict")

    @staticmethod
    def _set_payload_value(payload, key, value):
        """ Set the value for a given key, if it's not None """
        if value is not None:
            payload[key] = value
