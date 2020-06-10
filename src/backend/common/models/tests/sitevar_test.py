import json

from backend.common.models.sitevar import Sitevar


def test_init() -> None:
    data = {"key": ["value"]}
    s = Sitevar(values_json=json.dumps(data))
    assert s.contents == data
    assert s.values_json == json.dumps(data)


def test_init_default() -> None:
    s = Sitevar()
    assert s.contents == {}
    assert s.values_json == "{}"


def test_init_none() -> None:
    s = Sitevar(values_json=None)
    assert s.contents is None
    assert s.values_json is None


def test_contents() -> None:
    data = {"key": ["value"]}
    s = Sitevar()
    s.contents = data
    assert s.contents == data
    assert s.values_json == json.dumps(data)
