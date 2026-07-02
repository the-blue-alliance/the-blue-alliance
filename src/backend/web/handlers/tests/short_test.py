from werkzeug.test import Client


def test_short_team_number(web_client: Client) -> None:
    resp = web_client.get("/254")
    assert resp.status_code == 301
    assert resp.headers["Location"] == "/team/254"


def test_short_team_number_leading_zeros_not_matched(web_client: Client) -> None:
    # The regex only matches plain digits; leading zeros are valid but unusual
    resp = web_client.get("/00254")
    assert resp.status_code == 301
    assert resp.headers["Location"] == "/team/254"


def test_short_team_five_digits(web_client: Client) -> None:
    resp = web_client.get("/99999")
    assert resp.status_code == 301
    assert resp.headers["Location"] == "/team/99999"


def test_short_event_key(web_client: Client) -> None:
    resp = web_client.get("/2024miket")
    assert resp.status_code == 301
    assert resp.headers["Location"] == "/event/2024miket"


def test_short_event_key_with_digits_in_suffix(web_client: Client) -> None:
    resp = web_client.get("/2024cmp2")
    assert resp.status_code == 301
    assert resp.headers["Location"] == "/event/2024cmp2"


def test_short_district_key_known_abbreviation(web_client: Client) -> None:
    resp = web_client.get("/2024fim")
    assert resp.status_code == 301
    assert resp.headers["Location"] == "/events/fim/2024"


def test_short_district_key_old_abbreviation(web_client: Client) -> None:
    # "mar" is an old abbreviation for "fma" — still in ALL_KNOWN_DISTRICT_ABBREVIATIONS
    resp = web_client.get("/2019mar")
    assert resp.status_code == 301
    assert resp.headers["Location"] == "/events/mar/2019"


def test_short_district_key_ne(web_client: Client) -> None:
    resp = web_client.get("/2023ne")
    assert resp.status_code == 301
    assert resp.headers["Location"] == "/events/ne/2023"


def test_short_event_key_unknown_abbreviation_goes_to_event(
    web_client: Client,
) -> None:
    # "xyz" is not a known district abbreviation → treat as event key
    resp = web_client.get("/2024xyz")
    assert resp.status_code == 301
    assert resp.headers["Location"] == "/event/2024xyz"
