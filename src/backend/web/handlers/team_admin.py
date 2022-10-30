from collections import defaultdict
from datetime import datetime

from flask import abort, Blueprint, redirect, request, url_for
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.auth import current_user
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.manipulators.media_manipulator import MediaManipulator
from backend.common.manipulators.robot_manipulator import RobotManipulator
from backend.common.models.media import Media
from backend.common.models.robot import Robot
from backend.common.models.suggestion import Suggestion
from backend.common.models.team import Team
from backend.common.models.team_admin_access import TeamAdminAccess
from backend.common.queries.media_query import TeamSocialMediaQuery
from backend.web.decorators import require_login
from backend.web.profiled_render import render_template

blueprint = Blueprint("team_admin", __name__, url_prefix="/")

ALLOWED_SUGGESTION_TYPES = ["media", "social-media", "robot"]
SUGGESTION_NAMES = {
    "media": "Media",
    "social-media": "Social Media",
    "robot": "Robot CAD",
}
SUGGESTION_REVIEW_URL = {
    "media": "/suggest/team/media/review",
    "social-media": "/suggest/team/social/review",
    "robot": "/suggest/cad/review",
}


@blueprint.route("/mod", methods=["GET"])
@require_login
def team_mod():
    user = none_throws(current_user())
    account = user.account_key
    now = datetime.now()

    existing_access = TeamAdminAccess.query(
        TeamAdminAccess.account == account, TeamAdminAccess.expiration > now
    ).fetch()

    # If the current user is an admin, allow them to view this page for any
    # team/year combination
    forced_team = request.args.get("team")
    forced_year = request.args.get("year")
    if user.is_admin and forced_team and forced_year:
        existing_access.append(
            TeamAdminAccess(
                team_number=int(forced_team),
                year=int(forced_year),
            )
        )

    team_keys = [
        ndb.Key(Team, f"frc{access.team_number}") for access in existing_access
    ]
    if not team_keys:
        return redirect(url_for(".team_admin_redeem"))

    years = set([access.year for access in existing_access])
    teams_future = ndb.get_multi_async(team_keys)
    robot_keys = [
        ndb.Key(Robot, Robot.render_key_name(team.id(), now.year)) for team in team_keys
    ]
    robots_future = ndb.get_multi_async(robot_keys)
    social_media_futures = [
        TeamSocialMediaQuery(team_key.id()).fetch_async() for team_key in team_keys
    ]
    team_medias_future = Media.query(
        Media.references.IN(team_keys), Media.year.IN(years)
    ).fetch_async(50)
    suggestions_future = (
        Suggestion.query(Suggestion.review_state == SuggestionState.REVIEW_PENDING)
        .filter(Suggestion.target_model.IN(ALLOWED_SUGGESTION_TYPES))
        .filter(Suggestion.target_key.IN([k.id() for k in team_keys]))
        .fetch_async(limit=50)
    )

    teams = [team.get_result() for team in teams_future]
    team_num_to_team = {t.team_number: t for t in teams}

    robots = [robot.get_result() for robot in robots_future]
    team_num_to_robot_name = {
        int(robot.team.id()[3:]): robot.robot_name
        for robot in robots
        if robot is not None
    }
    team_medias = defaultdict(lambda: defaultdict(list))

    for media in team_medias_future.get_result():
        for reference in media.references:
            if reference in team_keys:
                team_num = reference.id()[3:]
                team_medias[int(team_num)][media.year].append(media)

    team_social_medias = defaultdict(list)
    for team_social_media_future in social_media_futures:
        social_medias = team_social_media_future.get_result()
        for media in social_medias:
            for reference in media.references:
                if reference in team_keys:
                    team_num = reference.id()[3:]
                    team_social_medias[int(team_num)].append(media)

    suggestions_by_team = defaultdict(lambda: defaultdict(list))
    for suggestion in suggestions_future.get_result():
        if not suggestion.target_key:
            continue
        # Assume all the keys are team keys
        team_num = suggestion.target_key[3:]
        suggestions_by_team[int(team_num)][suggestion.target_model].append(suggestion)

    template_values = {
        "existing_access": existing_access,
        "teams": team_num_to_team,
        "robot_names_by_team": team_num_to_robot_name,
        "team_medias": team_medias,
        "team_social_medias": team_social_medias,
        "suggestions_by_team": suggestions_by_team,
        "suggestion_names": SUGGESTION_NAMES,
        "suggestion_review_urls": SUGGESTION_REVIEW_URL,
    }

    return render_template("team_admin_dashboard.html", template_values)


