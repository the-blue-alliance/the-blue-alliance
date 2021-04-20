from backend.common.sitevars.apistatus_fmsapi_down import ApiStatusFMSApiDown


def test_key():
    assert ApiStatusFMSApiDown.key() == "apistatus.fmsapi_down"


def test_description():
    assert ApiStatusFMSApiDown.description() == "Is FMSAPI down?"


def test_default():
    assert ApiStatusFMSApiDown.get() is False


def test_put():
    assert ApiStatusFMSApiDown.get() is False
    ApiStatusFMSApiDown.put(True)
    assert ApiStatusFMSApiDown.get() is True
