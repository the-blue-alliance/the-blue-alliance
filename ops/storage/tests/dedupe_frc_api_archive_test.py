import datetime
import io
import random
from typing import List, Optional

import pytest

from storage.dedupe_frc_api_archive import (
    dedupe_directory,
    ObjectInfo,
    plan_dedupe,
    Reservoir,
    run,
    UTC,
)

CUTOFF = datetime.datetime(2026, 1, 1, tzinfo=UTC)
OLD = datetime.datetime(2025, 4, 1, tzinfo=UTC)
NEW = datetime.datetime(2026, 1, 5, tzinfo=UTC)


def obj(
    name: str,
    md5: Optional[str] = "md5A",
    crc: Optional[str] = "crcA",
    size: int = 10,
    created: datetime.datetime = OLD,
) -> ObjectInfo:
    return ObjectInfo(
        name=name,
        generation=1,
        md5_hash=md5,
        crc32c=crc,
        size=size,
        time_created=created,
    )


def kept_names(objects: List[ObjectInfo]) -> List[str]:
    return [o.name for p in plan_dedupe(objects, CUTOFF) for o in p.kept]


def deleted_names(objects: List[ObjectInfo]) -> List[str]:
    return [d.obj.name for p in plan_dedupe(objects, CUTOFF) for d in p.deletions]


def test_reverted_content_keeps_first_of_each_run() -> None:
    # A A B A keeps the first A, B and the reverted A.
    objects = [
        obj("d/1.json"),
        obj("d/2.json"),
        obj("d/3.json", md5="md5B", crc="crcB"),
        obj("d/4.json"),
    ]
    assert kept_names(objects) == ["d/1.json", "d/3.json", "d/4.json"]


def test_deleted_object_points_at_kept_duplicate() -> None:
    # Each deletion records the kept object it duplicates.
    plan = dedupe_directory("d", [obj("d/1.json"), obj("d/2.json")], CUTOFF)
    assert plan.deletions[0].duplicate_of.name == "d/1.json"


def test_same_md5_different_crc32c_kept() -> None:
    # A matching md5Hash alone is not enough.
    objects = [obj("d/1.json"), obj("d/2.json", crc="crcB")]
    assert deleted_names(objects) == []


def test_same_md5_different_size_kept() -> None:
    # Matching checksums with a different size is kept.
    objects = [obj("d/1.json"), obj("d/2.json", size=11)]
    assert deleted_names(objects) == []


def test_missing_md5_never_deleted() -> None:
    # Objects without md5Hash are kept and start a new run.
    objects = [obj("d/1.json", md5=None), obj("d/2.json", md5=None)]
    assert deleted_names(objects) == []


def test_missing_crc32c_never_deleted() -> None:
    # Objects without crc32c are kept and start a new run.
    objects = [obj("d/1.json", crc=None), obj("d/2.json", crc=None)]
    assert deleted_names(objects) == []


def test_object_after_missing_checksum_starts_new_run() -> None:
    # A after a checksum-less object is kept, then the next A is deleted.
    objects = [
        obj("d/1.json"),
        obj("d/2.json", md5=None),
        obj("d/3.json"),
        obj("d/4.json"),
    ]
    assert deleted_names(objects) == ["d/4.json"]


def test_directory_boundary_resets_run() -> None:
    # Identical content in a different directory is kept.
    objects = [obj("a/1.json"), obj("b/1.json")]
    assert deleted_names(objects) == []


def test_subdirectory_is_its_own_directory() -> None:
    # Nested directories interleaved in the listing are planned separately.
    objects = [obj("a/1.json"), obj("a/b/1.json"), obj("a/b/2.json"), obj("a/z.json")]
    plans = {p.directory: p for p in plan_dedupe(objects, CUTOFF)}
    assert [d.obj.name for d in plans["a"].deletions] == ["a/z.json"]


def test_young_object_kept() -> None:
    # Objects newer than the cutoff are never deleted.
    objects = [obj("d/1.json"), obj("d/2.json", created=NEW)]
    assert deleted_names(objects) == []


def test_young_object_starts_new_run() -> None:
    # The young object becomes the kept object for later comparisons.
    plan = dedupe_directory(
        "d",
        [obj("d/1.json"), obj("d/2.json", created=NEW), obj("d/3.json")],
        CUTOFF,
    )
    assert plan.deletions[0].duplicate_of.name == "d/2.json"


def test_orders_by_name_not_listing_order() -> None:
    # Listing order within a directory doesn't matter; name order does.
    objects = [
        obj("d/3.json"),
        obj("d/1.json"),
        obj("d/2.json", md5="md5B", crc="crcB"),
    ]
    assert kept_names(objects) == ["d/1.json", "d/2.json", "d/3.json"]


def test_unordered_listing_across_directories_raises() -> None:
    # A directory reappearing after another one means the listing isn't lexical.
    objects = [obj("a/1.json"), obj("b/1.json"), obj("a/2.json")]
    with pytest.raises(ValueError):
        list(plan_dedupe(objects, CUTOFF))


def test_summary_counts_and_bytes() -> None:
    # Summary row has kept/deleted counts and bytes, runs and longest run.
    objects = [
        obj("d/1.json", size=10),
        obj("d/2.json", size=10),
        obj("d/3.json", size=10),
        obj("d/4.json", md5="md5B", crc="crcB", size=7),
        obj("d/5.json", md5=None, size=3),
        obj("d/6.json", md5="md5C", crc="crcC", size=5, created=NEW),
    ]
    summary, manifest = io.StringIO(), io.StringIO()
    run(objects, "bkt", CUTOFF, summary, manifest, Reservoir(0, random.Random(0)))
    assert summary.getvalue().splitlines() == [
        "directory,kept,deleted,kept_bytes,deleted_bytes,runs,longest_run,"
        "missing_checksum,too_young",
        "d,4,2,25,20,4,3,1,1",
    ]


def test_manifest_rows() -> None:
    # Manifest is "bucket,name,generation" with one row per deletion.
    summary, manifest = io.StringIO(), io.StringIO()
    run(
        [obj("d/1.json"), obj("d/2.json")],
        "bkt",
        CUTOFF,
        summary,
        manifest,
        Reservoir(0, random.Random(0)),
    )
    assert manifest.getvalue().splitlines() == [
        "bucket,name,generation",
        "bkt,d/2.json,1",
    ]


def test_totals() -> None:
    # Totals sum objects and bytes over directories.
    summary, manifest = io.StringIO(), io.StringIO()
    totals = run(
        [obj("a/1.json"), obj("a/2.json"), obj("b/1.json", size=4)],
        "bkt",
        CUTOFF,
        summary,
        manifest,
        Reservoir(0, random.Random(0)),
    )
    assert (totals.kept, totals.deleted, totals.kept_bytes, totals.deleted_bytes) == (
        2,
        1,
        14,
        10,
    )


def test_reservoir_samples_at_most_k() -> None:
    # The sample is capped at the requested size.
    summary, manifest = io.StringIO(), io.StringIO()
    reservoir = Reservoir(2, random.Random(0))
    run(
        [obj(f"d/{i}.json") for i in range(10)],
        "bkt",
        CUTOFF,
        summary,
        manifest,
        reservoir,
    )
    assert (reservoir.seen, len(reservoir.items)) == (9, 2)
