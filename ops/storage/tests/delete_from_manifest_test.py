import csv
import json
import math
import os
import random
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pytest

from storage.delete_from_manifest import (
    ALREADY_GONE,
    DELETED,
    FAILED,
    GcsBatchDeleter,
    main,
    ManifestInfo,
    ManifestRow,
    PRECONDITION_FAILED,
    RetryPolicy,
    RunDir,
    Runner,
    State,
    status_report,
    TokenBucket,
    validate_manifest,
)

BUCKET = "bkt"


class FakeDeleter:
    """Returns scripted statuses per object name; the last status repeats."""

    def __init__(self, script: Optional[Dict[str, List[Optional[int]]]] = None) -> None:
        self.script: Dict[str, List[Optional[int]]] = script or {}
        self.calls: List[List[ManifestRow]] = []
        self.attempts: Dict[str, int] = {}
        self.raise_on_call: Optional[int] = None

    def delete(self, rows: Sequence[ManifestRow]) -> List[Optional[int]]:
        self.calls.append(list(rows))
        if self.raise_on_call == len(self.calls):
            raise ConnectionError("network down")
        statuses: List[Optional[int]] = []
        for row in rows:
            n = self.attempts.get(row.name, 0)
            self.attempts[row.name] = n + 1
            seq = self.script.get(row.name, [204])
            statuses.append(seq[min(n, len(seq) - 1)])
        return statuses

    @property
    def deleted_names(self) -> List[str]:
        return [r.name for call in self.calls for r in call]


def write_manifest(
    path: str, n: int, header: str = "bucket,name,generation", bucket: str = BUCKET
) -> str:
    with open(path, "w") as f:
        f.write(header + "\n")
        for i in range(n):
            f.write(f"{bucket},d/{i:05d}.json,{1000 + i}\n")
    return path


@pytest.fixture
def manifest(tmp_path: Any) -> str:
    return write_manifest(str(tmp_path / "manifest.csv"), 5)


def execute(
    manifest_path: str,
    run_dir: str,
    deleter: FakeDeleter,
    rows: int,
    extra: Optional[List[str]] = None,
) -> int:
    argv = [
        "--manifest",
        manifest_path,
        "--bucket",
        BUCKET,
        "--run-dir",
        run_dir,
        "--execute",
        "--confirm-count",
        str(rows),
        "--workers",
        "2",
        "--max-rate",
        "1000000",
    ] + (extra or [])
    return main(argv, deleter_factory=lambda: deleter, sleep=lambda s: None)


def make_runner(
    tmp_path: Any,
    deleter: FakeDeleter,
    rows: int = 1,
    chunk_size: int = 10,
    max_attempts: int = 3,
) -> Tuple[Runner, RunDir]:
    path = write_manifest(str(tmp_path / "m.csv"), rows)
    info = validate_manifest(path, BUCKET)
    run_dir = RunDir(str(tmp_path / "run"))
    run_dir.open()
    state = State(
        manifest_path=path,
        manifest_sha256=info.sha256,
        rows=info.rows,
        chunk_size=chunk_size,
        bucket=BUCKET,
    )
    runner = Runner(
        manifest=info,
        run_dir=run_dir,
        state=state,
        deleter_factory=lambda: deleter,
        limiter=TokenBucket(1e9, capacity=1e9),
        workers=1,
        policy=RetryPolicy(max_attempts=max_attempts),
        sleep=lambda s: None,
        rng=random.Random(0),
        progress_s=3600,
    )
    return runner, run_dir


def outcome_of(tmp_path: Any, statuses: List[Optional[int]]) -> Tuple[str, int]:
    deleter = FakeDeleter({"d/00000.json": statuses})
    runner, run_dir = make_runner(tmp_path, deleter)
    runner.run()
    run_dir.close()
    (outcome,) = [o for o, n in runner.state.counts.items() if n]
    return outcome, len(deleter.calls)


def read_csv(path: str) -> List[List[str]]:
    with open(path, newline="") as f:
        return list(csv.reader(f))


# Manifest validation


def test_invalid_header_aborts(tmp_path: Any) -> None:
    # A header other than bucket,name,generation aborts before deleting.
    path = write_manifest(str(tmp_path / "m.csv"), 3, header="bucket,object")
    deleter = FakeDeleter()
    assert execute(path, str(tmp_path / "run"), deleter, 3) == 2
    assert deleter.calls == []


def test_wrong_bucket_aborts(tmp_path: Any) -> None:
    # Rows naming a bucket other than --bucket abort before deleting.
    path = write_manifest(str(tmp_path / "m.csv"), 3, bucket="other")
    deleter = FakeDeleter()
    assert execute(path, str(tmp_path / "run"), deleter, 3) == 2
    assert deleter.calls == []


