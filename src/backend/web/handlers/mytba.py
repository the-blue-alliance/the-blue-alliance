import datetime
from collections import defaultdict

from flask import request
from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.wrappers import Response

from backend.common.auth import current_user
from backend.common.consts.model_type import ModelType
from backend.common.helpers.award_helper import AwardHelper
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.event_team import EventTeam
from backend.common.models.favorite import Favorite
from backend.common.models.team import Team
from backend.common.queries.award_query import TeamYearAwardsQuery
from backend.common.queries.event_query import TeamYearEventsQuery
from backend.web.decorators import require_login
from backend.web.profiled_render import render_template


@require_login
def mytba_live() -> Response:
    current_season = SeasonHelper.get_current_season()
    year = request.args.get("year")
    if year and year.isdigit():
        year = int(year)
    else:
        year = current_season

    user = none_throws(current_user())
    now = datetime.datetime.now()

    team_favorites_future = Favorite.query(
        Favorite.model_type == ModelType.TEAM, ancestor=user.account_key
    ).fetch_async()

    favorite_team_keys = map(
        lambda f: ndb.Key(Team, f.model_key), team_favorites_future.get_result()
    )
    favorite_teams_future = ndb.get_multi_async(favorite_team_keys)

    favorite_teams = [team_future.get_result() for team_future in favorite_teams_future]

    favorite_teams_events_futures = []
    favorite_teams_awards_futures = {}
    for team in favorite_teams:
        favorite_teams_events_futures.append(
            TeamYearEventsQuery(team.key_name, year).fetch_async()
        )
        favorite_teams_awards_futures[team.key.id()] = TeamYearAwardsQuery(
            team.key_name, year
        ).fetch_async()

    past_events_by_event = {}
    live_events_by_event = {}
    future_events_by_event = {}
    favorite_event_team_keys = []
    for team, events_future in zip(favorite_teams, favorite_teams_events_futures):
        events = events_future.get_result()
        if not events:
            continue
        events = EventHelper.sorted_events(events)  # Sort by date
        for event in events:
            favorite_event_team_keys.append(
                ndb.Key(EventTeam, "{}_{}".format(event.key.id(), team.key.id()))
            )
            if event.within_a_day:
                if event.key_name not in live_events_by_event:
                    live_events_by_event[event.key_name] = (event, [])
                live_events_by_event[event.key_name][1].append(team)
            elif event.start_date < now:
                if event.key_name not in past_events_by_event:
                    past_events_by_event[event.key_name] = (event, [])
                past_events_by_event[event.key_name][1].append(team)
            else:
                if event.key_name not in future_events_by_event:
                    future_events_by_event[event.key_name] = (event, [])
                future_events_by_event[event.key_name][1].append(team)

    event_team_awards = defaultdict(lambda: defaultdict(list))
    for team_key, awards_future in favorite_teams_awards_futures.items():
        for award in awards_future.get_result():
            event_team_awards[award.event.id()][team_key].append(award)

    ndb.get_multi(favorite_event_team_keys)  # Warms context cache

    past_events_with_teams = []
    for event, teams in past_events_by_event.values():
        teams_and_statuses = []
        for team in teams:
            event_team = none_throws(
                EventTeam.get_by_id("{}_{}".format(event.key.id(), team.key.id()))
            )  # Should be in context cache
            teams_and_statuses.append(
                (
                    team,
                    event_team.status,
                    event_team.status_strings,
                    AwardHelper.organize_awards(
                        event_team_awards[event.key.id()][team.key.id()]
                    ),
                )
            )
        teams_and_statuses.sort(key=lambda x: x[0].team_number)
        past_events_with_teams.append((event, teams_and_statuses))
    past_events_with_teams.sort(key=lambda x: x[0].name)
    past_events_with_teams.sort(
        key=lambda x: EventHelper.start_date_or_distant_future(x[0])
    )
    past_events_with_teams.sort(
        key=lambda x: EventHelper.end_date_or_distant_future(x[0])
    )

    live_events_with_teams = []
    for event, teams in live_events_by_event.values():
        teams_and_statuses = []
        for team in teams:
            event_team = none_throws(
                EventTeam.get_by_id("{}_{}".format(event.key.id(), team.key.id()))
            )  # Should be in context cache
            teams_and_statuses.append(
                (
                    team,
                    event_team.status,
                    event_team.status_strings,
                    AwardHelper.organize_awards(
                        event_team_awards[event.key.id()][team.key.id()]
                    ),
                )
            )
        teams_and_statuses.sort(key=lambda x: x[0].team_number)
        live_events_with_teams.append((event, teams_and_statuses))
    live_events_with_teams.sort(key=lambda x: x[0].name)
    live_events_with_teams.sort(
        key=lambda x: EventHelper.start_date_or_distant_future(x[0])
    )
    live_events_with_teams.sort(
        key=lambda x: EventHelper.end_date_or_distant_future(x[0])
    )

    future_events_with_teams = []
    for event, teams in future_events_by_event.values():
        teams.sort(key=lambda t: t.team_number)
        future_events_with_teams.append((event, teams))
    future_events_with_teams.sort(key=lambda x: x[0].name)
    future_events_with_teams.sort(
        key=lambda x: EventHelper.start_date_or_distant_future(x[0])
    )
    future_events_with_teams.sort(
        key=lambda x: EventHelper.end_date_or_distant_future(x[0])
    )

    template_values = {
        "year": year,
        "past_only": year < current_season,
        "past_events_with_teams": past_events_with_teams,
        "live_events_with_teams": live_events_with_teams,
        "future_events_with_teams": future_events_with_teams,
    }

    return render_template("mytba_live.html", template_values)
