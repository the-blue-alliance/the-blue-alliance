from backend.common.consts.auth_type import AuthType
from backend.common.sitevars.trusted_api import TrustedApiConfig


def test_key() -> None:
    assert TrustedApiConfig.key() == "trustedapi"


def test_description() -> None:
    assert (
        TrustedApiConfig.description()
        == "For configuring which types of event data are allowed to be changed via the trusted API"
    )


def test_default_sitevar() -> None:
    default_sitevar = TrustedApiConfig._fetch_sitevar()
    assert default_sitevar is not None

    assert default_sitevar.contents == {}

    for auth_type in AuthType:
        assert TrustedApiConfig.is_auth_enalbed({auth_type}) is True


def test_sitevar_contents_disabled() -> None:
    TrustedApiConfig.put({str(t): False for t in AuthType})

    for auth_type in AuthType:
        assert TrustedApiConfig.is_auth_enalbed({auth_type}) is False


def test_sitevar_contents_mixed() -> None:
    TrustedApiConfig.put(
        {
            str(AuthType.MATCH_VIDEO): True,
            str(AuthType.EVENT_TEAMS): False,
        }
    )

    assert TrustedApiConfig.get() == {
        "1": True,
        "2": False,
    }

    assert (
        TrustedApiConfig.is_auth_enalbed({AuthType.MATCH_VIDEO, AuthType.EVENT_TEAMS})
        is False
    )
