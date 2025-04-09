from typing import Optional

from flask import Response

from backend.api.handlers.decorators import (
    api_authenticated,
    validate_keys,
)
from backend.api.handlers.helpers.model_properties import (
    filter_event_properties,
    filter_match_properties,
    filter_team_properties,
    ModelType,
)
from backend.api.handlers.helpers.profiled_jsonify import profiled_jsonify
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.consts.media_tag import get_enum_from_url
from backend.common.consts.teams import TEAM_PAGE_SIZE
from backend.common.decorators import cached_public
from backend.common.models.event_team import EventTeam
from backend.common.models.history import History
from backend.common.models.keys import EventKey, TeamKey
from backend.common.models.team import Team
from backend.common.queries.award_query import (
    TeamAwardsQuery,
    TeamEventAwardsQuery,
    TeamYearAwardsQuery,
)
from backend.common.queries.district_query import TeamDistrictsQuery
from backend.common.queries.event_query import (
    TeamEventsQuery,
    TeamYearEventsQuery,
    TeamYearEventTeamsQuery,
)
from backend.common.queries.match_query import (
    TeamEventMatchesQuery,
    TeamYearMatchesQuery,
)
from backend.common.queries.media_query import (
    TeamSocialMediaQuery,
    TeamTagMediasQuery,
    TeamYearMediaQuery,
    TeamYearTagMediasQuery,
)
from backend.common.queries.robot_query import TeamRobotsQuery
from backend.common.queries.team_query import (
    TeamListQuery,
    TeamListYearQuery,
    TeamParticipationQuery,
    TeamQuery,
)


@api_authenticated
@validate_keys
@cached_public
def team(team_key: TeamKey, model_type: Optional[ModelType] = None) -> Response:
    """
    Returns details about one team, specified by |team_key|.
    """
    track_call_after_response("team", team_key, model_type)

    team = TeamQuery(team_key=team_key).fetch_dict(ApiMajorVersion.API_V3)
    if model_type is not None:
        team = filter_team_properties([team], model_type)[0]
    return profiled_jsonify(team)


@api_authenticated
@validate_keys
@cached_public
def team_history(team_key: TeamKey) -> Response:
    track_call_after_response("team/history", team_key)

    events_future = TeamEventsQuery(team_key=team_key).fetch_dict_async(
        ApiMajorVersion.API_V3
    )
    awards_future = TeamAwardsQuery(team_key=team_key).fetch_dict_async(
        ApiMajorVersion.API_V3
    )

    events = events_future.get_result()
    awards = awards_future.get_result()

    history: History = History(events=events, awards=awards)
    return profiled_jsonify(history)


@api_authenticated
@validate_keys
@cached_public
def team_years_participated(team_key: TeamKey) -> Response:
    """
    Returns a list of years the given Team participated in an event.
    """
    track_call_after_response("team/years_participated", team_key)

    years_participated = TeamParticipationQuery(team_key=team_key).fetch()
    years_participated = sorted(years_participated)
    return profiled_jsonify(years_participated)


@api_authenticated
@validate_keys
@cached_public
def team_history_districts(team_key: TeamKey) -> Response:
    """
    Returns a list of all DistrictTeam models associated with the given Team.
    """
    track_call_after_response("team/history/districts", team_key)

    team_districts = TeamDistrictsQuery(team_key=team_key).fetch_dict(
        ApiMajorVersion.API_V3
    )
    return profiled_jsonify(team_districts)


@api_authenticated
@validate_keys
@cached_public
def team_history_robots(team_key: TeamKey) -> Response:
    """
    Returns a list of all Robot models associated with the given Team.
    """
    track_call_after_response("team/history/robots", team_key)

    team_robots = TeamRobotsQuery(team_key=team_key).fetch_dict(ApiMajorVersion.API_V3)
    return profiled_jsonify(team_robots)


@api_authenticated
@validate_keys
@cached_public
def team_social_media(team_key: TeamKey) -> Response:
    """
    Returns a list of all social media models associated with the given Team.
    """
    track_call_after_response("team/social_media", team_key)

    team_social_media = TeamSocialMediaQuery(team_key=team_key).fetch_dict(
        ApiMajorVersion.API_V3
    )
    return profiled_jsonify(team_social_media)


