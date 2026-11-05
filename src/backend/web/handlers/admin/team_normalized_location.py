import logging
from typing import Dict, List, Optional

from flask import flash, redirect, url_for
from google.appengine.ext import ndb
from werkzeug import Response

from backend.common.helpers.deferred import defer_safe
from backend.common.manipulators.team_manipulator import TeamManipulator
from backend.common.models.team import Team
from backend.web.profiled_render import render_template

CLEAR_BATCH_SIZE = 500


def team_normalized_location_dashboard() -> str:
    # Indexed subfield; every geocoded location has a country
    remaining = Team.query(Team.normalized_location.country > "").count()
    template_values = {
        "remaining": remaining,
        "batch_size": CLEAR_BATCH_SIZE,
    }
    return render_template("admin/team_normalized_location.html", template_values)


def team_normalized_location_clear_post() -> Response:
    defer_safe(
        _clear_team_normalized_locations,
        _queue="admin",
        _target="py3-tasks-io",
    )
    flash(
        "Enqueued Team.normalized_location clear task. Batches self-defer; "
        "watch logs for per-batch scanned/cleared counts."
    )
    return redirect(url_for("admin.team_normalized_location_dashboard"))


def _clear_team_normalized_locations(
    cursor_urlsafe: Optional[str] = None,
    batch_size: int = CLEAR_BATCH_SIZE,
    totals: Optional[Dict[str, int]] = None,
) -> Dict[str, int]:
    """
    Page through every Team and clear the deprecated normalized_location,
    writing through TeamManipulator so affected cached queries are cleared.
    Teams without one are not written, so re-running is a no-op.

    Self-defers the next batch until the scan completes. Returns running totals.
    """
    # pyre-ignore[16]: pyre stubs don't list ndb.Cursor, but it exists at runtime
    cursor = ndb.Cursor(urlsafe=cursor_urlsafe) if cursor_urlsafe else None
    teams, next_cursor, more = Team.query().fetch_page(batch_size, start_cursor=cursor)

    to_clear: List[Team] = []
    for team in teams:
        if team.normalized_location is not None:
            team.normalized_location = None
            to_clear.append(team)
    if to_clear:
        TeamManipulator.createOrUpdate(to_clear)

    running = dict(totals or {"scanned": 0, "cleared": 0})
    running["scanned"] += len(teams)
    running["cleared"] += len(to_clear)
    logging.info(
        f"Team.normalized_location clear batch: scanned {len(teams)}, "
        f"cleared {len(to_clear)} (running totals: {running})"
    )

    if more and next_cursor is not None:
        defer_safe(
            _clear_team_normalized_locations,
            cursor_urlsafe=next_cursor.urlsafe(),
            batch_size=batch_size,
            totals=running,
            _queue="admin",
            _target="py3-tasks-io",
        )
    else:
        logging.info(f"Team.normalized_location clear complete: {running}")
    return running
