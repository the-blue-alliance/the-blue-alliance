import bs4
import pytest
from werkzeug.test import Client

from backend.common.sitevars.platinum_sponsors import (
    ContentType,
    PlatinumSponsors,
    Sponsor,
)

ANDYMARK = Sponsor(
    name="AndyMark",
    url="https://www.andymark.com/",
    logo_style="wordmark",
    logo_url="https://www.thebluealliance.com/images/sponsors/andymark-on-light.png",
    logo_url_dark="https://www.thebluealliance.com/images/sponsors/andymark-on-dark.png",
)
QUILLFEATHER = Sponsor(
    name="Quillfeather Robotics",
    url="https://quillfeather.example.com/",
    logo_style="mark",
    logo_url="https://quillfeather.example.com/mark.png",
    logo_url_dark=None,
)
NO_LOGO = Sponsor(
    name="Plain Text Co",
    url="https://plaintext.example.com/",
    logo_style="wordmark",
    logo_url=None,
    logo_url_dark=None,
)


def _credit(web_client: Client) -> bs4.Tag | None:
    resp = web_client.get("/about")
    assert resp.status_code == 200
    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    for p in soup.select("#footer p"):
        if isinstance(p, bs4.Tag) and "platinum sponsor" in p.get_text():
            return p
    return None


@pytest.fixture(autouse=True)
def auto_ndb(ndb_stub) -> None:
    pass


def test_footer_default_credits_andymark(web_client: Client) -> None:
    credit = _credit(web_client)
    assert credit is not None
    assert str(credit) == (
        '<p>Thanks to our platinum sponsor <a href="https://www.andymark.com/"'
        ' title="AndyMark"><img alt="AndyMark"'
        ' src="https://www.thebluealliance.com/images/sponsors/andymark-on-light.png"'
        ' width="100"/></a></p>'
    )


def test_footer_hidden_when_no_sponsors(web_client: Client) -> None:
    PlatinumSponsors.put(ContentType(sponsors=[]))
    assert _credit(web_client) is None


def test_footer_pluralizes_label(web_client: Client) -> None:
    PlatinumSponsors.put(ContentType(sponsors=[ANDYMARK, QUILLFEATHER]))
    credit = _credit(web_client)
    assert credit is not None
    assert credit.get_text().startswith("Thanks to our platinum sponsors ")


def test_footer_mark_logo_shows_name(web_client: Client) -> None:
    PlatinumSponsors.put(ContentType(sponsors=[QUILLFEATHER]))
    credit = _credit(web_client)
    assert credit is not None
    link = credit.find("a", href="https://quillfeather.example.com/")
    assert link is not None and link.get_text(strip=True) == "Quillfeather Robotics"


def test_footer_no_logo_shows_name(web_client: Client) -> None:
    PlatinumSponsors.put(ContentType(sponsors=[NO_LOGO]))
    credit = _credit(web_client)
    assert credit is not None
    assert credit.find("img") is None and "Plain Text Co" in credit.get_text()
