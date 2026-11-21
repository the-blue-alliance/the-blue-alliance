from collections import defaultdict

from flask import abort, redirect, request, url_for
from werkzeug import Response

from backend.common.helpers.deferred import defer_safe
from backend.common.manipulators.event_details_manipulator import (
    EventDetailsManipulator,
)
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.manipulators.team_manipulator import TeamManipulator
from backend.common.models.cached_query_result import CachedQueryResult
from backend.common.models.event import Event
from backend.common.models.event import EventDetails
from backend.common.models.match import Match
from backend.common.models.team import Team
from backend.common.queries.cached_query_orphans import (
    purge_orphaned_cached_query_results,
)
from backend.common.queries.database_query import CachedDatabaseQuery
from backend.web.profiled_render import render_template

DATASTORE_PAGE_SIZE = 1000


def cached_query_list() -> str:
    cached_queries = {
        c.__name__: {
            "class_name": c.__name__,
            "cache_version": c.CACHE_VERSION,
            "cache_key_format": c.CACHE_KEY_FORMAT,
        }
        for c in CachedDatabaseQuery.__subclasses__()
    }

    template_args = {
        "cached_queries": cached_queries,
    }
    return render_template(
        "admin/cached_query_list.html", template_values=template_args
    )


def cached_query_key_lookup_post(query_class_name: str) -> Response:
    cache_key = request.form.get("cache_key")

    if query_class_name is None or cache_key is None:
        abort(400)

    if ":" not in cache_key:
        query_class = CachedDatabaseQuery.get_query_class_by_name(query_class_name)
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
    query_class = CachedDatabaseQuery.get_query_class_by_name(query_class_name)
    if query_class is None:
        abort(404)

    cache_key_prefix = CachedQueryResult.cache_key_prefix_from_format(
        query_class.CACHE_KEY_FORMAT
    )

    cached_items_by_version = defaultdict(lambda: 0)
    db_version_counts = defaultdict(lambda: 0)
    total_records = 0
    for item in CachedQueryResult.iter_keys_by_cache_key_prefix(
        cache_key_prefix, DATASTORE_PAGE_SIZE
    ):
        total_records += 1
        key_string = item.string_id()
        if key_string is None:
            continue
        query_version = CachedQueryResult.query_version_from_key_string(key_string)
        db_version = CachedQueryResult.db_version_from_key_string(key_string)
        if query_version is None or db_version is None:
            continue
        cached_items_by_version[(db_version, query_version)] += 1
        db_version_counts[db_version] += 1

    template_args = {
        "query_class_name": query_class_name,
        "query_class": query_class,
        "current_db_version": CachedDatabaseQuery.DATABASE_QUERY_VERSION,
        "db_version_counts": db_version_counts,
        "cached_items_by_version": cached_items_by_version,
        "total_records": total_records,
    }
    return render_template(
        "admin/cached_query_detail.html", template_values=template_args
    )


def cached_query_info(query_class_name: str, cache_key: str) -> str:
    cached_query = CachedQueryResult.get_by_id(cache_key)
    if cached_query is None:
        abort(404)

    template_args = {
        "query_class_name": query_class_name,
        "cache_key": cache_key,
        "cached_query": cached_query,
    }
    return render_template(
        "admin/cached_query_info.html", template_values=template_args
    )


def cached_query_delete(query_class_name: str, cache_key: str) -> Response:
    cached_query = CachedQueryResult.get_by_id(cache_key)
    if cached_query is None:
        abort(404)

    cached_query.key.delete()
    return redirect(
        url_for("admin.cached_query_detail", query_class_name=query_class_name)
    )


def cached_query_purge_orphans() -> Response:
    """Enqueue a scan for cache entries no current query will read; dry run unless asked."""
    dry_run = request.form.get("execute") != "true"
    defer_safe(
        purge_orphaned_cached_query_results,
        dry_run=dry_run,
        _queue="cache-clearing",
        _target="py3-tasks-io",
    )
    return redirect(url_for("admin.cached_query_list"))


def clear_model_cache(model_type: str, model_key: str) -> Response:
    match model_type:
        case "event":
            event = Event.get_by_id(model_key)
            if not event:
                abort(404)
            EventManipulator.clearCache(event)

            event_details = EventDetails.get_by_id(model_key)
            if event_details:
                EventDetailsManipulator.clearCache(event_details)
            return redirect(url_for("admin.event_detail", event_key=model_key))
        case "match":
            match = Match.get_by_id(model_key)
            if not match:
                abort(404)
            MatchManipulator.clearCache(match)
            return redirect(url_for("admin.match_detail", match_key=model_key))
        case "team":
            team = Team.get_by_id(model_key)
            if not team:
                abort(404)
            TeamManipulator.clearCache(team)
            return redirect(url_for("admin.team_detail", team_number=team.team_number))

    return redirect(url_for("admin.admin_home"))
