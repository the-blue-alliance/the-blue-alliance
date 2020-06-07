from flask import render_template

from backend.common.queries.team_query import TeamListQuery

MAX_TEAM_NUMBER_EXCLUSIVE = (
    9000  # Support between Team 0 and Team MAX_TEAM_NUMBER_EXCLUSIVE - 1
)
TEAMS_PER_PAGE = 1000
VALID_PAGES = range(
    1, (MAX_TEAM_NUMBER_EXCLUSIVE // TEAMS_PER_PAGE) + 1
)  # + 1 to make range inclusive


def team_list(page: int) -> str:
    page_labels = []
    cur_page_label = ""
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
    return render_template("team_list.html", **template_values)
