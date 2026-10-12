"""Dry-run planner for deduplicating the FRC API response archive (RFC #11012).

READ-ONLY: this script contains no delete code. It lists objects under a
prefix of the archive bucket, decides which snapshots are byte-identical
repeats of the snapshot kept before them, byte-compares a random sample of
those decisions, and writes a Storage Batch Operations manifest. Deleting is a
separate, manual step: a maintainer reviews the outputs and then runs

    gcloud storage batch-operations jobs create ... \\
        --manifest-location=gs://<scratch>/manifest.csv --delete-object

The rule: within one directory (object name up to the last "/"), walk objects
in name order (= time order) and keep an object unless its md5Hash, crc32c and
size all equal those of the previously kept object. Objects missing md5Hash or
crc32c, or younger than --min-age-days, are always kept and start a new run.

Outputs in --out-dir:
  manifest.csv  header "bucket,name,generation", one row per object to delete
                (generation-pinned, so a newer overwrite is never touched).
                Not written if any sampled pair differs.
  summary.csv   per directory: kept, deleted, kept_bytes, deleted_bytes, runs,
                longest_run, missing_checksum, too_young.

Usage:
  uv run python ops/storage/dedupe_frc_api_archive.py \\
      --prefix frc-api-response/v3.0/2025/ --out-dir /tmp/dedupe-2025

Uses Application Default Credentials; pass --gcloud-token to use the active
gcloud account instead. Only object list and object get calls are made.
"""

import argparse
import csv
import datetime
import os
import random
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, Iterable, Iterator, List, Optional, Set, TextIO, Tuple

from google.auth.credentials import Credentials
from google.cloud import storage

DEFAULT_BUCKET = "tbatv-prod-hrd.appspot.com"
DEFAULT_PROJECT = "tbatv-prod-hrd"
USD_PER_GIB_MONTH = 0.026
GIB = 1024**3
UTC = datetime.timezone(datetime.timedelta(0))
LIST_FIELDS = "items(name,generation,md5Hash,crc32c,size,timeCreated),nextPageToken"


@dataclass(frozen=True)
class ObjectInfo:
    name: str
    generation: int
    md5_hash: Optional[str]
    crc32c: Optional[str]
    size: int
    time_created: datetime.datetime

    @property
    def directory(self) -> str:
        return self.name.rpartition("/")[0]


@dataclass(frozen=True)
class Deletion:
    obj: ObjectInfo
    duplicate_of: ObjectInfo


@dataclass
class DirectoryPlan:
    directory: str
    kept: List[ObjectInfo] = field(default_factory=list)
    deletions: List[Deletion] = field(default_factory=list)
    longest_run: int = 0
    missing_checksum: int = 0
    too_young: int = 0

    @property
    def kept_bytes(self) -> int:
        return sum(o.size for o in self.kept)

    @property
    def deleted_bytes(self) -> int:
        return sum(d.obj.size for d in self.deletions)

    @property
    def runs(self) -> int:
        return len(self.kept)


def _same_content(a: ObjectInfo, b: ObjectInfo) -> bool:
    return (
        a.md5_hash is not None
        and a.crc32c is not None
        and a.md5_hash == b.md5_hash
        and a.crc32c == b.crc32c
        and a.size == b.size
    )


def dedupe_directory(
    directory: str, objects: Iterable[ObjectInfo], cutoff: datetime.datetime
) -> DirectoryPlan:
    """Plans one directory. Objects created after `cutoff` are always kept."""
    plan = DirectoryPlan(directory=directory)
    kept: Optional[ObjectInfo] = None
    run = 0
    for obj in sorted(objects, key=lambda o: o.name):
        has_checksums = obj.md5_hash is not None and obj.crc32c is not None
        old_enough = obj.time_created <= cutoff
        if not has_checksums:
            plan.missing_checksum += 1
        if not old_enough:
            plan.too_young += 1
        if (
            has_checksums
            and old_enough
            and kept is not None
            and _same_content(obj, kept)
        ):
            plan.deletions.append(Deletion(obj=obj, duplicate_of=kept))
            run += 1
        else:
            plan.kept.append(obj)
            kept = obj
            run = 1
        plan.longest_run = max(plan.longest_run, run)
    return plan


