import json

from werkzeug.test import Client

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.models.match import Match


def seed_event(event_key: str = "2024mil") -> Event:
    event = Event(
        id=event_key,
        event_short=event_key[4:],
        name="Milstein Division",
        short_name="Milstein",
        year=int(event_key[:4]),
        event_type_enum=EventType.CMP_DIVISION,
    )
    event.put()
    for comp_level, number in [(CompLevel.QM, 1), (CompLevel.F, 1)]:
        Match(
            id=Match.render_key_name(event_key, comp_level, 1, number),
            event=event.key,
            year=event.year,
            comp_level=comp_level,
            set_number=1,
            match_number=number,
            team_key_names=["frc1", "frc2", "frc3", "frc4", "frc5", "frc6"],
            alliances_json=json.dumps(
                {
                    "red": {"teams": ["frc1", "frc2", "frc3"], "score": 100},
                    "blue": {"teams": ["frc4", "frc5", "frc6"], "score": 90},
                }
            ),
        ).put()
    return event


def test_scores_every_match_regardless_of_schedule(local_client: Client) -> None:
    seed_event()

    resp = local_client.get("/local/match_suggestions/2024mil")

    assert resp.status_code == 200
    # Both matches are played and have no scheduled time, so the cron feed would
    # skip them entirely
    assert {s["match_key"] for s in resp.json["suggestions"]} == {
        "2024mil_qm1",
        "2024mil_f1m1",
    }


def test_time_decay_is_zeroed(local_client: Client) -> None:
    seed_event()

    resp = local_client.get("/local/match_suggestions/2024mil")

    for suggestion in resp.json["suggestions"]:
        assert suggestion["components"]["time_decay"] == 0.0


def test_finals_outrank_quals(local_client: Client) -> None:
    seed_event()

    resp = local_client.get("/local/match_suggestions/2024mil")

    suggestions = {s["match_key"]: s for s in resp.json["suggestions"]}
    assert suggestions["2024mil_f1m1"]["components"]["significance"] == 1.0
    assert suggestions["2024mil_qm1"]["components"]["significance"] == 0.0
    assert suggestions["2024mil_f1m1"]["rank"] < suggestions["2024mil_qm1"]["rank"]


def test_accepts_multiple_events(local_client: Client) -> None:
    seed_event("2024mil")
    seed_event("2024arc")

    resp = local_client.get("/local/match_suggestions/2024mil,2024arc")

    assert resp.status_code == 200
    assert len(resp.json["suggestions"]) == 4


def test_unknown_event_is_404(local_client: Client) -> None:
    resp = local_client.get("/local/match_suggestions/2024nope")

    assert resp.status_code == 404
    assert "not found" in resp.json["Error"]


def test_not_installed_outside_dev() -> None:
    import importlib

    from backend.web import main

    importlib.reload(main)
    resp = main.app.test_client().get("/local/match_suggestions/2024mil")
    assert resp.status_code == 404


def test_results_are_ordered_by_score(local_client: Client) -> None:
    seed_event()

    resp = local_client.get("/local/match_suggestions/2024mil")

    suggestions = resp.json["suggestions"]
    # Flask sorts JSON object keys alphabetically, which would put qm1 ahead of
    # f1m1 -- the list has to carry the ranking instead
    assert [s["match_key"] for s in suggestions] == ["2024mil_f1m1", "2024mil_qm1"]
    assert [s["rank"] for s in suggestions] == [0, 1]
    scores = [s["score"] for s in suggestions]
    assert scores == sorted(scores, reverse=True)
