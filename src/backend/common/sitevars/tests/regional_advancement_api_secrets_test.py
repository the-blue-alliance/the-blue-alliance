from backend.common.sitevars.regional_advancement_api_secrets import (
    ContentType,
    RegionalAdvancementApiSecret,
)


def test_key() -> None:
    assert RegionalAdvancementApiSecret.key() == "ra_api.secrets"


def test_description() -> None:
    assert (
        RegionalAdvancementApiSecret.description()
        == "For accessing regional advancement info"
    )


def test_default_sitevar() -> None:
    default_sitevar = RegionalAdvancementApiSecret._fetch_sitevar()
    assert default_sitevar is not None
    assert default_sitevar.contents == {"url_format": ""}


def test_url_format_empty() -> None:
    assert RegionalAdvancementApiSecret.url_format() is None


def test_url_format() -> None:
    RegionalAdvancementApiSecret.put(
        ContentType(url_format="https://example.com/{year}")
    )
    assert RegionalAdvancementApiSecret.url_format() == "https://example.com/{year}"
