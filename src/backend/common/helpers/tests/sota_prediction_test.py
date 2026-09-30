import datetime

import pytest

from backend.common.helpers.sota_prediction import (
    HKFEventPCGPredictor,
    MatchContext,
    MatchOutcome,
    sort_replay_stream,
    TemporalViolationError,
    to_match_context,
    to_match_outcome,
)
from backend.common.models.event import Event
from backend.common.models.match import Match


def test_hkf_sota_hyperparameters_and_overrides() -> None:
    pred = HKFEventPCGPredictor()
    assert pred.name == "hkf_ev_pcg"
    assert len(pred.p) == 138

    # Verify the 17 SOTA overrides
    assert pred.p["event_pcg"] is True
    assert pred.p["stack_lvl_sat"] is True
    assert pred.p["stack_po"] is True
    assert pred.p["po_score_cal"] is True
    assert pred.p["rank_score_cal"] is True
    assert pred.p["lattice"] is False
    assert pred.p["score_struct"] is True
    assert pred.p["scale_fix_pmf"] is True
    assert pred.p["sshape_gmm"] is True
    assert pred.p["sshape_gmm_cond"] == "xl"
    assert pred.p["sshape_gmm_cond_kg"] == 2000.0
    assert pred.p["sshape_gmm_cond_guard"] == 500
    assert pred.p["pcg_prog_debias"] is False
    assert pred.p["stack_early"] == 0.0
    assert pred.p["pcg_reg"] == 16.0
    assert pred.p["drift_event"] == 0.17
    assert pred.p["pcg_ev_carry"] == 0.40


def test_match_context_firewall_and_properties() -> None:
    ctx = MatchContext(
        match_key="2024casj_qm1",
        event_key="2024casj",
        comp_level="qm",
        set_number=1,
        match_number=1,
        red_teams=["frc254", "frc1678", "frc971"],
        blue_teams=["frc118", "frc148", "frc33"],
        scheduled_time=1710000000,
        actual_time=1710000060,
    )
    assert ctx.match_key == "2024casj_qm1"
    assert ctx.event_key == "2024casj"
    assert ctx.red_teams == ("frc254", "frc1678", "frc971")
    assert ctx.blue_teams == ("frc118", "frc148", "frc33")

    # Anti-lookahead guards: accessing outcome fields must raise TemporalViolationError
    with pytest.raises(TemporalViolationError):
        _ = ctx.red_score

    with pytest.raises(TemporalViolationError):
        _ = ctx["winning_alliance"]

    with pytest.raises(TemporalViolationError):
        _ = "score_breakdown" in ctx


def test_to_match_context_and_outcome_from_models() -> None:
    event = Event(
        id="2024casj",
        year=2024,
        event_type_enum=0,
        name="Silicon Valley Regional",
    )
    now = datetime.datetime(2024, 3, 15, 14, 0, 0)
    match = Match(
        id="2024casj_qm1",
        year=2024,
        event=event.key,
        comp_level="qm",
        set_number=1,
        match_number=1,
        time=now,
        actual_time=now,
        alliances_json='{"red": {"score": 85, "teams": ["frc254", "frc1678", "frc971"], "surrogates": [], "dqs": []}, "blue": {"score": 72, "teams": ["frc118", "frc148", "frc33"], "surrogates": [], "dqs": []}}',
        score_breakdown_json='{"red": {"melodyBonusAchieved": true, "ensembleBonusAchieved": false, "rp": 3}, "blue": {"melodyBonusAchieved": false, "ensembleBonusAchieved": false, "rp": 0}}',
    )

    ctx = to_match_context(match, event)
    assert ctx.match_key == "2024casj_qm1"
    assert ctx.event_key == "2024casj"
    assert ctx.scheduled_time == int(now.timestamp())
    assert ctx.red_teams == ("frc254", "frc1678", "frc971")

    outcome = to_match_outcome(match, event)
    assert outcome is not None
    assert outcome.match_key == "2024casj_qm1"
    assert outcome.red_score == 85
    assert outcome.blue_score == 72
    assert outcome.winning_alliance == "red"
    assert outcome.actual_red_win == 1.0
    assert outcome.red_bonus_rps == {"rp_1": 1, "rp_2": 0}
    assert outcome.blue_bonus_rps == {"rp_1": 0, "rp_2": 0}


