from flask import Blueprint, escape, make_response, redirect
# from werkzeug.wrappers import Response

# from backend.common.manipulators.team_manipulator import TeamManipulator
from backend.common.models.keys import EventKey
# from backend.common.models.team import Team
# from backend.common.sitevars.website_blacklist import WebsiteBlacklist


blueprint = Blueprint("tbans", __name__)


@blueprint.route("/awards/<event_key:str>")
def blacklist_website(event_key: EventKey) -> Response:
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
