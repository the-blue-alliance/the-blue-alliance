from urllib.error import HTTPError


class MockHTTPError(HTTPError):
    def __init__(self, code):
        super(MockHTTPError, self).__init__(
            "https://thebluealliance.com", code, "mock", {}, None
        )
