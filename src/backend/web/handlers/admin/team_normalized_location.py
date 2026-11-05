import logging
from typing import List, Optional

from flask import flash, redirect, url_for
from google.appengine.ext import ndb
from werkzeug import Response

from backend.common.helpers.deferred import defer_safe
from backend.common.manipulators.team_manipulator import TeamManipulator
from backend.common.models.team import Team
from backend.web.profiled_render import render_template

PURGE_BATCH_SIZE = 500
LEFTOVER_PROPERTY = "normalized_location"


def _leftover_query() -> ndb.Query:
    # Team no longer defines the field, but the stored null is still indexed
    return Team.query(ndb.GenericProperty(LEFTOVER_PROPERTY) == None)  # noqa: E711


def team_normalized_location_dashboard() -> str:
    template_values = {
        "remaining": _leftover_query().count(keys_only=True),
        "batch_size": PURGE_BATCH_SIZE,
    }
    return render_template("admin/team_normalized_location.html", template_values)


def team_normalized_location_purge_post() -> Response:
    defer_safe(
        _purge_team_normalized_locations,
        _queue="admin",
        _target="py3-tasks-io",
    )
    flash(
        "Enqueued Team.normalized_location purge task. Batches self-defer; "
        "watch logs for per-batch purged counts."
    )
    return redirect(url_for("admin.team_normalized_location_dashboard"))


def _drop_leftover_property(team: Team) -> bool:
    # NDB loads unknown stored properties as per-instance GenericProperty fakes
    # and writes them back on put(), so they must be removed from the instance
    # pyre-ignore[16]: NDB instance internals aren't in the stubs
    properties, values = team._properties, team._values
    if LEFTOVER_PROPERTY not in properties:
        return False
    del properties[LEFTOVER_PROPERTY]
    values.pop(LEFTOVER_PROPERTY, None)
    return True


def _purge_team_normalized_locations(
    cursor_urlsafe: Optional[str] = None,
    batch_size: int = PURGE_BATCH_SIZE,
    total_purged: int = 0,
) -> int:
    """
    Remove the leftover null normalized_location property from every Team that
    still stores one, then clear the affected cached queries. The manipulator
    can't express deleting a property the model doesn't define, so this writes
    with put_multi and clears caches through TeamManipulator.clearCache.

    Self-defers the next batch until done. Returns the running total purged.
    """
    # pyre-ignore[16]: pyre stubs don't list ndb.Cursor, but it exists at runtime
    cursor = ndb.Cursor(urlsafe=cursor_urlsafe) if cursor_urlsafe else None
    teams, next_cursor, more = (
        _leftover_query().order(Team.key).fetch_page(batch_size, start_cursor=cursor)
    )

    purged: List[Team] = [t for t in teams if _drop_leftover_property(t)]
    if purged:
        ndb.put_multi(purged)
        TeamManipulator.clearCache(purged)

    total_purged += len(purged)
    logging.info(
        f"Team.normalized_location purge batch: purged {len(purged)} "
        f"(running total: {total_purged})"
    )

    if more and next_cursor is not None:
        defer_safe(
            _purge_team_normalized_locations,
            cursor_urlsafe=next_cursor.urlsafe(),
            batch_size=batch_size,
            total_purged=total_purged,
            _queue="admin",
            _target="py3-tasks-io",
        )
    else:
        logging.info(f"Team.normalized_location purge complete: {total_purged}")
    return total_purged