def test_non_numeric_generation_aborts(tmp_path: Any) -> None:
    # A non-numeric generation anywhere in the manifest aborts before deleting.
    path = write_manifest(str(tmp_path / "m.csv"), 3)
    with open(path, "a") as f:
        f.write(f"{BUCKET},d/x.json,12a\n")
    deleter = FakeDeleter()
    assert execute(path, str(tmp_path / "run"), deleter, 4) == 2
    assert deleter.calls == []


def test_wrong_field_count_aborts(tmp_path: Any) -> None:
    # A row without exactly three fields aborts before deleting.
    path = write_manifest(str(tmp_path / "m.csv"), 3)
    with open(path, "a") as f:
        f.write(f"{BUCKET},d/x.json,1,extra\n")
    deleter = FakeDeleter()
    assert execute(path, str(tmp_path / "run"), deleter, 4) == 2
    assert deleter.calls == []


# Guards


def test_without_execute_nothing_deleted(manifest: str, tmp_path: Any) -> None:
    # The default mode only prints and never creates a deleter.
    def factory() -> FakeDeleter:
        raise AssertionError("deleter created in dry run")

    argv = ["--manifest", manifest, "--bucket", BUCKET]
    assert main(argv, deleter_factory=factory) == 0


def test_confirm_count_mismatch_aborts(manifest: str, tmp_path: Any) -> None:
    # --confirm-count must equal the manifest row count.
    deleter = FakeDeleter()
    assert execute(manifest, str(tmp_path / "run"), deleter, 4) == 2
    assert deleter.calls == []


def test_execute_without_confirm_count_aborts(manifest: str, tmp_path: Any) -> None:
    # --execute without --confirm-count deletes nothing.
    deleter = FakeDeleter()
    argv = ["--manifest", manifest, "--bucket", BUCKET]
    argv += ["--run-dir", str(tmp_path / "run"), "--execute"]
    assert main(argv, deleter_factory=lambda: deleter) == 2
    assert deleter.calls == []


def test_execute_without_run_dir_aborts(manifest: str) -> None:
    # --execute requires --run-dir.
    argv = ["--manifest", manifest, "--bucket", BUCKET, "--execute"]
    with pytest.raises(SystemExit):
        main(argv + ["--confirm-count", "5"], deleter_factory=FakeDeleter)


# Outcomes


@pytest.mark.parametrize("status", [200, 204])
def test_success_counts_deleted(tmp_path: Any, status: int) -> None:
    # 200 and 204 are deleted.
    assert outcome_of(tmp_path, [status]) == (DELETED, 1)


def test_404_counts_already_gone(tmp_path: Any) -> None:
    # 404 is already gone and not retried.
    assert outcome_of(tmp_path, [404]) == (ALREADY_GONE, 1)


def test_412_not_retried(tmp_path: Any) -> None:
    # 412 (generation changed) is skipped after one attempt.
    assert outcome_of(tmp_path, [412, 204]) == (PRECONDITION_FAILED, 1)


@pytest.mark.parametrize("status", [429, 503, None])
def test_transient_retried_then_success(tmp_path: Any, status: Optional[int]) -> None:
    # 429, 5xx and network errors are retried until they succeed.
    assert outcome_of(tmp_path, [status, status, 204]) == (DELETED, 3)


def test_other_4xx_failed_without_retry(tmp_path: Any) -> None:
    # Other client errors fail immediately.
    assert outcome_of(tmp_path, [403, 204]) == (FAILED, 1)


def test_batch_exception_retried(tmp_path: Any) -> None:
    # A whole batch request raising is retried.
    deleter = FakeDeleter()
    deleter.raise_on_call = 1
    runner, run_dir = make_runner(tmp_path, deleter)
    runner.run()
    run_dir.close()
    assert (runner.state.counts[DELETED], len(deleter.calls)) == (1, 2)


def test_503_exhausted_written_to_failures(manifest: str, tmp_path: Any) -> None:
    # Exhausted retries land in failures.csv in manifest format.
    run = str(tmp_path / "run")
    deleter = FakeDeleter({"d/00002.json": [503]})
    assert execute(manifest, run, deleter, 5, ["--max-attempts", "3"]) == 1
    assert deleter.attempts["d/00002.json"] == 3
    assert read_csv(os.path.join(run, "failures.csv")) == [
        ["bucket", "name", "generation"],
        [BUCKET, "d/00002.json", "1002"],
    ]


def test_failures_csv_is_valid_manifest(manifest: str, tmp_path: Any) -> None:
    # failures.csv can be fed back in as a manifest.
    run = str(tmp_path / "run")
    execute(manifest, run, FakeDeleter({"d/00002.json": [403]}), 5)
    assert validate_manifest(os.path.join(run, "failures.csv"), BUCKET).rows == 1