@api_authenticated
@validate_keys
@cached_public
def team_events(
    team_key: TeamKey,
    year: Optional[int] = None,
    model_type: Optional[ModelType] = None,
) -> Response:
    """
    Returns a list of all event models associated with the given Team.
    Optionally only returns events from the specified year.
    """
    api_action = "team/events"
    if year is not None:
        api_action += f"/{year}"
    track_call_after_response(api_action, team_key, model_type)

    if year is None:
        team_events = TeamEventsQuery(team_key=team_key).fetch_dict(
            ApiMajorVersion.API_V3
        )
    else:
        team_events = TeamYearEventsQuery(team_key=team_key, year=year).fetch_dict(
            ApiMajorVersion.API_V3
        )

    if model_type is not None:
        team_events = filter_event_properties(team_events, model_type)
    return profiled_jsonify(team_events)


@api_authenticated
@validate_keys
@cached_public
def team_events_statuses_year(team_key: TeamKey, year: int) -> Response:
    """
    Returns a dict of { event_key: status_dict } for all events in the given year for the associated team.
    """
    track_call_after_response("team/events/statuses", f"{team_key}/{year}")

    event_teams = TeamYearEventTeamsQuery(team_key=team_key, year=year).fetch()
    statuses = {}
    for event_team in event_teams:
        status = event_team.status
        if status is not None:
            status_strings = event_team.status_strings
            status.update(
                {
                    "alliance_status_str": status_strings["alliance"],
                    "playoff_status_str": status_strings["playoff"],
                    "overall_status_str": status_strings["overall"],
                }
            )
        statuses[event_team.event.id()] = status
    return profiled_jsonify(statuses)


@api_authenticated
@validate_keys
@cached_public
def team_event_matches(
    team_key: TeamKey, event_key: EventKey, model_type: Optional[ModelType] = None
) -> Response:
    """
    Returns a list of matches for a team at an event.
    """
    track_call_after_response(
        "team/event/matches", f"{team_key}/{event_key}", model_type
    )

    matches = TeamEventMatchesQuery(team_key=team_key, event_key=event_key).fetch_dict(
        ApiMajorVersion.API_V3
    )

    if model_type is not None:
        matches = filter_match_properties(matches, model_type)
    return profiled_jsonify(matches)


@api_authenticated
@validate_keys
@cached_public
def team_event_awards(team_key: TeamKey, event_key: EventKey) -> Response:
    """
    Returns a list of awards for a team at an event.
    """
    track_call_after_response("team/event/awards", f"{team_key}/{event_key}")

    awards = TeamEventAwardsQuery(team_key=team_key, event_key=event_key).fetch_dict(
        ApiMajorVersion.API_V3
    )
    return profiled_jsonify(awards)


@api_authenticated
@validate_keys
@cached_public
def team_event_status(team_key: TeamKey, event_key: EventKey) -> Response:
    """
    Return the status for a team at an event.
    """
    track_call_after_response("team/event/status", f"{team_key}/{event_key}")

    event_team = EventTeam.get_by_id("{}_{}".format(event_key, team_key))

    status = None
    if event_team is not None:
        status = event_team.status
        if status is not None:
            status_strings = event_team.status_strings
            status.update(
                {  # pyre-ignore[55]
                    "alliance_status_str": status_strings["alliance"],
                    "playoff_status_str": status_strings["playoff"],
                    "overall_status_str": status_strings["overall"],
                }
            )
    return profiled_jsonify(status)


@api_authenticated
@validate_keys
@cached_public
def team_awards(
    team_key: TeamKey,
    year: Optional[int] = None,
) -> Response:
    """
    Returns a list of awards associated with the given Team.
    Optionally only returns events from the specified year.
    """
    if year is None:
        track_call_after_response("team/history/awards", team_key)
        awards = TeamAwardsQuery(team_key=team_key).fetch_dict(ApiMajorVersion.API_V3)
    else:
        track_call_after_response("team/year/awards", f"{team_key}/{year}")
        awards = TeamYearAwardsQuery(team_key=team_key, year=year).fetch_dict(
            ApiMajorVersion.API_V3
        )
    return profiled_jsonify(awards)


