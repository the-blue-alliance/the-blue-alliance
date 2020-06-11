from flask import abort

from backend.common.models.team import Team
from backend.common.queries.team_query import TeamListQuery, TeamQuery
from backend.web.profiled_render import render_template

MAX_TEAM_NUMBER_EXCLUSIVE = (
    9000  # Support between Team 0 and Team MAX_TEAM_NUMBER_EXCLUSIVE - 1
)
TEAMS_PER_PAGE = 1000
VALID_PAGES = range(
    1, (MAX_TEAM_NUMBER_EXCLUSIVE // TEAMS_PER_PAGE) + 1
)  # + 1 to make range inclusive


def team_canonical(team_number: int) -> str:
    team_key = f"frc{team_number}"
    if not Team.validate_key_name(team_key):
        abort(404)
    team_future = TeamQuery(team_key=f"frc{team_number}").fetch_async()
    team = team_future.get_result()
    if not team:
        abort(404)

    template_values = {
        "team": team,
        # TODO stubbed stuff below
        "year": 2020,
        "hof": {},
        "medias_by_slugname": {},
    }
    return render_template("team_details.html", template_values)


def team_list(page: int) -> str:
    page_labels = []
    cur_page_label = ""
    if page not in VALID_PAGES:
        abort(404)
    for curPage in VALID_PAGES:
        if curPage == 1:
            label = "1-999"
        else:
            label = f"{(curPage - 1) * TEAMS_PER_PAGE}'s"
        page_labels.append(label)
        if curPage == page:
            cur_page_label = label

    teams_1 = TeamListQuery(page=2 * (page - 1)).fetch_async()
    teams_2 = TeamListQuery(page=2 * (page - 1) + 1).fetch_async()
    teams = teams_1.get_result() + teams_2.get_result()

    num_teams = len(teams)
    middle_value = num_teams // 2
    if num_teams % 2 != 0:
        middle_value += 1
    teams_a, teams_b = teams[:middle_value], teams[middle_value:]

    template_values = {
        "teams_a": teams_a,
        "teams_b": teams_b,
        "num_teams": num_teams,
        "page_labels": page_labels,
        "cur_page_label": cur_page_label,
        "current_page": page,
    }
    return render_template("team_list.html", template_values)
