from collections import defaultdict

from flask import abort, redirect, request, url_for
from google.appengine.ext import ndb
from werkzeug import Response

from backend.common.models.cached_query_result import CachedQueryResult
from backend.common.queries.database_query import CachedDatabaseQuery
from backend.web.profiled_render import render_template


def cached_query_list() -> str:
    cached_queries = {
        c.__name__: {
            "class_name": c.__name__,
            "cache_version": c.CACHE_VERSION,
            "cache_key_format": c.CACHE_KEY_FORMAT,
        }
        for c in CachedDatabaseQuery.__subclasses__()
    }
    template_args = {"cached_queries": cached_queries}
    return render_template("admin/cached_query_list.html", template_args)


def cached_query_key_lookup_post(query_class_name: str) -> Response:
    cache_key = request.form.get("cache_key")

    if query_class_name is None or cache_key is None:
        abort(400)

    if ":" not in cache_key:
        query_class = next(
            (
                c
                for c in CachedDatabaseQuery.__subclasses__()
                if c.__name__ == query_class_name
            ),
            None,
        )
        if query_class is None:
            abort(404)

        cache_key = query_class.BASE_CACHE_KEY_FORMAT.format(
            cache_key,
            query_class.CACHE_VERSION,
            query_class.DATABASE_QUERY_VERSION,
        )

    return redirect(
        url_for(
            "admin.cached_query_info",
            query_class_name=query_class_name,
            cache_key=cache_key,
        )
    )


def cached_query_detail(query_class_name: str) -> str:
    query_class = next(
        (
            c
            for c in CachedDatabaseQuery.__subclasses__()
            if c.__name__ == query_class_name
        ),
        None,
    )
    if query_class is None:
        abort(404)

    cache_key_splits = query_class.CACHE_KEY_FORMAT.split("_")
    cache_key_prefix_parts = []
    for part in cache_key_splits:
        if "{" not in part and "}" not in part:
            cache_key_prefix_parts.append(part)
    cache_key_prefix = "_".join(cache_key_prefix_parts)
    cached_item_keys = (
        CachedQueryResult.query()
        .filter(
            CachedQueryResult.key  # pyre-ignore[58]
            > ndb.Key(CachedQueryResult, cache_key_prefix)
        )
        .filter(
            CachedQueryResult.key  # pyre-ignore[58]
            < ndb.Key(CachedQueryResult, cache_key_prefix + "_:")
        )
        .fetch(keys_only=True)
    )

    cached_items_by_version = defaultdict(lambda: 0)
    for item in cached_item_keys:
        key_split = item.string_id().split(":")
        query_version = int(key_split[1])
        global_version = key_split[2]
        cached_items_by_version[(global_version, query_version)] += 1

    template_args = {
        "query_class_name": query_class_name,
        "query_class": query_class,
        "cached_items_by_version": cached_items_by_version,
        "total_records": len(cached_item_keys),
    }
    return render_template("admin/cached_query_detail.html", template_args)


def cached_query_info(query_class_name: str, cache_key: str) -> str:
    cached_query = CachedQueryResult.get_by_id(cache_key)
    if cached_query is None:
        abort(404)

    template_args = {
        "query_class_name": query_class_name,
        "cache_key": cache_key,
        "cached_query": cached_query,
    }
    return render_template("admin/cached_query_info.html", template_args)


def cached_query_delete(query_class_name: str, cache_key: str) -> Response:
    cached_query = CachedQueryResult.get_by_id(cache_key)
    if cached_query is None:
        abort(404)

    cached_query.key.delete()
    return redirect(
        url_for("admin.cached_query_detail", query_class_name=query_class_name)
    )


def cached_query_purge_version(
    query_class_name: str, db_version: str, query_version: int
) -> Response:
    query_class = next(
        (
            c
            for c in CachedDatabaseQuery.__subclasses__()
            if c.__name__ == query_class_name
        ),
        None,
    )
    if query_class is None:
        abort(404)

    cache_key_splits = query_class.CACHE_KEY_FORMAT.split("_")
    cache_key_prefix_parts = []
    for part in cache_key_splits:
        if "{" not in part and "}" not in part:
            cache_key_prefix_parts.append(part)
    cache_key_prefix = "_".join(cache_key_prefix_parts)

    cache_key_prefix = "_".join(cache_key_prefix_parts)
    cached_item_keys = (
        CachedQueryResult.query()
        .filter(
            CachedQueryResult.key  # pyre-ignore[58]
            > ndb.Key(CachedQueryResult, cache_key_prefix)
        )
        .filter(
            CachedQueryResult.key  # pyre-ignore[58]
            < ndb.Key(CachedQueryResult, cache_key_prefix + "_:")
        )
        .fetch(keys_only=True)
    )

    keys_to_delete = set()
    for key in cached_item_keys:
        key_split = key.string_id().split(":")
        item_query_version = int(key_split[1])
        item_db_version = key_split[2]
        if query_version == item_query_version and item_db_version == db_version:
            keys_to_delete.add(key)

    ndb.delete_multi(keys_to_delete)

    return redirect(
        url_for("admin.cached_query_detail", query_class_name=query_class_name)
    )
