import json

from werkzeug.test import Client

from backend.common.models.typeahead_entry import TypeaheadEntry


def test_typeahead_empty(web_client: Client) -> None:
    resp = web_client.get("/_/typeahead/teams-all")
    assert resp.status_code == 200
    assert resp.json == []


def test_typeahead_empty_cached(web_client: Client) -> None:
    resp = web_client.get("/_/typeahead/teams-all")
    assert resp.status_code == 200
    assert resp.json == []


def test_typeahead_content(web_client: Client) -> None:
    data = ["254 | The Cheesy Poofs"]
    entry = TypeaheadEntry(id=TypeaheadEntry.ALL_TEAMS_KEY, data_json=json.dumps(data))
    entry.put()

    resp = web_client.get("/_/typeahead/teams-all")
    assert resp.status_code == 200
    assert resp.json == data


def test_typeahead_content_cached(web_client: Client) -> None:
    data = ["254 | The Cheesy Poofs"]
    entry = TypeaheadEntry(id=TypeaheadEntry.ALL_TEAMS_KEY, data_json=json.dumps(data))
    entry.put()

    resp = web_client.get("/_/typeahead/teams-all")
    assert resp.status_code == 200
    assert resp.json == data

    resp2 = web_client.get(
        "/_/typeahead/teams-all",
        headers={"If-Modified-Since": resp.headers["Last-Modified"]},
    )
    assert resp2.status_code == 304
