import datetime
from typing import List

from flask import abort

from backend.common.decorators import cached_public
from backend.common.models.event_participation import EventParticipation
from backend.common.models.team import Team
from backend.common.queries.event_query import TeamYearEventsQuery
from backend.common.queries.team_query import (
    TeamListQuery,
    TeamParticipationQuery,
    TeamQuery,
)
from backend.web.profiled_render import render_template

MAX_TEAM_NUMBER_EXCLUSIVE = (
    9000  # Support between Team 0 and Team MAX_TEAM_NUMBER_EXCLUSIVE - 1
)
TEAMS_PER_PAGE = 1000
VALID_PAGES = range(
    1, (MAX_TEAM_NUMBER_EXCLUSIVE // TEAMS_PER_PAGE) + 1
)  # + 1 to make range inclusive


@cached_public
def team_detail(team_number: int, year: int, is_canonical: bool = False) -> str:
    team_key = f"frc{team_number}"
    if not Team.validate_key_name(team_key):
        abort(404)
    team_future = TeamQuery(team_key=f"frc{team_number}").fetch_async()
    team = team_future.get_result()
    if not team:
        abort(404)

    events_future = TeamYearEventsQuery(team_key=team.key_name, year=year).fetch_async()
    valid_years_future = TeamParticipationQuery(team_key=team.key_name).fetch_async()

    events_sorted = sorted(
        events_future.get_result(),
        key=lambda e: e.start_date if e.start_date else datetime.datetime(year, 12, 31),
    )  # unknown goes last
    valid_years = sorted(valid_years_future.get_result())

    if not events_sorted:
        abort(404)

    event_participation: List[EventParticipation] = []
    for event in events_sorted:
        event_participation.append(
            EventParticipation(
                event=event,
                matches={},
                wlt=None,
                qual_avg=None,
                elim_avg=None,
                rank=None,
                awards=[],
                playlist="",
                district_points=None,
            )
        )

    template_values = {
        "team": team,
        "year": year,
        "is_canonical": is_canonical,
        "years": valid_years,
        "participation": event_participation,
        # TODO stubbed stuff below
        "hof": {},
        "medias_by_slugname": {},
    }
    return render_template("team_details.html", template_values)


@cached_public
def team_history(team_number: int) -> str:
    abort(501)


@cached_public
def team_canonical(team_number: int) -> str:
    team_future = TeamQuery(team_key=f"frc{team_number}").fetch_async()
    team = team_future.get_result()
    if not team:
        abort(404)

    current_year = datetime.datetime.now().year
    events_future = TeamYearEventsQuery(
        team_key=team.key_name, year=current_year
    ).fetch_async()
    events = events_future.get_result()
    if not events:
        return team_history(team_number)

    return team_detail(team_number, current_year, is_canonical=True)


@cached_public
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
