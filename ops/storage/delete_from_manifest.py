"""Deletes the objects listed in a reviewed dedupe manifest (RFC #11012).

Input is the `manifest.csv` written by dedupe_frc_api_archive.py: header
"bucket,name,generation", one row per object to delete. Every row is
validated before anything is deleted (exact header, three fields, numeric
generation, bucket equal to --bucket); any invalid row aborts the run.

Each object is deleted through the JSON API with ifGenerationMatch=<generation>,
so only the exact version that was reviewed can be deleted: if the object was
overwritten since the dry run, the delete fails with 412 and is skipped. The
live object is soft-deleted (no `generation=` and no hard delete is ever
issued). The bucket has soft delete with 7-day retention, so every deleted
object can be restored for 7 days with

    gcloud storage restore gs://<bucket>/<name>#<generation>

Without --execute the script only validates the manifest and prints what it
would do. With --execute it also requires --confirm-count equal to the
manifest's row count and a --run-dir that holds all durable state:

  state.json    checkpoint: manifest sha256, completed chunks, cumulative
                counts per outcome, sessions. Written to a temp file, fsync'd
                and atomically renamed, so a kill at any point leaves either
                the old or the new checkpoint.
  events.jsonl  append-only, fsync'd JSON lines: session_start, chunk_done,
                progress, session_end.
  run.log       human-readable log.
  failures.csv  rows that could not be deleted, in manifest format, so the
                file can be fed back in as a manifest.

The manifest is processed in chunks of --chunk-size rows. A chunk is marked
done only after every row in it has a final outcome; after a crash or kill a
partly processed chunk is redone (404 = already gone, 412 = skipped, so redoing
is safe). Re-running with the same --run-dir resumes; a different manifest is
refused. SIGINT/SIGTERM finish in-flight batches, checkpoint and exit. --status
prints cumulative progress from the run dir without touching the bucket.

Deletes are sent in batch requests of up to 100 by --workers threads (each with
its own client), capped across workers at --max-rate deletes/sec by a token
bucket. The default (500/s) stays under Cloud Storage's ~1000 writes/s initial
per-bucket guidance, so no ramp-up is needed. 429, 408, 5xx and network errors
are retried with exponential backoff and jitter; 412 is never retried.

Usage:
  caffeinate -i uv run python ops/storage/delete_from_manifest.py \\
      --manifest manifest.csv --bucket tbatv-prod-hrd.appspot.com \\
      --run-dir ~/tba-ops/frc-api-dedupe-2026-10/runs/2025 \\
      --execute --confirm-count <rows> [--gcloud-token]
"""

import argparse
import csv
import datetime
import fcntl
import hashlib
import json
import logging
import math
import os
import random
import re
import signal
import socket
import sys
import threading
import time
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from types import FrameType
from typing import (
    Any,
    Callable,
    Dict,
    IO,
    Iterator,
    List,
    Optional,
    Protocol,
    Sequence,
    Set,
    Tuple,
)

import google.auth.transport.requests

if __name__ == "__main__" and not __package__:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.cloud import storage as gcs  # noqa: E402
from storage.dedupe_frc_api_archive import (  # noqa: E402
    DEFAULT_PROJECT,
    GcloudUserCredentials,
)

MANIFEST_HEADER = ["bucket", "name", "generation"]
BATCH_SIZE = 100
DEFAULT_CHUNK_SIZE = 10_000
DELETED = "deleted"
ALREADY_GONE = "already_gone"
PRECONDITION_FAILED = "precondition_failed"
FAILED = "failed"
OUTCOMES = (DELETED, ALREADY_GONE, PRECONDITION_FAILED, FAILED)
GENERATION_RE = re.compile(r"[0-9]+")
STATE_VERSION = 1

logger: logging.Logger = logging.getLogger("delete_from_manifest")


@dataclass(frozen=True)
class ManifestRow:
    bucket: str
    name: str
    generation: int


@dataclass(frozen=True)
class ManifestInfo:
    path: str
    sha256: str
    rows: int
    first_rows: List[ManifestRow]


