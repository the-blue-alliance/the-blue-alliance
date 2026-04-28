from backend.common.models.nexus_event_details import NexusEventDetails


def test_key_name() -> None:
    model = NexusEventDetails(id="2026casj", pitmap_json={"size": {"x": 10, "y": 20}})
    assert model.key_name == "2026casj"


def test_pitmap_json_persisted(ndb_stub) -> None:
    data = {
        "size": {"x": 10, "y": 20},
        "pits": {"A": {"team": "254"}},
    }
    NexusEventDetails(id="2026casj", pitmap_json=data).put()

    stored = NexusEventDetails.get_by_id("2026casj")
    assert stored is not None
    assert stored.pitmap_json == data