def group_by_directory(
    objects: Iterable[ObjectInfo],
) -> Iterator[Tuple[str, List[ObjectInfo]]]:
    """Groups a lexically ordered listing by directory, streaming.

    All names under "d/" are contiguous in a lexical listing, so a directory can
    be finished as soon as a name outside it appears. Only directories nested
    inside each other are open at once, which bounds memory. Raises if a
    directory reappears after it was finished (listing not in lexical order).
    """
    stack: List[Tuple[str, List[ObjectInfo]]] = []
    finished: Set[str] = set()
    for obj in objects:
        d = obj.directory
        while stack and not (d == stack[-1][0] or d.startswith(stack[-1][0] + "/")):
            done = stack.pop()
            finished.add(done[0])
            yield done
        if not stack or stack[-1][0] != d:
            if d in finished:
                raise ValueError(f"Listing is not in lexical order: {d!r} reappeared")
            stack.append((d, []))
        stack[-1][1].append(obj)
    while stack:
        yield stack.pop()


def plan_dedupe(
    objects: Iterable[ObjectInfo], cutoff: datetime.datetime
) -> Iterator[DirectoryPlan]:
    for directory, members in group_by_directory(objects):
        yield dedupe_directory(directory, members, cutoff)


SUMMARY_HEADER = [
    "directory",
    "kept",
    "deleted",
    "kept_bytes",
    "deleted_bytes",
    "runs",
    "longest_run",
    "missing_checksum",
    "too_young",
]


def summary_row(plan: DirectoryPlan) -> List[Any]:
    return [
        plan.directory,
        len(plan.kept),
        len(plan.deletions),
        plan.kept_bytes,
        plan.deleted_bytes,
        plan.runs,
        plan.longest_run,
        plan.missing_checksum,
        plan.too_young,
    ]


@dataclass
class Totals:
    kept: int = 0
    deleted: int = 0
    kept_bytes: int = 0
    deleted_bytes: int = 0
    missing_checksum: int = 0
    too_young: int = 0
    directories: int = 0

    def add(self, plan: DirectoryPlan) -> None:
        self.kept += len(plan.kept)
        self.deleted += len(plan.deletions)
        self.kept_bytes += plan.kept_bytes
        self.deleted_bytes += plan.deleted_bytes
        self.missing_checksum += plan.missing_checksum
        self.too_young += plan.too_young
        self.directories += 1

    def report(self) -> str:
        saved = self.deleted_bytes / GIB * USD_PER_GIB_MONTH * 12
        return "\n".join(
            [
                f"directories:      {self.directories:,}",
                f"objects kept:     {self.kept:,} ({self.kept_bytes / GIB:,.2f} GiB)",
                f"objects deleted:  {self.deleted:,} ({self.deleted_bytes / GIB:,.2f} GiB)",
                f"missing checksum: {self.missing_checksum:,} (always kept)",
                f"too young:        {self.too_young:,} (always kept)",
                f"est. saved:       ${saved:,.2f}/yr at ${USD_PER_GIB_MONTH}/GiB-month",
            ]
        )


class Reservoir:
    """Uniform random sample of up to k deletions from a stream."""

    def __init__(self, k: int, rng: random.Random) -> None:
        self.k = k
        self.rng = rng
        self.seen = 0
        self.items: List[Deletion] = []

    def offer(self, item: Deletion) -> None:
        self.seen += 1
        if len(self.items) < self.k:
            self.items.append(item)
        else:
            j = self.rng.randrange(self.seen)
            if j < self.k:
                self.items[j] = item


