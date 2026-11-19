import json
from typing import List

from flask import flash, redirect, url_for
from google.appengine.ext import ndb
from werkzeug import Response

from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.web.profiled_render import render_template

# Matches uploaded through the trusted API before #9748 stored this
# non-scoring key in each alliance's breakdown; it now rejects it.
EVENT_KEY = "2025bc"
STRAY_KEY = "alliance"


def _matches_with_stray_key() -> List[Match]:
    matches = Match.query(Match.event == ndb.Key(Event, EVENT_KEY)).fetch()
    return sorted((m for m in matches if _has_stray_key(m)), key=lambda m: m.key_name)


def _has_stray_key(match: Match) -> bool:
    breakdown = _stored_breakdown(match)
    return any(
        isinstance(alliance, dict) and STRAY_KEY in alliance
        for alliance in breakdown.values()
    )


def _stored_breakdown(match: Match) -> dict:
    # The raw JSON, not Match.score_breakdown, which adds computed tba_ fields
    if not match.score_breakdown_json:
        return {}
    try:
        breakdown = json.loads(match.score_breakdown_json)
    except json.JSONDecodeError:
        return {}
    return breakdown if isinstance(breakdown, dict) else {}


def score_breakdown_alliance_key_dashboard() -> str:
    template_values = {
        "event_key": EVENT_KEY,
        "stray_key": STRAY_KEY,
        "match_keys": [m.key_name for m in _matches_with_stray_key()],
    }
    return render_template("admin/score_breakdown_alliance_key.html", template_values)


def score_breakdown_alliance_key_strip_post() -> Response:
    cleaned = strip_stray_alliance_key()
    flash(f"Removed '{STRAY_KEY}' from {len(cleaned)} {EVENT_KEY} match breakdowns.")
    return redirect(url_for("admin.score_breakdown_alliance_key_dashboard"))


def strip_stray_alliance_key() -> List[Match]:
    """
    Remove STRAY_KEY from every alliance breakdown of EVENT_KEY's matches and
    save them through MatchManipulator, which clears their cached queries.
    Leaves every other breakdown field untouched; safe to re-run.
    """
    updated: List[Match] = []
    for match in _matches_with_stray_key():
        breakdown = _stored_breakdown(match)
        for alliance in breakdown.values():
            if isinstance(alliance, dict):
                alliance.pop(STRAY_KEY, None)
        # A full copy, so the merge can't reset fields a partial Match leaves
        # at their defaults (e.g. no_auto_update)
        fields = match.to_dict(exclude=["created", "updated"])
        fields["score_breakdown_json"] = json.dumps(breakdown)
        updated.append(Match(id=match.key_name, **fields))
    if updated:
        MatchManipulator.createOrUpdate(updated)
    return updated