def test_predictor_lifecycle_and_idempotency() -> None:
    pred = HKFEventPCGPredictor()
    pred.start_season(2024)

    ctx = MatchContext(
        match_key="2024casj_qm1",
        event_key="2024casj",
        comp_level="qm",
        set_number=1,
        match_number=1,
        red_teams=["frc254", "frc1678", "frc971"],
        blue_teams=["frc118", "frc148", "frc33"],
    )

    # Phase 1: Predict match before outcome
    prediction = pred.predict_match(ctx)
    assert 0.0 <= prediction.red_win_prob <= 1.0
    assert prediction.red.mean > 0
    assert prediction.blue.mean > 0
    assert prediction.red.pmf is not None
    assert prediction.blue.pmf is not None

    # Phase 2: Update with outcome
    outcome = MatchOutcome(
        match_key="2024casj_qm1",
        event_key="2024casj",
        red_score=85,
        blue_score=72,
        red_teams=("frc254", "frc1678", "frc971"),
        blue_teams=("frc118", "frc148", "frc33"),
        red_bonus_rps={"rp_1": 1, "rp_2": 0},
        blue_bonus_rps={"rp_1": 0, "rp_2": 0},
        season=2024,
    )
    pred.update(outcome)
    assert "2024casj_qm1" in pred.processed_match_keys

    # Check team rating state exists
    assert "frc254" in pred.teams

    # Idempotency check: duplicate update must be a no-op
    snapshot_dump = pred.dump_state()
    pred.update(outcome)
    assert pred.dump_state() == snapshot_dump


def test_predictor_state_pruning_and_serialization() -> None:
    pred = HKFEventPCGPredictor()
    pred.start_season(2024)

    # Play two matches across two events
    for ek in ("2024event1", "2024event2"):
        outcome = MatchOutcome(
            match_key=f"{ek}_qm1",
            event_key=ek,
            red_score=60,
            blue_score=50,
            red_teams=(f"{ek}_t1", f"{ek}_t2", f"{ek}_t3"),
            blue_teams=(f"{ek}_t4", f"{ek}_t5", f"{ek}_t6"),
            season=2024,
        )
        pred.update(outcome)

    assert "2024event1" in pred.events
    assert "2024event2" in pred.events

    # Prune completed event 1, keeping only event 2
    pred.prune_dead_state(active_event_keys=["2024event2"])
    assert "2024event1" not in pred.events
    assert "2024event2" in pred.events
    # Team ratings for event 1 are still preserved
    assert "2024event1_t1" in pred.teams

    # Test dump and restore
    blob = pred.dump_state()
    restored = HKFEventPCGPredictor()
    restored.load_state(blob)

    assert "2024event2" in restored.events
    assert "2024event1_t1" in restored.teams
    assert "2024event1_qm1" in restored.processed_match_keys


def test_sort_replay_stream_canonical_ordering() -> None:
    # Event 1: Qual 1, Qual 2
    m1_1 = {
        "key": "2024e1_qm1",
        "event_key": "2024e1",
        "comp_level": "qm",
        "match_number": 1,
        "set_number": 1,
        "actual_time": 1000,
    }
    m1_2 = {
        "key": "2024e1_qm2",
        "event_key": "2024e1",
        "comp_level": "qm",
        "match_number": 2,
        "set_number": 1,
        "actual_time": 1020,
    }

    # Event 2: Qual 1, Qual 2
    m2_1 = {
        "key": "2024e2_qm1",
        "event_key": "2024e2",
        "comp_level": "qm",
        "match_number": 1,
        "set_number": 1,
        "actual_time": 1010,
    }
    m2_2 = {
        "key": "2024e2_qm2",
        "event_key": "2024e2",
        "comp_level": "qm",
        "match_number": 2,
        "set_number": 1,
        "actual_time": 1030,
    }

    events = {
        "2024e1": {"year": 2024, "event_type": 0},
        "2024e2": {"year": 2024, "event_type": 0},
    }

    # Unsorted input
    unsorted_matches = [m2_2, m1_2, m2_1, m1_1]
    sorted_stream = sort_replay_stream(unsorted_matches, events)
    sorted_keys = [m["key"] for m in sorted_stream]

    # Interleaved order by running max timestamp:
    # m1_1 (ts 1000) -> m2_1 (ts 1010) -> m1_2 (ts 1020) -> m2_2 (ts 1030)
    assert sorted_keys == ["2024e1_qm1", "2024e2_qm1", "2024e1_qm2", "2024e2_qm2"]
