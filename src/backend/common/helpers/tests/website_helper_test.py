import pytest

from backend.common.helpers.website_helper import WebsiteHelper


@pytest.mark.parametrize(
    "website, expected",
    [
        (None, None),
        ("", None),
        ("website.com", "http://website.com"),
        (" https://website.com ", "https://website.com"),
        ("http://website.com", "http://website.com"),
        ("ftp://website.com", None),
        ("https://wébsite.com", None),
    ],
)
def test_format_url(website, expected) -> None:
    assert WebsiteHelper.format_url(website) == expected
