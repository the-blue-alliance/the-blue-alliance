from typing import Any, cast, Dict, List

import pytest
from werkzeug.test import Client

from backend.common.consts.auth_type import AuthType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.sitevars.platinum_sponsors import (
    ContentType,
    PlatinumSponsors,
    Sponsor,
)

AUTH_HEADERS = {"X-TBA-Auth-Key": "test_auth_key"}


@pytest.fixture(autouse=True)
def auth_key(ndb_stub) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()


def _sponsor(name: str, logo_style: str = "wordmark") -> Sponsor:
    return Sponsor(
        name=name,
        url=f"https://{name.lower()}.example.com/",
        logo_style="mark" if logo_style == "mark" else "wordmark",
        logo_url=f"https://{name.lower()}.example.com/light.png",
        logo_url_dark=f"https://{name.lower()}.example.com/dark.png",
    )


def _put(sponsors: List[Sponsor]) -> None:
    PlatinumSponsors.put(ContentType(sponsors=sponsors))


def test_sponsors_requires_auth(api_client: Client) -> None:
    resp = api_client.get("/api/v3/sponsors")
    assert resp.status_code == 401


def test_sponsors_default(api_client: Client) -> None:
    resp = api_client.get("/api/v3/sponsors", headers=AUTH_HEADERS)
    assert resp.get_json() == {
        "sponsors": [
            {
                "name": "AndyMark",
                "url": "https://www.andymark.com/",
                "logo_style": "wordmark",
                "logo_url": "https://www.thebluealliance.com"
                "/images/sponsors/andymark-on-light.png",
                "logo_url_dark": "https://www.thebluealliance.com"
                "/images/sponsors/andymark-on-dark.png",
            }
        ]
    }


def test_sponsors_empty(api_client: Client) -> None:
    _put([])
    resp = api_client.get("/api/v3/sponsors", headers=AUTH_HEADERS)
    assert resp.get_json() == {"sponsors": []}


def test_sponsors_one(api_client: Client) -> None:
    _put([_sponsor("Acme", "mark")])
    resp = api_client.get("/api/v3/sponsors", headers=AUTH_HEADERS)
    assert resp.get_json() == {
        "sponsors": [
            {
                "name": "Acme",
                "url": "https://acme.example.com/",
                "logo_style": "mark",
                "logo_url": "https://acme.example.com/light.png",
                "logo_url_dark": "https://acme.example.com/dark.png",
            }
        ]
    }


def test_sponsors_three_in_order(api_client: Client) -> None:
    _put([_sponsor("C"), _sponsor("A"), _sponsor("B")])
    resp = api_client.get("/api/v3/sponsors", headers=AUTH_HEADERS)
    assert [s["name"] for s in resp.get_json()["sponsors"]] == ["C", "A", "B"]


def test_sponsors_malformed_entry_dropped(api_client: Client) -> None:
    PlatinumSponsors.put(
        ContentType(sponsors=[cast(Any, {"name": "Broken"}), _sponsor("A")])
    )
    resp = api_client.get("/api/v3/sponsors", headers=AUTH_HEADERS)
    assert [s["name"] for s in resp.get_json()["sponsors"]] == ["A"]


def test_sponsors_cache_control(api_client: Client) -> None:
    resp = api_client.get("/api/v3/sponsors", headers=AUTH_HEADERS)
    assert resp.headers["Cache-Control"] == "public, max-age=3600, s-maxage=3600"


def test_sponsors_unknown_logo_style_served_as_wordmark(api_client: Client) -> None:
    sponsor = cast(Dict[str, Any], _sponsor("A"))
    sponsor["logo_style"] = "banner"
    PlatinumSponsors.put(ContentType(sponsors=[cast(Sponsor, sponsor)]))
    resp = api_client.get("/api/v3/sponsors", headers=AUTH_HEADERS)
    assert resp.get_json()["sponsors"][0]["logo_style"] == "wordmark"
