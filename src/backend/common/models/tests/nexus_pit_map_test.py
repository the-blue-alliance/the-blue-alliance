from backend.common.models.nexus_pit_map import NexusPitMap


def test_key_name() -> None:
    model = NexusPitMap(id="2026casj", data_json={"size": {"x": 10, "y": 20}})
    assert model.key_name == "2026casj"


def test_data_json_persisted(ndb_stub) -> None:
    data = {
        "size": {"x": 10, "y": 20},
        "pits": {"A": {"team": "254"}},
    }
    NexusPitMap(id="2026casj", data_json=data).put()

    stored = NexusPitMap.get_by_id("2026casj")
    assert stored is not None
    assert stored.data_json == data
