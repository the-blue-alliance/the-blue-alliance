import datetime
from typing import cast, List

from flask import abort, Blueprint, make_response, redirect, request, url_for
from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from markupsafe import Markup
from pyre_extensions import none_throws
from werkzeug.wrappers import Response

from backend.common.consts.auth_type import WRITE_TYPE_NAMES
from backend.common.helpers.event_remapteams_helper import EventRemapTeamsHelper
from backend.common.manipulators.team_manipulator import TeamManipulator
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.models.keys import EventKey, TeamKey, Year
from backend.common.models.team import Team
from backend.common.sitevars.website_blocklist import WebsiteBlocklist

blueprint = Blueprint("tasks", __name__)


@blueprint.route("/backend-tasks/do/team_blacklist_website/<team_key>")
def blacklist_website(team_key: TeamKey) -> Response:
    if not Team.validate_key_name(team_key):
        return make_response(f"Bad team key: {Markup.escape(team_key)}", 400)

    team = Team.get_by_id(team_key)

    if team and team.website:
        # Blacklist website
        WebsiteBlocklist.blacklist(team.website)
        # Clear existing website
        team.website = ""
        TeamManipulator.createOrUpdate(team)

    return redirect(f"/backend-tasks/get/team_details/{team_key}")


@blueprint.route("/tasks/do/remap_teams/<event_key>")
def remap_teams(event_key: EventKey) -> str:
    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    EventRemapTeamsHelper.remap_teams(event_key)
    return ""


@blueprint.route("/tasks/enqueue/remap_teams/<int:year>")
def enqueue_remap_teams(year: Year) -> Response:
    event_keys = [
        event.key_name
        for event in Event.query(Event.year == year).fetch()
        if event.remap_teams
    ]
    for event_key in event_keys:
        taskqueue.add(
            url=url_for("tasks.remap_teams", event_key=event_key),
            method="GET",
            target="py3-tasks-io",
        )

    if "X-Appengine-Taskname" not in request.headers:
        return make_response(f"Enqueued for: {event_keys}")

    return make_response("")


@blueprint.route("/tasks/do/archive_api_keys")
def archive_api_keys() -> str:
    keys: List[ApiAuthAccess] = ApiAuthAccess.query(
        ndb.AND(
            cast(ndb.IntegerProperty, ApiAuthAccess.auth_types_enum).IN(
                list(WRITE_TYPE_NAMES.keys())
            ),
            ApiAuthAccess.expiration == None,  # noqa: E711
        )
    ).fetch()

    current_year = datetime.datetime.now().year
    new_expiration = datetime.datetime(month=1, day=1, year=current_year)
    to_update = []

    for key in keys:
        event_years = (
            int(none_throws(event_key.string_id())[:4]) for event_key in key.event_list
        )
        if all(event_year < current_year for event_year in event_years):
            key.expiration = new_expiration
            to_update.append(key)

    if to_update:
        ndb.put_multi(to_update)

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return f"Updated: {','.join([t.key.id() for t in to_update])}"

    return ""
