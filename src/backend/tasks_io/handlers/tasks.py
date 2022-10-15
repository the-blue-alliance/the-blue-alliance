from flask import abort, Blueprint, escape, make_response, redirect
from werkzeug.wrappers import Response

from backend.common.helpers.event_remapteams_helper import EventRemapTeamsHelper
from backend.common.manipulators.award_manipulator import AwardManipulator
from backend.common.manipulators.event_details_manipulator import (
    EventDetailsManipulator,
)
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.manipulators.team_manipulator import TeamManipulator
from backend.common.models.event import Event
from backend.common.models.keys import EventKey, TeamKey
from backend.common.models.team import Team
from backend.common.sitevars.website_blacklist import WebsiteBlacklist


blueprint = Blueprint("tasks", __name__)


@blueprint.route("/backend-tasks/do/team_blacklist_website/<team_key>")
def blacklist_website(team_key: TeamKey) -> Response:
    if not Team.validate_key_name(team_key):
        return make_response(f"Bad team key: {escape(team_key)}", 400)

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

    event.prep_awards_matches_teams()

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
