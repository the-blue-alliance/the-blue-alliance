from unittest.mock import Mock, patch

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


def test_set_down():
    assert ApiStatusFMSApiDown.get() is False
    ApiStatusFMSApiDown.set_down(True)

    assert ApiStatusFMSApiDown.get() is True


def test_set_down_do_not_update():
    ApiStatusFMSApiDown.set_down(True)

    mock = Mock()
    mock.contents = True

    with patch.object(ApiStatusFMSApiDown, "_fetch_sitevar", return_value=mock):
        ApiStatusFMSApiDown.set_down(True)

    assert not mock.put.called