@api_authenticated
@validate_keys
@cached_public
def team_matches(
    team_key: TeamKey,
    year: int,
    model_type: Optional[ModelType] = None,
) -> Response:
    """
    Returns a list of matches associated with the given Team in a given year.
    """
    track_call_after_response("team/year/matches", f"{team_key}/{year}", model_type)

    matches = TeamYearMatchesQuery(team_key=team_key, year=year).fetch_dict(
        ApiMajorVersion.API_V3
    )

    if model_type is not None:
        matches = filter_match_properties(matches, model_type)
    return profiled_jsonify(matches)


@api_authenticated
@validate_keys
@cached_public
def team_media_year(team_key: TeamKey, year: int) -> Response:
    """
    Returns a list of media associated with the given Team in a given year.
    """
    track_call_after_response("team/media", f"{team_key}/{year}")

    media = TeamYearMediaQuery(team_key=team_key, year=year).fetch_dict(
        ApiMajorVersion.API_V3
    )
    return profiled_jsonify(media)


@api_authenticated
@validate_keys
@cached_public
def team_media_tag(
    team_key: TeamKey, media_tag: str, year: Optional[int] = None
) -> Response:
    """
    Returns a list of media associated with the given Team with a given tag.
    Optionally filters by year.
    """
    api_label = f"{team_key}/{media_tag}"
    if year is not None:
        api_label += f"/{year}"
    track_call_after_response("team/media/tag", api_label)

    tag_enum = get_enum_from_url(media_tag)
    if tag_enum is None:
        return profiled_jsonify([])

    if year is None:
        media = TeamTagMediasQuery(team_key=team_key, media_tag=tag_enum).fetch_dict(
            ApiMajorVersion.API_V3
        )
    else:
        media = TeamYearTagMediasQuery(
            team_key=team_key, media_tag=tag_enum, year=year
        ).fetch_dict(ApiMajorVersion.API_V3)
    return profiled_jsonify(media)


@api_authenticated
@cached_public
def team_list_all(model_type: Optional[ModelType] = None) -> Response:
    """
    Returns a list of all teams.
    """
    track_call_after_response("team/list", "all", model_type)

    max_team_key = Team.query().order(-Team.team_number).fetch(1, keys_only=True)[0]
    max_team_num = int(max_team_key.id()[3:])
    max_team_page = int(max_team_num / TEAM_PAGE_SIZE)

    futures = []
    for page_num in range(max_team_page + 1):
        futures.append(
            TeamListQuery(page=page_num).fetch_dict_async(ApiMajorVersion.API_V3)
        )

    team_list = []
    for future in futures:
        partial_team_list = future.get_result()
        team_list += partial_team_list

    if model_type is not None:
        team_list = filter_team_properties(team_list, model_type)
    return profiled_jsonify(team_list)


@api_authenticated
@cached_public
def team_list(
    page_num: int, year: Optional[int] = None, model_type: Optional[ModelType] = None
) -> Response:
    """
    Returns a list of teams, paginated by team number in sets of 500.
    Optionally only returns teams that participated in the specified year.
    page_num = 0 returns teams from 0-499
    page_num = 1 returns teams from 500-999
    page_num = 2 returns teams from 1000-1499
    etc.
    """
    api_action = "team/list"
    if year is not None:
        api_action += f"/{year}"
    track_call_after_response(api_action, str(page_num), model_type)

    if year is None:
        team_list = TeamListQuery(page=page_num).fetch_dict(ApiMajorVersion.API_V3)
    else:
        team_list = TeamListYearQuery(year=year, page=page_num).fetch_dict(
            ApiMajorVersion.API_V3
        )

    if model_type is not None:
        team_list = filter_team_properties(team_list, model_type)
    return profiled_jsonify(team_list)