@blueprint.route("/mod", methods=["POST"])
@require_login
def team_mod_post():
    team_number = request.form.get("team_number")
    if not team_number:
        return abort(400)
    team_number = int(team_number)
    team = Team.get_by_id(f"frc{team_number}")
    if not team:
        return abort(400)

    user = none_throws(current_user()).account_key
    now = datetime.now()
    existing_access = TeamAdminAccess.query(
        TeamAdminAccess.account == user,
        TeamAdminAccess.team_number == team_number,
        TeamAdminAccess.expiration > now,
    ).fetch()
    if not existing_access:
        return abort(403)

    action = request.form.get("action")

    if action == "remove_media_reference":
        media_key_name = request.form.get("media_key_name")
        media, team_ref = get_media_and_team_ref(media_key_name, team_number)

        if team_ref in media.references:
            media.references.remove(team_ref)
        if team_ref in media.preferred_references:
            media.preferred_references.remove(team_ref)
        MediaManipulator.createOrUpdate(media, auto_union=False)
    elif action == "remove_media_preferred":
        media_key_name = request.form.get("media_key_name")
        media, team_ref = get_media_and_team_ref(media_key_name, team_number)

        if team_ref in media.preferred_references:
            media.preferred_references.remove(team_ref)
        MediaManipulator.createOrUpdate(media, auto_union=False)
    elif action == "add_media_preferred":
        media_key_name = request.form.get("media_key_name")
        media, team_ref = get_media_and_team_ref(media_key_name, team_number)

        if team_ref not in media.preferred_references:
            media.preferred_references.append(team_ref)
        MediaManipulator.createOrUpdate(media, auto_union=False)
    elif action == "set_team_info":
        robot_name = request.form.get("robot_name").strip()
        current_year = datetime.now().year
        robot_key = Robot.render_key_name(team.key_name, current_year)
        if robot_name:
            robot = Robot(
                id=robot_key,
                team=team.key,
                year=current_year,
                robot_name=robot_name,
            )
            RobotManipulator.createOrUpdate(robot)
        else:
            RobotManipulator.delete_keys([ndb.Key(Robot, robot_key)])
    else:
        return abort(400)

    return redirect(url_for(".team_mod"))


def get_media_and_team_ref(media_key_name, team_number):
    media = Media.get_by_id(media_key_name)
    if not media:
        return abort(400)
    team_ref = Media.create_reference("team", f"frc{team_number}")
    return media, team_ref


@blueprint.route("/mod/redeem", methods=["GET"])
@require_login
def team_admin_redeem():
    user = none_throws(current_user()).account_key
    existing_access = TeamAdminAccess.query(TeamAdminAccess.account == user).fetch()

    team_keys = [
        ndb.Key(Team, f"frc{access.team_number}") for access in existing_access
    ]

    teams = ndb.get_multi(team_keys)
    team_num_to_team = {team.team_number: team for team in teams}

    template_values = {
        "existing_access": existing_access,
        "status": request.args.get("status"),
        "team": request.args.get("team"),
        "teams": team_num_to_team,
    }

    return render_template("team_admin_redeem.html", template_values)


@require_login
@blueprint.route("/mod/redeem", methods=["POST"])
def team_admin_redeem_post():
    user = none_throws(current_user()).account_key

    team_number = request.form.get("team_number")
    if not team_number or not team_number.isdigit():
        return redirect(url_for(".team_admin_redeem", status="invalid_code"))
    team_number = int(team_number)
    auth_code = request.form.get("auth_code").strip()

    access = TeamAdminAccess.query(
        TeamAdminAccess.team_number == team_number,
        TeamAdminAccess.access_code == auth_code,
    ).fetch(1)
    if not access:
        return redirect(url_for(".team_admin_redeem", status="invalid_code"))

    access = access[0]
    if access.account:
        return redirect(url_for(".team_admin_redeem", status="code_used"))

    access.account = user
    access.put()

    return redirect(url_for(".team_admin_redeem", status="success", team=team_number))
