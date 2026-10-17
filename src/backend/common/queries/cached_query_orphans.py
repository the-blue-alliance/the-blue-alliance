"""
Find and delete CachedQueryResult entities that current code will never read.

A cache key is `{partial}:{CACHE_VERSION}:{DATABASE_QUERY_VERSION}` with an
optional `~dictv{major}.{subversion}` suffix (see CachedDatabaseQuery). Reads only
ever look up the current generation, and entries are only written on a miss, so
an entry from an older generation is never read or overwritten again.

A key is only considered orphaned when it parses cleanly AND either:
  - its DATABASE_QUERY_VERSION is older than the prior-version buffer (the same
    rule as CachedDatabaseQuery.validate_db_version_for_deletion), or
  - its partial key matches at least one known query class's CACHE_KEY_FORMAT and
    it is older than the buffer for every class it matches (CACHE_VERSION or dict
    subversion more than one behind).

Anything unparseable, or not attributable to a known class, is left alone.
Cache key prefixes overlap (e.g. "event_{event_key}" vs "event_awards_{event_key}"),
so classes are matched on the full format, never by prefix.
"""

import importlib
import logging
import pkgutil
import re
from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Pattern, Sequence, Tuple, Type

from google.appengine.ext import ndb

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.helpers.deferred import defer_safe
from backend.common.models.cached_query_result import CachedQueryResult
from backend.common.queries.database_query import CachedDatabaseQuery

# How many generations behind current are kept, so a rolled-back deploy still hits cache
VERSION_BUFFER = 1

PAGE_SIZE = 1000
PAGES_PER_TASK = 50
DELETE_BATCH_SIZE = 500

REASON_DB_VERSION = "db_version"
REASON_CACHE_VERSION = "cache_version"
REASON_DICT_SUBVERSION = "dict_subversion"

_DICT_SUFFIX_RE: Pattern[str] = re.compile(r"dictv(\d+)\.(\d+)")
_FORMAT_FIELD_RE: Pattern[str] = re.compile(r"\{[^{}]*\}")


@dataclass(frozen=True)
class ParsedCacheKey:
    partial: str
    cache_version: int
    db_version: int
    # (api major version, converter subversion), or None for the model cache key
    dict_version: Optional[Tuple[int, int]]


def parse_cache_key(key_string: str) -> Optional[ParsedCacheKey]:
    base, has_suffix, suffix = key_string.partition("~")
    parts = base.rsplit(":", 2)
    if len(parts) != 3 or not parts[0]:
        return None
    try:
        cache_version = int(parts[1])
        db_version = int(parts[2])
    except ValueError:
        return None

    dict_version = None
    if has_suffix:
        match = _DICT_SUFFIX_RE.fullmatch(suffix)
        if match is None:
            return None
        dict_version = (int(match.group(1)), int(match.group(2)))

    return ParsedCacheKey(
        partial=parts[0],
        cache_version=cache_version,
        db_version=db_version,
        dict_version=dict_version,
    )


def _format_regex(cache_key_format: str) -> Pattern[str]:
    literals = _FORMAT_FIELD_RE.split(cache_key_format)
    return re.compile("(.+)".join(re.escape(literal) for literal in literals))


def all_query_classes() -> List[Type[CachedDatabaseQuery]]:
    # Subclasses only register on import, so import every query module first
    import backend.common.queries as queries_package

    for module in pkgutil.walk_packages(
        queries_package.__path__, queries_package.__name__ + "."
    ):
        if ".tests" not in module.name:
            importlib.import_module(module.name)

    found: List[Type[CachedDatabaseQuery]] = []
    pending = list(CachedDatabaseQuery.__subclasses__())
    while pending:
        query_class = pending.pop()
        if query_class not in found:
            found.append(query_class)
            pending.extend(query_class.__subclasses__())
    return found


