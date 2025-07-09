import datetime
from typing import cast, List

from flask import abort, Blueprint, make_response, redirect, request
from google.appengine.ext import ndb
from markupsafe import Markup
from pyre_extensions import none_throws
from werkzeug.wrappers import Response

from backend.common.consts.auth_type import WRITE_TYPE_NAMES
from backend.common.helpers.event_remapteams_helper import EventRemapTeamsHelper
from backend.common.manipulators.award_manipulator import AwardManipulator
from backend.common.manipulators.event_details_manipulator import (
    EventDetailsManipulator,
)
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.manipulators.team_manipulator import TeamManipulator
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.models.keys import EventKey, TeamKey
from backend.common.models.team import Team
from backend.common.sitevars.website_blacklist import WebsiteBlacklist


blueprint = Blueprint("tasks", __name__)


@blueprint.route("/backend-tasks/do/team_blacklist_website/<team_key>")
def blacklist_website(team_key: TeamKey) -> Response:
    if not Team.validate_key_name(team_key):
        return make_response(f"Bad team key: {Markup.escape(team_key)}", 400)

    team = Team.get_by_id(team_key)

    if team and team.website:
        # Blacklist website
        WebsiteBlacklist.blacklist(team.website)
        # Clear existing website
        team.website = ""
        TeamManipulator.createOrUpdate(team)

    return redirect(f"/backend-tasks/get/team_details/{team_key}")


@blueprint.route("/tasks/do/remap_teams/<event_key>")
def remap_teams(event_key: EventKey) -> str:
    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    if not event.remap_teams:
        return ""

    event.prep_awards()
    event.prep_matches()
    event.prep_teams()

    # Remap matches
    EventRemapTeamsHelper.remapteams_matches(event.matches, event.remap_teams)
    MatchManipulator.createOrUpdate(event.matches)

    # Remap alliance selections
    if event.alliance_selections:
        EventRemapTeamsHelper.remapteams_alliances(
            event.alliance_selections, event.remap_teams
        )
    if event.details and event.details.rankings2:
        EventRemapTeamsHelper.remapteams_rankings2(
            event.details.rankings2, event.remap_teams
        )
    EventDetailsManipulator.createOrUpdate(event.details)

    # Remap awards
    EventRemapTeamsHelper.remapteams_awards(event.awards, event.remap_teams)
    AwardManipulator.createOrUpdate(event.awards, auto_union=False)
    return ""


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