# Batching


def test_batches_never_exceed_100(tmp_path: Any) -> None:
    # 250 rows go out as batches of at most 100.
    path = write_manifest(str(tmp_path / "m.csv"), 250)
    deleter = FakeDeleter()
    execute(path, str(tmp_path / "run"), deleter, 250, ["--workers", "1"])
    assert [len(c) for c in deleter.calls] == [100, 100, 50]


def test_gcs_deleter_uses_if_generation_match() -> None:
    # Deletes are conditional on ifGenerationMatch, never generation=.
    calls: List[Tuple[str, Dict[str, Any]]] = []

    class Bucket:
        def delete_blob(self, name: str, if_generation_match: int, retry: None) -> None:
            calls.append((name, {"if_generation_match": if_generation_match}))

    class Batch:
        def __init__(self) -> None:
            self._responses: List[Any] = []

        def __enter__(self) -> "Batch":
            return self

        def __exit__(self, *exc: Any) -> None:
            self._responses = [type("R", (), {"status_code": 204})()] * len(calls)

    class Client:
        def bucket(self, name: str) -> Bucket:
            return Bucket()

        def batch(self, raise_exception: bool) -> Batch:
            assert raise_exception is False
            return Batch()

    statuses = GcsBatchDeleter(Client()).delete([ManifestRow(BUCKET, "d/a.json", 7)])
    assert (calls, statuses) == ([("d/a.json", {"if_generation_match": 7})], [204])


# Rate limiting


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def sleep(self, s: float) -> None:
        self.now += s


def test_token_bucket_burst_is_free() -> None:
    # Up to capacity tokens are available without waiting.
    clock = FakeClock()
    bucket = TokenBucket(10, capacity=100, clock=clock, sleep=clock.sleep)
    assert bucket.acquire(100) == 0


def test_token_bucket_waits_for_refill() -> None:
    # Past capacity, a caller waits n / rate seconds.
    clock = FakeClock()
    bucket = TokenBucket(10, capacity=100, clock=clock, sleep=clock.sleep)
    bucket.acquire(100)
    assert bucket.acquire(50) == 5.0


def test_token_bucket_caps_throughput() -> None:
    # 10,000 tokens at 500/s with a 100 burst take (10,000 - 100) / 500 s.
    clock = FakeClock()
    bucket = TokenBucket(500, capacity=100, clock=clock, sleep=clock.sleep)
    for _ in range(100):
        bucket.acquire(100)
    assert math.isclose(clock.now, 19.8)


# Durability and resume


def test_resume_skips_completed_chunks(tmp_path: Any) -> None:
    # A second session only deletes chunks not checkpointed by the first.
    path = write_manifest(str(tmp_path / "m.csv"), 25)
    run = str(tmp_path / "run")
    first = FakeDeleter({"d/00012.json": [503]})
    execute(path, run, first, 25, ["--chunk-size", "10", "--max-attempts", "1"])
    state = RunDir(run).load_state()
    assert state is not None
    state.completed.discard(1)
    state.counts[FAILED] -= 1
    state.counts[DELETED] -= 9
    state.failure_rows = 0
    RunDir(run).save_state(state)
    second = FakeDeleter()
    assert execute(path, run, second, 25, ["--chunk-size", "10"]) == 0
    assert second.deleted_names == [f"d/{i:05d}.json" for i in range(10, 20)]


def test_mid_chunk_interruption_redoes_that_chunk_only(tmp_path: Any) -> None:
    # A chunk stopped mid-way is not checkpointed and is redone in full.
    path = write_manifest(str(tmp_path / "m.csv"), 30)
    run = str(tmp_path / "run")
    first = FakeDeleter()
    runner_ref: List[Runner] = []

    def factory() -> FakeDeleter:
        return first

    original = first.delete

    def stop_mid_chunk(rows: Sequence[ManifestRow]) -> List[Optional[int]]:
        result = original(rows)
        if rows[0].name == "d/00010.json":
            runner_ref[0].stop.set()
        return result

    first.delete = stop_mid_chunk  # pyre-ignore[8]
    info = validate_manifest(path, BUCKET)
    run_dir = RunDir(run)
    run_dir.open()
    state = State(path, info.sha256, info.rows, 10, BUCKET, sessions=1)
    runner = Runner(
        info,
        run_dir,
        state,
        factory,
        TokenBucket(1e9, 1e9),
        workers=1,
        policy=RetryPolicy(),
        sleep=lambda s: None,
        progress_s=3600,
        batch_size=5,
    )
    runner_ref.append(runner)
    runner.run()
    run_dir.close()
    assert state.completed == {0}
    second = FakeDeleter()
    assert execute(path, run, second, 30, ["--chunk-size", "10"]) == 0
    assert second.deleted_names == [f"d/{i:05d}.json" for i in range(10, 30)]


