import datetime
import logging
from operator import itemgetter
from typing import List, Optional, Tuple

from flask import abort
from google.appengine.ext import ndb
from werkzeug.wrappers import Response

from backend.common.decorators import cached_public
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.event_team_status_helper import EventTeamStatusHelper
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.helpers.team_helper import TeamHelper
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import DistrictAbbreviation, Year
from backend.common.queries.district_query import (
    DistrictHistoryQuery,
    DistrictQuery,
    DistrictsInYearQuery,
)
from backend.common.queries.event_query import DistrictEventsQuery
from backend.common.queries.team_query import DistrictTeamsQuery, EventTeamsQuery
from backend.web.profiled_render import render_template


@cached_public(timeout=60 * 15)
def district_detail(
    district_abbrev: DistrictAbbreviation, year: Optional[Year]
) -> Response:
    explicit_year = year is not None
    if year is None:
        year = SeasonHelper.get_current_season()

    valid_years = list(reversed(SeasonHelper.get_valid_years()))
    if year not in valid_years:
        abort(404)

    district = DistrictQuery("{}{}".format(year, district_abbrev)).fetch()
    if not district:
        abort(404)

    events_future = DistrictEventsQuery(district.key_name).fetch_async()

    # needed for district teams
    district_teams_future = DistrictTeamsQuery(district.key_name).fetch_async()

    # needed for valid_years
    history_future = DistrictHistoryQuery(district.abbreviation).fetch_async()

    # needed for valid_districts
    districts_in_year_future = DistrictsInYearQuery(district.year).fetch_async()

    # needed for active team statuses
    live_events = []
    live_eventteams_futures = []

    if year == datetime.datetime.now().year:  # Only show active teams for current year
        live_events = EventHelper.week_events()
    for event in live_events:
        live_eventteams_futures.append(EventTeamsQuery(event.key_name).fetch_async())

    events = EventHelper.sorted_events(events_future.get_result())
    events_by_key = {}
    for event in events:
        events_by_key[event.key.id()] = event
    week_events = EventHelper.group_by_week(events)

    valid_districts: List[Tuple[str, DistrictAbbreviation]] = []
    districts_in_year = districts_in_year_future.get_result()
    for dist in districts_in_year:
        valid_districts.append((dist.display_name, dist.abbreviation))
    valid_districts = sorted(valid_districts, key=itemgetter(0))

    teams = TeamHelper.sort_teams(district_teams_future.get_result())
    team_keys = set([t.key.id() for t in teams])

    num_teams = len(teams)
    middle_value = num_teams // 2
    if num_teams % 2 != 0:
        middle_value += 1
    teams_a, teams_b = teams[:middle_value], teams[middle_value:]

    # Currently Competing Team Status
    event_team_keys = []
    for event, teams_future in zip(live_events, live_eventteams_futures):
        for team in teams_future.get_result():
            if team.key.id() in team_keys:
                event_team_keys.append(
                    ndb.Key(EventTeam, "{}_{}".format(event.key.id(), team.key.id()))
                )  # Should be in context cache

    ndb.get_multi(event_team_keys)  # Warms context cache

    live_events_with_teams = []
    for event, teams_future in zip(live_events, live_eventteams_futures):
        teams_and_statuses = []
        has_teams = False
        for team in teams_future.get_result():
            if team.key.id() in team_keys:
                has_teams = True
                event_team = EventTeam.get_by_id(
                    "{}_{}".format(event.key.id(), team.key.id())
                )  # Should be in context cache
                if event_team is None:
                    logging.info(
                        "No EventTeam for {}_{}".format(event.key.id(), team.key.id())
                    )
                    continue
                status_str = {
                    "alliance": EventTeamStatusHelper.generate_team_at_event_alliance_status_string(
                        team.key.id(), event_team.status
                    ),
                    "playoff": EventTeamStatusHelper.generate_team_at_event_playoff_status_string(
                        team.key.id(), event_team.status
                    ),
                }
                teams_and_statuses.append((team, event_team.status, status_str))
        if has_teams:
            teams_and_statuses.sort(key=lambda x: x[0].team_number)
            live_events_with_teams.append((event, teams_and_statuses))

    live_events_with_teams.sort(key=lambda x: x[0].name)
    live_events_with_teams.sort(
        key=lambda x: EventHelper.start_date_or_distant_future(x[0])
    )
    live_events_with_teams.sort(
        key=lambda x: EventHelper.end_date_or_distant_future(x[0])
    )

    # Get valid years
    district_history = history_future.get_result()
    valid_years = map(lambda d: d.year, district_history)
    valid_years = sorted(valid_years)

    rankings = district.rankings
    # Do not show district rankings for 2021
    if district.year == 2021:
        rankings = None

    template_values = {
        "explicit_year": explicit_year,
        "year": year,
        "valid_years": valid_years,
        "valid_districts": valid_districts,
        "district_name": district.display_name,
        "district_abbrev": district_abbrev,
        "week_events": week_events,
        "events_by_key": events_by_key,
        "rankings": rankings,
        "advancement": district.advancement,
        "num_teams": num_teams,
        "teams_a": teams_a,
        "teams_b": teams_b,
        "live_events_with_teams": live_events_with_teams,
    }

    return render_template("district_details.html", template_values)