class OrphanClassifier:
    def __init__(
        self,
        query_classes: Iterable[Type[CachedDatabaseQuery]],
        current_db_version: int = CachedDatabaseQuery.DATABASE_QUERY_VERSION,
    ) -> None:
        self.current_db_version = current_db_version
        self._classes: List[Tuple[Pattern[str], Type[CachedDatabaseQuery]]] = [
            (_format_regex(c.CACHE_KEY_FORMAT), c)
            for c in query_classes
            if c.CACHE_KEY_FORMAT
        ]

    def matching_classes(self, partial: str) -> List[Type[CachedDatabaseQuery]]:
        return [c for regex, c in self._classes if regex.fullmatch(partial)]

    def _dict_version_is_live(
        self,
        query_class: Type[CachedDatabaseQuery],
        dict_version: Optional[Tuple[int, int]],
    ) -> bool:
        if dict_version is None:
            return True
        converter = getattr(query_class, "DICT_CONVERTER", None)
        if converter is None:
            return False
        major, subversion = dict_version
        try:
            current = converter.SUBVERSIONS[ApiMajorVersion(major)]
        except (KeyError, ValueError):
            return False
        return subversion >= current - VERSION_BUFFER

    def orphan_reason(self, key_string: str) -> Optional[str]:
        """Why this key will never be read again, or None if it must be kept."""
        parsed = parse_cache_key(key_string)
        if parsed is None:
            return None

        if parsed.db_version < self.current_db_version - VERSION_BUFFER:
            return REASON_DB_VERSION

        matches = self.matching_classes(parsed.partial)
        if not matches:
            return None

        reasons: List[str] = []
        for query_class in matches:
            if parsed.cache_version < query_class.CACHE_VERSION - VERSION_BUFFER:
                reasons.append(REASON_CACHE_VERSION)
            elif not self._dict_version_is_live(query_class, parsed.dict_version):
                reasons.append(REASON_DICT_SUBVERSION)
            else:
                return None
        return reasons[0]


def _merge_counts(totals: Dict[str, int], counts: Counter[str]) -> Dict[str, int]:
    merged = Counter(totals)
    merged.update(counts)
    return dict(merged)


def purge_orphaned_cached_query_results(
    dry_run: bool = True,
    cursor: Optional[str] = None,
    totals: Optional[Dict[str, int]] = None,
    pages_per_task: int = PAGES_PER_TASK,
    page_size: int = PAGE_SIZE,
) -> Dict[str, int]:
    """
    Scan a slice of CachedQueryResult keys (keys-only), delete orphans unless
    dry_run, then re-enqueue itself from where it stopped. Logs running totals.
    """
    classifier = OrphanClassifier(all_query_classes())
    query = CachedQueryResult.query()
    # pyre-ignore[16]: pyre stubs don't list ndb.Cursor, but it exists at runtime
    start_cursor = ndb.Cursor(urlsafe=cursor) if cursor else None

    counts: Counter[str] = Counter()
    pending_deletes: List[ndb.Key] = []
    more = True
    next_cursor = None
    for _ in range(pages_per_task):
        keys: Sequence[ndb.Key]
        keys, next_cursor, more = query.fetch_page(
            page_size, start_cursor=start_cursor, keys_only=True
        )
        for key in keys:
            counts["scanned"] += 1
            key_string = key.string_id()
            reason = classifier.orphan_reason(key_string) if key_string else None
            if reason is None:
                counts["kept"] += 1
                continue
            counts[f"orphaned:{reason}"] += 1
            if not dry_run:
                pending_deletes.append(key)
                if len(pending_deletes) >= DELETE_BATCH_SIZE:
                    ndb.delete_multi(pending_deletes)
                    pending_deletes = []
        if not more or next_cursor is None:
            more = False
            break
        start_cursor = next_cursor

    if pending_deletes:
        ndb.delete_multi(pending_deletes)

    running = _merge_counts(totals or {}, counts)
    mode = "dry run" if dry_run else "purge"
    if more and next_cursor is not None:
        logging.info(f"Orphaned CachedQueryResult {mode} progress: {running}")
        defer_safe(
            purge_orphaned_cached_query_results,
            dry_run=dry_run,
            cursor=next_cursor.urlsafe().decode(),
            totals=running,
            pages_per_task=pages_per_task,
            page_size=page_size,
            _queue="cache-clearing",
            _target="py3-tasks-io",
        )
    else:
        logging.info(f"Orphaned CachedQueryResult {mode} finished: {running}")
    return running