class ManifestError(Exception):
    pass


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def validate_manifest(path: str, bucket: str, max_errors: int = 10) -> ManifestInfo:
    """Reads the whole manifest; raises ManifestError listing invalid rows."""
    errors: List[str] = []
    first_rows: List[ManifestRow] = []
    rows = 0
    with open(path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header != MANIFEST_HEADER:
            raise ManifestError(
                [f"header is {header!r}, expected {','.join(MANIFEST_HEADER)!r}"]
            )
        for line_no, fields in enumerate(reader, start=2):
            rows += 1
            error = _row_error(fields, bucket)
            if error is not None:
                errors.append(f"line {line_no}: {error}")
                if len(errors) >= max_errors:
                    break
            elif len(first_rows) < 5:
                first_rows.append(_to_row(fields))
    if errors:
        raise ManifestError(errors)
    return ManifestInfo(
        path=path, sha256=file_sha256(path), rows=rows, first_rows=first_rows
    )


def _row_error(fields: List[str], bucket: str) -> Optional[str]:
    if len(fields) != 3:
        return f"expected 3 fields, got {len(fields)}"
    row_bucket, name, generation = fields
    if row_bucket != bucket:
        return f"bucket {row_bucket!r} != --bucket {bucket!r}"
    if not name:
        return "empty object name"
    if not GENERATION_RE.fullmatch(generation):
        return f"generation {generation!r} is not numeric"
    return None


def _to_row(fields: List[str]) -> ManifestRow:
    return ManifestRow(bucket=fields[0], name=fields[1], generation=int(fields[2]))


def iter_chunks(path: str, chunk_size: int) -> Iterator[Tuple[int, List[ManifestRow]]]:
    with open(path, newline="") as f:
        reader = csv.reader(f)
        next(reader)
        chunk: List[ManifestRow] = []
        index = 0
        for fields in reader:
            chunk.append(_to_row(fields))
            if len(chunk) == chunk_size:
                yield index, chunk
                index += 1
                chunk = []
        if chunk:
            yield index, chunk


class TokenBucket:
    """Thread-safe rate limiter shared by all workers.

    acquire(n) takes n tokens, refilled at `rate` per second up to `capacity`.
    The balance may go negative: the caller then sleeps until its tokens would
    have accrued, so waiting callers queue in order and the long-run rate never
    exceeds `rate`.
    """

    def __init__(
        self,
        rate: float,
        capacity: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.rate = rate
        self.capacity = capacity
        self.clock = clock
        self.sleep = sleep
        self.tokens = capacity
        self.last: float = clock()
        self.lock = threading.Lock()

    def acquire(self, n: int) -> float:
        with self.lock:
            now = self.clock()
            self.tokens = min(
                self.capacity, self.tokens + (now - self.last) * self.rate
            )
            self.last = now
            self.tokens -= n
            wait_s = -self.tokens / self.rate if self.tokens < 0 else 0.0
        if wait_s > 0:
            self.sleep(wait_s)
        return wait_s


def classify(status: Optional[int]) -> Optional[str]:
    """Final outcome for a per-object status, or None to retry."""
    if status in (200, 204):
        return DELETED
    if status == 404:
        return ALREADY_GONE
    if status == 412:
        return PRECONDITION_FAILED
    if status is None or status in (401, 408, 429) or status >= 500:
        return None
    return FAILED


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 6
    base_s: float = 1.0
    cap_s: float = 60.0

    def delay(self, attempt: int, rng: random.Random) -> float:
        """Full-jitter exponential backoff after the given 0-based attempt."""
        return rng.uniform(0, min(self.cap_s, self.base_s * 2**attempt))


class Deleter(Protocol):
    def delete(self, rows: Sequence[ManifestRow]) -> List[Optional[int]]:
        """One batch request; returns one HTTP status per row."""
        ...


class GcsBatchDeleter:
    """Deletes up to 100 objects per JSON API batch request.

    Each delete is conditional on ifGenerationMatch, so it only removes the
    live object if it is still the reviewed generation.
    """

    def __init__(self, client: Any) -> None:
        self.client = client

    def delete(self, rows: Sequence[ManifestRow]) -> List[Optional[int]]:
        if len(rows) > BATCH_SIZE:
            raise ValueError(f"batch of {len(rows)} exceeds {BATCH_SIZE}")
        bucket = self.client.bucket(rows[0].bucket)
        batch = self.client.batch(raise_exception=False)
        with batch:
            for row in rows:
                bucket.delete_blob(
                    row.name, if_generation_match=row.generation, retry=None
                )
        statuses = [r.status_code for r in batch._responses]
        if 401 in statuses:
            # The access token expired mid-run; mint a new one before the retry.
            self.refresh_credentials()
        return statuses

    def refresh_credentials(self) -> None:
        credentials = getattr(self.client, "_credentials", None)
        if credentials is not None:
            credentials.refresh(google.auth.transport.requests.Request())


@dataclass
class State:
    manifest_path: str
    manifest_sha256: str
    rows: int
    chunk_size: int
    bucket: str
    completed: Set[int] = field(default_factory=set)
    counts: Dict[str, int] = field(default_factory=lambda: {o: 0 for o in OUTCOMES})
    failure_rows: int = 0
    sessions: int = 0

    @property
    def chunks(self) -> int:
        return math.ceil(self.rows / self.chunk_size)

    @property
    def done_rows(self) -> int:
        return sum(self.counts.values())

    def to_json(self) -> Dict[str, Any]:
        return {
            "version": STATE_VERSION,
            "manifest_path": self.manifest_path,
            "manifest_sha256": self.manifest_sha256,
            "rows": self.rows,
            "chunk_size": self.chunk_size,
            "bucket": self.bucket,
            "completed": sorted(self.completed),
            "counts": self.counts,
            "failure_rows": self.failure_rows,
            "sessions": self.sessions,
        }

    @classmethod
    def from_json(cls, d: Dict[str, Any]) -> "State":
        if d.get("version") != STATE_VERSION:
            raise ValueError(f"unsupported state version {d.get('version')!r}")
        counts = {o: 0 for o in OUTCOMES}
        counts.update(d["counts"])
        return cls(
            manifest_path=d["manifest_path"],
            manifest_sha256=d["manifest_sha256"],
            rows=d["rows"],
            chunk_size=d["chunk_size"],
            bucket=d["bucket"],
            completed=set(d["completed"]),
            counts=counts,
            failure_rows=d["failure_rows"],
            sessions=d["sessions"],
        )

    def summary(self) -> str:
        pct = 100 * self.done_rows / self.rows if self.rows else 100.0
        return "\n".join(
            [
                f"manifest:   {self.manifest_path} (sha256 {self.manifest_sha256[:12]})",
                f"chunks:     {len(self.completed):,}/{self.chunks:,} done",
                f"rows:       {self.done_rows:,}/{self.rows:,} ({pct:.1f}%)",
                "outcomes:   " + ", ".join(f"{o}={self.counts[o]:,}" for o in OUTCOMES),
                f"failures:   {self.failure_rows:,} rows in failures.csv",
                f"sessions:   {self.sessions}",
            ]
        )


def _fsync_dir(path: str) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class RunDir:
    """Durable state for one manifest, safe against abrupt kills."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.state_path: str = os.path.join(path, "state.json")
        self.events_path: str = os.path.join(path, "events.jsonl")
        self.log_path: str = os.path.join(path, "run.log")
        self.failures_path: str = os.path.join(path, "failures.csv")
        self.lock = threading.Lock()
        self._lock_file: Optional[IO[str]] = None
        self._events: Optional[IO[str]] = None

    def open(self) -> None:
        os.makedirs(self.path, exist_ok=True)
        lock_file = open(os.path.join(self.path, ".lock"), "w")
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lock_file.close()
            raise RuntimeError(f"{self.path} is in use by another session")
        self._lock_file = lock_file
        self._events = open(self.events_path, "a")

    def close(self) -> None:
        if self._events is not None:
            self._events.close()
            self._events = None
        if self._lock_file is not None:
            self._lock_file.close()
            self._lock_file = None

    def load_state(self) -> Optional[State]:
        if not os.path.exists(self.state_path):
            return None
        with open(self.state_path) as f:
            return State.from_json(json.load(f))

    def save_state(self, state: State) -> None:
        tmp = self.state_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(state.to_json(), f, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.state_path)
        _fsync_dir(self.path)

    def event(self, kind: str, **fields: Any) -> None:
        record = {"event": kind, "ts": datetime.datetime.now().astimezone().isoformat()}
        record.update(fields)
        line = json.dumps(record, sort_keys=True) + "\n"
        with self.lock:
            events = self._events
            if events is None:
                raise RuntimeError("run dir is not open")
            events.write(line)
            events.flush()
            os.fsync(events.fileno())

    def read_events(self) -> List[Dict[str, Any]]:
        """Parsed events; a torn last line from a kill mid-write is skipped."""
        if not os.path.exists(self.events_path):
            return []
        events = []
        with open(self.events_path) as f:
            for line in f:
                try:
                    events.append(json.loads(line))
                except ValueError:
                    continue
        return events

    def append_failures(self, rows: Sequence[ManifestRow]) -> None:
        new = not os.path.exists(self.failures_path)
        with open(self.failures_path, "a", newline="") as f:
            writer = csv.writer(f)
            if new:
                writer.writerow(MANIFEST_HEADER)
            for row in rows:
                writer.writerow([row.bucket, row.name, row.generation])
            f.flush()
            os.fsync(f.fileno())

    def reconcile_failures(self, expected_rows: int) -> int:
        """Drops failure rows appended after the last checkpoint; returns count."""
        if not os.path.exists(self.failures_path):
            return 0
        with open(self.failures_path, newline="") as f:
            rows = list(csv.reader(f))[1:]
        extra = len(rows) - expected_rows
        if extra <= 0:
            return 0
        tmp = self.failures_path + ".tmp"
        with open(tmp, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(MANIFEST_HEADER)
            writer.writerows(rows[:expected_rows])
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.failures_path)
        _fsync_dir(self.path)
        return extra


class _WorkerLocal(threading.local):
    deleter: Optional[Deleter] = None


class Runner:
    def __init__(
        self,
        manifest: ManifestInfo,
        run_dir: RunDir,
        state: State,
        deleter_factory: Callable[[], Deleter],
        limiter: TokenBucket,
        workers: int,
        policy: RetryPolicy,
        sleep: Callable[[float], None] = time.sleep,
        rng: Optional[random.Random] = None,
        clock: Callable[[], float] = time.monotonic,
        progress_s: float = 30.0,
        batch_size: int = BATCH_SIZE,
    ) -> None:
        self.manifest = manifest
        self.run_dir = run_dir
        self.state = state
        self.deleter_factory = deleter_factory
        self.limiter = limiter
        self.workers = workers
        self.policy = policy
        self.sleep = sleep
        self.rng: random.Random = rng or random.Random()
        self.clock = clock
        self.progress_s = progress_s
        self.batch_size: int = min(batch_size, BATCH_SIZE)
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.local = _WorkerLocal()
        self.session_rows = 0
        self.session_committed = 0
        self.retries = 0
        self.started: float = clock()

    def _deleter(self) -> Deleter:
        deleter = self.local.deleter
        if deleter is None:
            deleter = self.deleter_factory()
            self.local.deleter = deleter
        return deleter

    def _finalize(self, n: int) -> None:
        with self.lock:
            self.session_rows += n

    def delete_batch(
        self, rows: List[ManifestRow]
    ) -> Optional[List[Tuple[ManifestRow, str]]]:
        """Final outcome per row, or None if stopped before all were final."""
        results: List[Tuple[ManifestRow, str]] = []
        pending = rows
        for attempt in range(self.policy.max_attempts):
            self.limiter.acquire(len(pending))
            try:
                statuses = self._deleter().delete(pending)
                if len(statuses) != len(pending):
                    raise ValueError(
                        f"{len(statuses)} responses for {len(pending)} deletes"
                    )
            except Exception as e:
                logger.warning("batch of %d failed: %r", len(pending), e)
                statuses = [None] * len(pending)
            retry: List[ManifestRow] = []
            for row, status in zip(pending, statuses):
                outcome = classify(status)
                if outcome is None:
                    retry.append(row)
                    continue
                if outcome == PRECONDITION_FAILED:
                    logger.info(
                        "412 generation changed, skipped: %s#%d",
                        row.name,
                        row.generation,
                    )
                elif outcome == FAILED:
                    logger.warning(
                        "HTTP %s, not retried: %s#%d", status, row.name, row.generation
                    )
                results.append((row, outcome))
            self._finalize(len(pending) - len(retry))
            if not retry:
                return results
            if self.stop.is_set():
                return None
            pending = retry
            if attempt + 1 < self.policy.max_attempts:
                with self.lock:
                    self.retries += len(retry)
                self.sleep(self.policy.delay(attempt, self.rng))
        for row in pending:
            logger.warning("retries exhausted: %s#%d", row.name, row.generation)
            results.append((row, FAILED))
        self._finalize(len(pending))
        return results

    def process_chunk(self, index: int, rows: List[ManifestRow]) -> bool:
        """Returns True if the chunk was completed and checkpointed."""
        start = self.clock()
        results: List[Tuple[ManifestRow, str]] = []
        for i in range(0, len(rows), self.batch_size):
            if self.stop.is_set():
                return False
            batch_results = self.delete_batch(rows[i : i + self.batch_size])
            if batch_results is None:
                return False
            results.extend(batch_results)
        counts = {o: 0 for o in OUTCOMES}
        for _, outcome in results:
            counts[outcome] += 1
        failures = [row for row, outcome in results if outcome == FAILED]
        self.commit_chunk(index, counts, failures, self.clock() - start)
        return True

    def commit_chunk(
        self,
        index: int,
        counts: Dict[str, int],
        failures: List[ManifestRow],
        elapsed: float,
    ) -> None:
        with self.lock:
            if failures:
                self.run_dir.append_failures(failures)
            self.state.completed.add(index)
            for o in OUTCOMES:
                self.state.counts[o] += counts[o]
            self.state.failure_rows += len(failures)
            self.run_dir.save_state(self.state)
            self.session_committed += sum(counts.values())
        self.run_dir.event(
            "chunk_done",
            chunk=index,
            rows=sum(counts.values()),
            counts=counts,
            elapsed_s=round(elapsed, 3),
        )

    def progress(self) -> Dict[str, Any]:
        with self.lock:
            done = self.state.done_rows + self.session_rows - self.session_committed
            counts = dict(self.state.counts)
            session_rows = self.session_rows
            retries = self.retries
        elapsed = max(self.clock() - self.started, 1e-9)
        rate = session_rows / elapsed
        remaining = self.state.rows - done
        eta = remaining / rate if rate > 0 else None
        return {
            "done": done,
            "total": self.state.rows,
            "rate_per_s": round(rate, 1),
            "eta_s": round(eta) if eta is not None else None,
            "checkpointed_counts": counts,
            "chunks_done": len(self.state.completed),
            "chunks": self.state.chunks,
            "retries": retries,
        }

    def log_progress(self) -> None:
        p = self.progress()
        eta = (
            str(datetime.timedelta(seconds=p["eta_s"]))
            if p["eta_s"] is not None
            else "?"
        )
        logger.info(
            "%s/%s rows, %s/s, ETA %s, chunks %s/%s, retries %s, %s",
            f"{p['done']:,}",
            f"{p['total']:,}",
            p["rate_per_s"],
            eta,
            p["chunks_done"],
            p["chunks"],
            p["retries"],
            ", ".join(f"{k}={v:,}" for k, v in p["checkpointed_counts"].items()),
        )
        self.run_dir.event("progress", **p)

    def _progress_loop(self, done: threading.Event) -> None:
        while not done.wait(self.progress_s):
            self.log_progress()

    def run(self) -> None:
        """Processes every uncompleted chunk until done or self.stop is set."""
        progress_done = threading.Event()
        reporter = threading.Thread(
            target=self._progress_loop, args=(progress_done,), daemon=True
        )
        reporter.start()
        try:
            with ThreadPoolExecutor(max_workers=self.workers) as pool:
                in_flight: Set[Future[bool]] = set()
                for index, rows in iter_chunks(
                    self.manifest.path, self.state.chunk_size
                ):
                    if self.stop.is_set():
                        break
                    if index in self.state.completed:
                        continue
                    while len(in_flight) >= 2 * self.workers:
                        finished, in_flight = wait(
                            in_flight, timeout=1.0, return_when=FIRST_COMPLETED
                        )
                        for f in finished:
                            f.result()
                    in_flight.add(pool.submit(self.process_chunk, index, rows))
                while in_flight:
                    finished, in_flight = wait(
                        in_flight, timeout=1.0, return_when=FIRST_COMPLETED
                    )
                    for f in finished:
                        f.result()
        finally:
            progress_done.set()
            reporter.join()


def status_report(run_dir: RunDir) -> str:
    state = run_dir.load_state()
    if state is None:
        return f"{run_dir.path}: no state.json (nothing run yet)"
    lines = [state.summary()]
    events = run_dir.read_events()
    if events:
        last = events[-1]
        lines.append(f"last event: {last.get('event')} at {last.get('ts')}")
        if last.get("event") != "session_end":
            lines.append("last session did not log session_end (killed or running)")
    return "\n".join(lines)


def _gcs_deleter_factory(project: str, gcloud_token: bool) -> Callable[[], Deleter]:
    def make() -> Deleter:
        credentials = GcloudUserCredentials() if gcloud_token else None
        return GcsBatchDeleter(gcs.Client(project=project, credentials=credentials))

    return make


def _setup_logging(log_path: str) -> List[logging.Handler]:
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handlers: List[logging.Handler] = [
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(log_path),
    ]
    for h in handlers:
        h.setFormatter(fmt)
        logger.addHandler(h)
    logger.setLevel(logging.INFO)
    return handlers


def _start_state(run_dir: RunDir, manifest: ManifestInfo, args: Any) -> State:
    state = run_dir.load_state()
    if state is None:
        return State(
            manifest_path=os.path.abspath(manifest.path),
            manifest_sha256=manifest.sha256,
            rows=manifest.rows,
            chunk_size=args.chunk_size,
            bucket=args.bucket,
        )
    mismatches = [
        f"{label}: run dir has {old!r}, now {new!r}"
        for label, old, new in [
            ("manifest sha256", state.manifest_sha256, manifest.sha256),
            ("rows", state.rows, manifest.rows),
            ("chunk size", state.chunk_size, args.chunk_size),
            ("bucket", state.bucket, args.bucket),
        ]
        if old != new
    ]
    if mismatches:
        raise ManifestError(mismatches)
    return state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument("--manifest", help="manifest.csv from the dry run")
    parser.add_argument("--bucket", help="bucket every manifest row must name")
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument("--run-dir", help="durable state dir (required with --execute)")
    parser.add_argument("--execute", action="store_true", help="actually delete")
    parser.add_argument("--confirm-count", type=int, help="must equal manifest rows")
    parser.add_argument("--status", action="store_true", help="print run-dir progress")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--max-rate", type=float, default=500.0, help="deletes/sec")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--max-attempts", type=int, default=6)
    parser.add_argument("--progress-seconds", type=float, default=30.0)
    parser.add_argument(
        "--gcloud-token",
        action="store_true",
        help="Authenticate with `gcloud auth print-access-token` instead of ADC",
    )
    return parser


def main(
    argv: Optional[List[str]] = None,
    deleter_factory: Optional[Callable[[], Deleter]] = None,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.status:
        if not args.run_dir:
            parser.error("--status requires --run-dir")
        print(status_report(RunDir(os.path.expanduser(args.run_dir))))
        return 0
    if not args.manifest or not args.bucket:
        parser.error("--manifest and --bucket are required")
    if args.execute and not args.run_dir:
        parser.error("--execute requires --run-dir")

    try:
        manifest = validate_manifest(args.manifest, args.bucket)
    except ManifestError as e:
        print(f"Invalid manifest {args.manifest}; nothing deleted:", file=sys.stderr)
        for error in e.args[0]:
            print(f"  {error}", file=sys.stderr)
        return 2

    if not args.execute:
        print(f"{manifest.rows:,} objects would be deleted from gs://{args.bucket}")
        print(f"manifest sha256 {manifest.sha256}")
        for row in manifest.first_rows:
            print(f"  {row.bucket},{row.name},{row.generation}")
        if args.run_dir:
            print(status_report(RunDir(os.path.expanduser(args.run_dir))))
        print(f"Dry run. To delete: --execute --confirm-count {manifest.rows}")
        return 0

    if args.confirm_count != manifest.rows:
        print(
            f"--confirm-count {args.confirm_count} != {manifest.rows} manifest rows;"
            " nothing deleted",
            file=sys.stderr,
        )
        return 2

    run_dir = RunDir(os.path.expanduser(args.run_dir))
    try:
        run_dir.open()
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 2
    handlers = _setup_logging(run_dir.log_path)
    previous_handlers: Dict[int, Any] = {}
    try:
        try:
            state = _start_state(run_dir, manifest, args)
        except ManifestError as e:
            for error in e.args[0]:
                logger.error("refusing to resume: %s", error)
            return 2
        dropped = run_dir.reconcile_failures(state.failure_rows)
        if dropped:
            logger.info("dropped %d uncheckpointed failure rows", dropped)
        previous = run_dir.read_events()
        if previous and previous[-1].get("event") != "session_end":
            logger.warning("previous session ended without session_end (killed)")
        if state.sessions:
            logger.info("resuming:\n%s", state.summary())
        state.sessions += 1
        run_dir.save_state(state)
        run_dir.event(
            "session_start",
            pid=os.getpid(),
            host=socket.gethostname(),
            manifest=os.path.abspath(manifest.path),
            manifest_sha256=manifest.sha256,
            rows=manifest.rows,
            session=state.sessions,
            args=vars(args),
        )

        runner = Runner(
            manifest=manifest,
            run_dir=run_dir,
            state=state,
            deleter_factory=deleter_factory
            or _gcs_deleter_factory(args.project, args.gcloud_token),
            limiter=TokenBucket(args.max_rate, capacity=BATCH_SIZE, sleep=sleep),
            workers=args.workers,
            policy=RetryPolicy(max_attempts=args.max_attempts),
            sleep=sleep,
            progress_s=args.progress_seconds,
        )
        stopped_by: List[str] = []

        def on_signal(signum: int, frame: Optional[FrameType]) -> None:
            name = signal.Signals(signum).name
            if not stopped_by:
                logger.warning("%s: finishing in-flight batches, then stopping", name)
            stopped_by.append(name)
            runner.stop.set()

        if threading.current_thread() is threading.main_thread():
            for sig in (signal.SIGINT, signal.SIGTERM):
                previous_handlers[sig] = signal.signal(sig, on_signal)

        reason = "complete"
        try:
            runner.run()
            if stopped_by:
                reason = f"signal {stopped_by[0]}"
        except BaseException as e:
            reason = f"error {e!r}"
            raise
        finally:
            runner.log_progress()
            run_dir.event("session_end", reason=reason, counts=state.counts)
            logger.info("session ended (%s)\n%s", reason, state.summary())
        if stopped_by:
            return 130
        return 1 if state.counts[FAILED] else 0
    finally:
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)
        for h in handlers:
            logger.removeHandler(h)
            h.close()
        run_dir.close()


if __name__ == "__main__":
    sys.exit(main())