def test_checkpoint_survives_crash_before_rename(
    tmp_path: Any, monkeypatch: Any
) -> None:
    # A crash after writing the temp file but before rename keeps the old state.
    run_dir = RunDir(str(tmp_path / "run"))
    os.makedirs(run_dir.path)
    state = State("m.csv", "abc", 20, 10, BUCKET, completed={0})
    run_dir.save_state(state)
    state.completed.add(1)

    def crash(src: str, dst: str) -> None:
        raise OSError("killed")

    monkeypatch.setattr(os, "replace", crash)
    with pytest.raises(OSError):
        run_dir.save_state(state)
    monkeypatch.undo()
    loaded = run_dir.load_state()
    assert loaded is not None and loaded.completed == {0}


def test_uncheckpointed_failures_dropped_on_resume(tmp_path: Any) -> None:
    # Failure rows appended after the last checkpoint are removed on restart.
    run_dir = RunDir(str(tmp_path / "run"))
    os.makedirs(run_dir.path)
    run_dir.append_failures([ManifestRow(BUCKET, "a", 1), ManifestRow(BUCKET, "b", 2)])
    assert run_dir.reconcile_failures(1) == 1
    assert read_csv(run_dir.failures_path)[1:] == [[BUCKET, "a", "1"]]


def test_manifest_hash_mismatch_refuses(manifest: str, tmp_path: Any) -> None:
    # Resuming a run dir with a different manifest deletes nothing.
    run = str(tmp_path / "run")
    execute(manifest, run, FakeDeleter(), 5)
    other = write_manifest(str(tmp_path / "other.csv"), 5)
    with open(other, "a") as f:
        f.write(f"{BUCKET},d/extra.json,1\n")
    deleter = FakeDeleter()
    assert execute(other, run, deleter, 6) == 2
    assert deleter.calls == []


def test_status_reports_cumulative_counts(tmp_path: Any, capsys: Any) -> None:
    # --status sums outcomes across sessions without deleting.
    path = write_manifest(str(tmp_path / "m.csv"), 20)
    run = str(tmp_path / "run")
    execute(path, run, FakeDeleter({"d/00001.json": [404]}), 20, ["--chunk-size", "10"])
    state = RunDir(run).load_state()
    assert state is not None
    state.completed.discard(1)
    state.counts[DELETED] -= 10
    RunDir(run).save_state(state)
    execute(path, run, FakeDeleter({"d/00011.json": [412]}), 20, ["--chunk-size", "10"])
    capsys.readouterr()
    assert main(["--status", "--run-dir", run]) == 0
    out = capsys.readouterr().out
    assert "deleted=18, already_gone=1, precondition_failed=1, failed=0" in out
    assert "sessions:   2" in out


def test_events_jsonl_lines_are_json(manifest: str, tmp_path: Any) -> None:
    # Every events.jsonl line parses; a session logs start, chunks and end.
    run = str(tmp_path / "run")
    execute(manifest, run, FakeDeleter(), 5, ["--chunk-size", "2"])
    with open(os.path.join(run, "events.jsonl")) as f:
        kinds = [json.loads(line)["event"] for line in f]
    assert [k for k in kinds if k != "progress"] == [
        "session_start",
        "chunk_done",
        "chunk_done",
        "chunk_done",
        "session_end",
    ]


def test_session_start_records_manifest_hash(manifest: str, tmp_path: Any) -> None:
    # session_start records the manifest sha256 and row count.
    run = str(tmp_path / "run")
    execute(manifest, run, FakeDeleter(), 5)
    with open(os.path.join(run, "events.jsonl")) as f:
        start = json.loads(f.readline())
    info: ManifestInfo = validate_manifest(manifest, BUCKET)
    assert (start["manifest_sha256"], start["rows"]) == (info.sha256, 5)


def test_torn_event_line_ignored(tmp_path: Any) -> None:
    # A half-written last line from a kill is skipped when reading events.
    run_dir = RunDir(str(tmp_path / "run"))
    os.makedirs(run_dir.path)
    with open(run_dir.events_path, "w") as f:
        f.write('{"event": "session_start"}\n{"event": "chu')
    assert [e["event"] for e in run_dir.read_events()] == ["session_start"]


def test_status_without_state(tmp_path: Any) -> None:
    # --status on an empty run dir says nothing has run.
    assert "nothing run yet" in status_report(RunDir(str(tmp_path / "run")))