class GcloudUserCredentials(Credentials):
    """Mints access tokens with `gcloud auth print-access-token`.

    Used with --gcloud-token when Application Default Credentials aren't set up.
    """

    def refresh(self, request: Any) -> None:
        self.token = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        # google-auth compares expiry as naive UTC.
        self.expiry = datetime.datetime.now(UTC).replace(
            tzinfo=None
        ) + datetime.timedelta(minutes=45)


def _to_object_info(blob: Any) -> ObjectInfo:
    return ObjectInfo(
        name=blob.name,
        generation=int(blob.generation),
        md5_hash=blob.md5_hash,
        crc32c=blob.crc32c,
        size=int(blob.size),
        time_created=blob.time_created,
    )


def _list_objects(client: Any, bucket: str, prefix: str) -> Iterator[ObjectInfo]:
    for i, blob in enumerate(
        client.list_blobs(bucket, prefix=prefix, fields=LIST_FIELDS, page_size=1000)
    ):
        if i and i % 100_000 == 0:
            print(f"listed {i:,} objects (at {blob.name})", file=sys.stderr, flush=True)
        yield _to_object_info(blob)


def verify_sample(client: Any, bucket: str, sample: List[Deletion]) -> List[Deletion]:
    """Downloads each pair and returns the ones whose bytes differ."""
    b = client.bucket(bucket)
    mismatches = []
    for d in sample:
        deleted = b.blob(d.obj.name, generation=d.obj.generation).download_as_bytes()
        kept = b.blob(
            d.duplicate_of.name, generation=d.duplicate_of.generation
        ).download_as_bytes()
        if deleted != kept:
            mismatches.append(d)
    return mismatches


def run(
    objects: Iterable[ObjectInfo],
    bucket: str,
    cutoff: datetime.datetime,
    summary_out: TextIO,
    manifest_out: TextIO,
    reservoir: Reservoir,
) -> Totals:
    totals = Totals()
    summary = csv.writer(summary_out)
    summary.writerow(SUMMARY_HEADER)
    manifest = csv.writer(manifest_out)
    manifest.writerow(["bucket", "name", "generation"])
    for plan in plan_dedupe(objects, cutoff):
        totals.add(plan)
        summary.writerow(summary_row(plan))
        for d in plan.deletions:
            manifest.writerow([bucket, d.obj.name, d.obj.generation])
            reservoir.offer(d)
    return totals


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--min-age-days", type=int, default=7)
    parser.add_argument("--sample", type=int, default=200)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument(
        "--gcloud-token",
        action="store_true",
        help="Authenticate with `gcloud auth print-access-token` instead of ADC",
    )
    args = parser.parse_args(argv)

    credentials = GcloudUserCredentials() if args.gcloud_token else None
    client = storage.Client(project=args.project, credentials=credentials)

    os.makedirs(args.out_dir, exist_ok=True)
    manifest_path = os.path.join(args.out_dir, "manifest.csv")
    partial_path = manifest_path + ".partial"
    cutoff = datetime.datetime.now(UTC) - datetime.timedelta(days=args.min_age_days)
    reservoir = Reservoir(args.sample, random.Random(args.seed))

    with (
        open(os.path.join(args.out_dir, "summary.csv"), "w", newline="") as summary_out,
        open(partial_path, "w", newline="") as manifest_out,
    ):
        totals = run(
            _list_objects(client, args.bucket, args.prefix),
            args.bucket,
            cutoff,
            summary_out,
            manifest_out,
            reservoir,
        )

    print(f"gs://{args.bucket}/{args.prefix}")
    print(totals.report())

    mismatches = verify_sample(client, args.bucket, reservoir.items)
    print(
        f"sample verification: {len(reservoir.items) - len(mismatches)}/"
        f"{len(reservoir.items)} pairs byte-identical"
    )
    if mismatches:
        os.remove(partial_path)
        for d in mismatches:
            print(f"MISMATCH: {d.obj.name} != {d.duplicate_of.name}", file=sys.stderr)
        print("Not writing manifest.csv.", file=sys.stderr)
        return 1

    os.replace(partial_path, manifest_path)
    print(f"wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
