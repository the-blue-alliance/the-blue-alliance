from tbans.consts.platform_payload_type import PlatformPayloadType
from tbans.consts.platform_payload_priority import PlatformPayloadPriority
from tbans.models.notifications.payloads.payload import Payload


class PlatformPayload(Payload):

    """
    Represents platform-specific push notification configuration options

    https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages

    Args:
        platform_type (int): Type for the platform payload - can be None when using for default payload.
        priority (int): Priority for push notification - may be None.
        collapse_key (string): Collapse key for push notification - may be None.
    """

    # TODO: Add ttl
    def __init__(self, platform_type=None, priority=None, collapse_key=None):
        """
        Args:
            platform_type (int): Type for the platform payload - can be None when using for default payload.
            priority (int): Priority for push notification - may be None.
            collapse_key (string): Collapse key for push notification - may be None.
        """
        # Check that our platform_type looks right
        if platform_type:
            if not isinstance(platform_type, int):
                raise TypeError('PlatformPayload platform_type must be a PlatformPayloadType constant')
            PlatformPayload._validate_platform_type(platform_type)
        self.platform_type = platform_type

        # Check that our priority looks right
        if priority:
            if not isinstance(priority, int):
                raise TypeError('PlatformPayload priority must be a PlatformPayloadPriority constant')
            if priority not in PlatformPayloadPriority.types:
                raise TypeError("Unsupported PlatformPayload priority: {}".format(priority))
        self.priority = priority

        # Check that our collapse key looks right
        if collapse_key and not isinstance(collapse_key, basestring):
            raise TypeError('PlatformPayload collapse_key must be a string')
        self.collapse_key = collapse_key

    def __str__(self):
        return 'PlatformPayload(platform_type={} priority={} collapse_key="{}")'.format(self.platform_type, self.priority, self.collapse_key)

    @staticmethod
    def _validate_platform_type(platform_type):
        """ Validate that the platform_type is supported.

        Raises:
            TypeError: If platform_type is not in _supported_clients.
        """
        if platform_type not in PlatformPayloadType.types:
            raise TypeError("Unsupported PlatformPayload platform_type: {}".format(platform_type))

    # Render a platform-specific payload dictionary for a platform type, given the platform payload's config
    # Ignore's the platform payload's platform_type
    def platform_payload_dict(self, platform_type):
        """ Render a platform-specific payload dictionary for a platform type, given the platform payload's config.

        Ignore's the platform payload's platform_type property. Used for generating platform payloads for a default config.

        Args:
            platform_type (PlatformPayloadType): Type for the platform payload - can be None when using for default payload.

        Returns:
            dict: None if no platform payload values exist for this object.

        Raises:
            TypeError: If platform_type is not in _supported_clients.
        """
        # Validate that platform_type is supported
        PlatformPayload._validate_platform_type(platform_type)

        payload = {}
        if platform_type == PlatformPayloadType.ANDROID:
            self._render_android(payload)
        elif platform_type == PlatformPayloadType.APNS:
            self._render_apns(payload)
        elif platform_type == PlatformPayloadType.WEBPUSH:
            self._render_webpush(payload)
        return None if not payload else payload  # `not payload` on an empty dict will be True

    @property
    def payload_dict(self):
        """ Render a platform-specific payload dictionary for this object's platform type. """
        return self.platform_payload_dict(self.platform_type)

    def _render_android(self, payload):
        """ Android specific options for messages sent through FCM connection server

        https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages#androidconfig
        """
        Payload._set_payload_value(payload, 'priority', PlatformPayloadPriority.android.get(self.priority, None))
        Payload._set_payload_value(payload, 'collapse_key', self.collapse_key)

    def _render_apns(self, payload):
        """ Apple Push Notification Service specific options

        https://goo.gl/MXRTPa
        https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages#ApnsConfig
        """
        Payload._set_payload_value(payload, 'apns-priority', PlatformPayloadPriority.apns.get(self.priority, None))
        Payload._set_payload_value(payload, 'apns-collapse-id', self.collapse_key)

    def _render_webpush(self, payload):
        """ Webpush protocol options

        https://tools.ietf.org/html/rfc8030
        https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages#WebpushConfig
        """
        Payload._set_payload_value(payload, 'Urgency', PlatformPayloadPriority.web.get(self.priority, None))
        Payload._set_payload_value(payload, 'Topic', self.collapse_key)
