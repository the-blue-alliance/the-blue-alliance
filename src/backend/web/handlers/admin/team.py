from flask import abort, redirect, request, url_for
from werkzeug.wrappers import Response

from backend.common.manipulators.robot_manipulator import RobotManipulator
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event_team import EventTeam
from backend.common.models.media import Media
from backend.common.models.robot import Robot
from backend.common.models.team import Team
from backend.common.queries.team_query import TeamParticipationQuery
from backend.web.profiled_render import render_template


def team_list(page_num: int = 0) -> str:
    MAX_PAGE = 10  # Everything after this will be shown on one page
    PAGE_SIZE = 1000

    if page_num < MAX_PAGE:
        start = PAGE_SIZE * page_num
        end = start + PAGE_SIZE
        teams = (
            Team.query(Team.team_number >= start, Team.team_number < end)
            .order(Team.team_number)
            .fetch()
        )
    else:
        start = PAGE_SIZE * MAX_PAGE
        teams = Team.query(Team.team_number >= start).order(Team.team_number).fetch()

    page_labels = []

    for page in range(MAX_PAGE):
        if page == 0:
            page_labels.append("1-999")
        else:
            page_labels.append("{}'s".format(1000 * page))

    page_labels.append("{}+".format(1000 * MAX_PAGE))

    template_values = {
        "teams": teams,
        "num_teams": Team.query().count(),
        "page_num": page_num,
        "page_labels": page_labels,
    }

    return render_template("admin/team_list.html", template_values)


def team_detail(team_number: int) -> str:
    team = Team.get_by_id(f"frc{team_number}")
    if not team:
        abort(404)

    event_teams = EventTeam.query(EventTeam.team == team.key).fetch(500)
    team_medias = Media.query(Media.references == team.key).fetch(500)
    robots = Robot.query(Robot.team == team.key).fetch()
    district_teams = DistrictTeam.query(DistrictTeam.team == team.key).fetch()
    years_participated = sorted(TeamParticipationQuery(team.key_name).fetch())

    team_medias_by_year = {}
    for media in team_medias:
        if media.year in team_medias_by_year:
            team_medias_by_year[media.year].append(media)
        else:
            team_medias_by_year[media.year] = [media]
    media_years = sorted(team_medias_by_year.keys(), reverse=True)

    template_values = {
        "event_teams": event_teams,
        "team": team,
        "team_media_years": media_years,
        "team_medias_by_year": team_medias_by_year,
        "robots": robots,
        "district_teams": district_teams,
        "years_participated": years_participated,
    }

    return render_template("admin/team_details.html", template_values)


def team_robot_name_update() -> Response:
    team_key = request.values.get("team_key")
    year = int(request.values.get("robot_year"))
    name = request.values.get("robot_name")

    team = Team.get_by_id(team_key)
    if not team:
        abort(404)

    if not year or not name:
        abort(400)

    robot = Robot(
        id=Robot.renderKeyName(team_key, year),
        team=team.key,
        year=year,
        robot_name=name.strip(),
    )
    RobotManipulator.createOrUpdate(robot)

    return redirect(url_for("admin.team_detail", team_number=team.team_number))
