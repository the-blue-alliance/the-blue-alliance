import datetime
from datetime import timedelta
from typing import Optional

from flask import abort, Response, redirect, url_for
from backend.common.consts.media_type import MediaType

from backend.common.decorators import cached_public
from backend.common.flask_cache import make_cached_response
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.keys import TeamNumber, Year
from backend.common.models.media import Media
from backend.common.models.team import Team
from backend.common.queries.event_query import TeamYearEventsQuery
from backend.common.queries.team_query import (
    TeamListQuery,
    TeamQuery,
)
from backend.web.profiled_render import render_template
from backend.web.renderers.team_renderer import TeamRenderer

MAX_TEAM_NUMBER_EXCLUSIVE = (
    9000  # Support between Team 0 and Team MAX_TEAM_NUMBER_EXCLUSIVE - 1
)
TEAMS_PER_PAGE = 1000
VALID_PAGES = range(
    1, (MAX_TEAM_NUMBER_EXCLUSIVE // TEAMS_PER_PAGE) + 1
)  # + 1 to make range inclusive


@cached_public
def team_detail(
    team_number: TeamNumber, year: Year, is_canonical: bool = False
) -> Response:
    team_key = f"frc{team_number}"
    if not Team.validate_key_name(team_key):
        abort(404)
    if year not in SeasonHelper.get_valid_years():
        abort(404)
    team_future = TeamQuery(team_key=f"frc{team_number}").fetch_async()
    team = team_future.get_result()
    if not team:
        abort(404)

    template_values, short_cache = TeamRenderer.render_team_details(
        team, year, is_canonical
    )
    if template_values is None:
        abort(404)
    return make_cached_response(
        render_template("team_details.html", template_values),
        ttl=timedelta(seconds=61) if short_cache else timedelta(days=1),
    )


@cached_public
def team_history(team_number: TeamNumber, is_canonical: bool = False) -> Response:
    team_key = f"frc{team_number}"
    if not Team.validate_key_name(team_key):
        abort(404)
    team_future = TeamQuery(team_key=f"frc{team_number}").fetch_async()
    team = team_future.get_result()
    if not team:
        abort(404)

    template_values, short_cache = TeamRenderer.render_team_history(team, is_canonical)
    return make_cached_response(
        render_template("team_history.html", template_values),
        ttl=timedelta(minutes=5) if short_cache else timedelta(days=1),
    )


@cached_public
def team_canonical(team_number: TeamNumber) -> Response:
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
        return team_history(team_number, is_canonical=True)

    return team_detail(team_number, current_year, is_canonical=True)


@cached_public(ttl=timedelta(days=7))
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
        "current_page": page
    }
    return render_template("team_list.html", template_values)


@cached_public
def avatar_list(year: Optional[Year] = None) -> Response:
    year = year or SeasonHelper.get_current_season()

    valid_years = list(range(2018, SeasonHelper.get_max_year() + 1))
    valid_years.remove(2021)  # No avatars in 2021 :(

    if year not in valid_years:
        abort(404)

    avatars_future = Media.query(Media.media_type_enum
                                 == MediaType.AVATAR, Media.year == year).fetch_async()
    avatars = sorted(avatars_future.get_result(),
                     key=lambda a: int(a.references[0].id()[3:]))

    template_values = {
        "year": year,
        "valid_years": valid_years,
        "avatars": avatars
    }

    return render_template("avatars.html", template_values)
