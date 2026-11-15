from typing import Any, cast

import pytest

from backend.common.sitevars.platinum_sponsors import (
    ContentType,
    PlatinumSponsors,
    Sponsor,
)


def _sponsor(sponsor_name: str, **overrides: Any) -> Sponsor:
    sponsor = {
        "name": sponsor_name,
        "url": f"https://{sponsor_name.lower()}.example.com/",
        "logo_style": "wordmark",
        "logo_url": f"https://{sponsor_name.lower()}.example.com/light.png",
        "logo_url_dark": f"https://{sponsor_name.lower()}.example.com/dark.png",
    }
    sponsor.update(overrides)
    return cast(Sponsor, sponsor)


def test_key() -> None:
    assert PlatinumSponsors.key() == "platinum_sponsors"


def test_description() -> None:
    assert "Platinum sponsors" in PlatinumSponsors.description()


def test_default_sitevar() -> None:
    default_sitevar = PlatinumSponsors._fetch_sitevar()
    assert default_sitevar.contents == {
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


def test_sponsors_default() -> None:
    assert [s["name"] for s in PlatinumSponsors.sponsors()] == ["AndyMark"]


def test_sponsors_empty() -> None:
    PlatinumSponsors.put(ContentType(sponsors=[]))
    assert PlatinumSponsors.sponsors() == []


def test_sponsors_keeps_order() -> None:
    PlatinumSponsors.put(ContentType(sponsors=[_sponsor("B"), _sponsor("A")]))
    assert [s["name"] for s in PlatinumSponsors.sponsors()] == ["B", "A"]


def test_sponsors_capped_at_three() -> None:
    PlatinumSponsors.put(
        ContentType(sponsors=[_sponsor(n) for n in ["A", "B", "C", "D"]])
    )
    assert [s["name"] for s in PlatinumSponsors.sponsors()] == ["A", "B", "C"]


@pytest.mark.parametrize(
    "bad_entry",
    [
        "not a dict",
        {"url": "https://x.example.com/", "logo_style": "wordmark"},
        _sponsor("A", name="  "),
        _sponsor("A", url="http://insecure.example.com/"),
        _sponsor("A", url=None),
    ],
)
def test_sponsors_drops_malformed_entry(bad_entry: Any) -> None:
    PlatinumSponsors.put(cast(ContentType, {"sponsors": [bad_entry, _sponsor("B")]}))
    assert [s["name"] for s in PlatinumSponsors.sponsors()] == ["B"]


@pytest.mark.parametrize("contents", [{}, {"sponsors": "AndyMark"}, [], None])
def test_sponsors_malformed_contents(contents: Any) -> None:
    PlatinumSponsors.put(cast(ContentType, contents))
    assert PlatinumSponsors.sponsors() == []


def test_sponsors_nulls_bad_logo_urls() -> None:
    PlatinumSponsors.put(
        ContentType(
            sponsors=[
                _sponsor("A", logo_url="/images/a.png", logo_url_dark=42),
            ]
        )
    )
    sponsor = PlatinumSponsors.sponsors()[0]
    assert (sponsor["logo_url"], sponsor["logo_url_dark"]) == (None, None)


def test_sponsors_fills_missing_logo_urls() -> None:
    PlatinumSponsors.put(
        cast(
            ContentType,
            {
                "sponsors": [
                    {
                        "name": "A",
                        "url": "https://a.example.com/",
                        "logo_style": "mark",
                    }
                ]
            },
        )
    )
    assert PlatinumSponsors.sponsors() == [
        {
            "name": "A",
            "url": "https://a.example.com/",
            "logo_style": "mark",
            "logo_url": None,
            "logo_url_dark": None,
        }
    ]


@pytest.mark.parametrize("logo_style", ["banner", None, 3])
def test_sponsors_unknown_logo_style_is_wordmark(logo_style: Any) -> None:
    PlatinumSponsors.put(ContentType(sponsors=[_sponsor("A", logo_style=logo_style)]))
    assert PlatinumSponsors.sponsors()[0]["logo_style"] == "wordmark"
