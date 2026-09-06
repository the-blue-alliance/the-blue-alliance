from typing import Any, Optional

from backend.api.handlers.decorators import (
    api_authenticated,
    validate_etag,
    validate_keys,
)
from backend.api.handlers.helpers.model_properties import (
    filter_event_properties,
    filter_match_properties,
    filter_team_properties,
    ModelType,
)
from backend.api.handlers.helpers.model_query_response import (
    model_query_response,
    models_query_response,
)
from backend.api.handlers.helpers.profiled_jsonify import (
    profiled_jsonify,
    TypedFlaskResponse,
)
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
from backend.common.queries.dict_converters.award_converter import AwardDict
from backend.common.queries.dict_converters.district_converter import DistrictDict
from backend.common.queries.dict_converters.event_converter import EventDict
from backend.common.queries.dict_converters.match_converter import MatchDict
from backend.common.queries.dict_converters.media_converter import MediaDict
from backend.common.queries.dict_converters.robot_converter import RobotDict
from backend.common.queries.dict_converters.team_converter import TeamDict
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
@cached_public
@validate_etag
@validate_keys
def team(
    team_key: TeamKey, model_type: Optional[ModelType] = None
) -> TypedFlaskResponse[TeamDict]:
    """
    Returns details about one team, specified by |team_key|.
    """
    track_call_after_response("team", team_key, model_type)
    return model_query_response(
        TeamQuery(team_key=team_key),
        model_type=model_type,
        filter_func=filter_team_properties,
    )


@api_authenticated
@cached_public
@validate_etag
@validate_keys
def team_history(team_key: TeamKey) -> TypedFlaskResponse[Any]:
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
@cached_public
@validate_etag
@validate_keys
def team_years_participated(team_key: TeamKey) -> TypedFlaskResponse[list[int]]:
    """
    Returns a list of years the given Team participated in an event.
    """
    track_call_after_response("team/years_participated", team_key)

    years_participated = TeamParticipationQuery(team_key=team_key).fetch()
    years_participated = sorted(years_participated)
    return profiled_jsonify(years_participated)


@api_authenticated
@cached_public
@validate_etag
@validate_keys
def team_history_districts(team_key: TeamKey) -> TypedFlaskResponse[list[DistrictDict]]:
    """
    Returns a list of all DistrictTeam models associated with the given Team.
    """
    track_call_after_response("team/history/districts", team_key)
    return models_query_response(
        TeamDistrictsQuery(team_key=team_key),
    )


@api_authenticated
@cached_public
@validate_etag
@validate_keys
def team_history_robots(team_key: TeamKey) -> TypedFlaskResponse[list[RobotDict]]:
    """
    Returns a list of all Robot models associated with the given Team.
    """
    track_call_after_response("team/history/robots", team_key)
    return models_query_response(
        TeamRobotsQuery(team_key=team_key),
    )


@api_authenticated
@cached_public
@validate_etag
@validate_keys
def team_social_media(team_key: TeamKey) -> TypedFlaskResponse[list[MediaDict]]:
    """
    Returns a list of all social media models associated with the given Team.
    """
    track_call_after_response("team/social_media", team_key)
    return models_query_response(
        TeamSocialMediaQuery(team_key=team_key),
    )


@api_authenticated
@cached_public
@validate_etag
@validate_keys
def team_events(
    team_key: TeamKey,
    year: Optional[int] = None,
    model_type: Optional[ModelType] = None,
) -> TypedFlaskResponse[list[EventDict]]:
    """
    Returns a list of all event models associated with the given Team.
    Optionally only returns events from the specified year.
    """
    api_action = "team/events"
    if year is not None:
        api_action += f"/{year}"
    track_call_after_response(api_action, team_key, model_type)

    query = (
        TeamEventsQuery(team_key=team_key)
        if year is None
        else TeamYearEventsQuery(team_key=team_key, year=year)
    )
    return models_query_response(
        query,
        model_type=model_type,
        filter_func=filter_event_properties,
    )


@api_authenticated
@cached_public
@validate_etag
@validate_keys
def team_events_statuses_year(team_key: TeamKey, year: int) -> TypedFlaskResponse[dict]:
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
            status_dict = status.copy()
            status_dict.update(
                {  # pyre-ignore[55]
                    "alliance_status_str": status_strings["alliance"],
                    "playoff_status_str": status_strings["playoff"],
                    "overall_status_str": status_strings["overall"],
                }
            )
            statuses[event_team.event.id()] = status_dict
        else:
            statuses[event_team.event.id()] = status
        pit_location = event_team.pit_location
        if pit_location:
            if statuses[event_team.event.id()] is None:
                statuses[event_team.event.id()] = {}
            statuses[event_team.event.id()]["pit_location"] = pit_location["location"]
    return profiled_jsonify(statuses)


@api_authenticated
@cached_public
@validate_etag
@validate_keys
def team_event_matches(
    team_key: TeamKey, event_key: EventKey, model_type: Optional[ModelType] = None
) -> TypedFlaskResponse[list[MatchDict]]:
    """
    Returns a list of matches for a team at an event.
    """
    track_call_after_response(
        "team/event/matches", f"{team_key}/{event_key}", model_type
    )
    return models_query_response(
        TeamEventMatchesQuery(team_key=team_key, event_key=event_key),
        model_type=model_type,
        filter_func=filter_match_properties,
    )


@api_authenticated
@cached_public
@validate_etag
@validate_keys
def team_event_awards(
    team_key: TeamKey, event_key: EventKey
) -> TypedFlaskResponse[list[AwardDict]]:
    """
    Returns a list of awards for a team at an event.
    """
    track_call_after_response("team/event/awards", f"{team_key}/{event_key}")
    return models_query_response(
        TeamEventAwardsQuery(team_key=team_key, event_key=event_key),
    )


@api_authenticated
@cached_public
@validate_etag
@validate_keys
def team_event_status(
    team_key: TeamKey, event_key: EventKey
) -> TypedFlaskResponse[Any]:
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
        pit_location = event_team.pit_location
        if pit_location:
            if status is None:
                status = {}
            status["pit_location"] = pit_location["location"]  # pyre-ignore[27]
    return profiled_jsonify(status)


@api_authenticated
@cached_public
@validate_etag
@validate_keys
def team_awards(
    team_key: TeamKey,
    year: Optional[int] = None,
) -> TypedFlaskResponse[list[AwardDict]]:
    """
    Returns a list of awards associated with the given Team.
    Optionally only returns events from the specified year.
    """
    if year is None:
        track_call_after_response("team/history/awards", team_key)
        query = TeamAwardsQuery(team_key=team_key)
    else:
        track_call_after_response("team/year/awards", f"{team_key}/{year}")
        query = TeamYearAwardsQuery(team_key=team_key, year=year)
    return models_query_response(query)


@api_authenticated
@cached_public
@validate_etag
@validate_keys
def team_matches(
    team_key: TeamKey,
    year: int,
    model_type: Optional[ModelType] = None,
) -> TypedFlaskResponse[list[MatchDict]]:
    """
    Returns a list of matches associated with the given Team in a given year.
    """
    track_call_after_response("team/year/matches", f"{team_key}/{year}", model_type)
    return models_query_response(
        TeamYearMatchesQuery(team_key=team_key, year=year),
        model_type=model_type,
        filter_func=filter_match_properties,
    )


@api_authenticated
@cached_public
@validate_etag
@validate_keys
def team_media_year(
    team_key: TeamKey, year: int
) -> TypedFlaskResponse[list[MediaDict]]:
    """
    Returns a list of media associated with the given Team in a given year.
    """
    track_call_after_response("team/media", f"{team_key}/{year}")
    return models_query_response(TeamYearMediaQuery(team_key=team_key, year=year))


@api_authenticated
@cached_public
@validate_etag
@validate_keys
def team_media_tag(
    team_key: TeamKey, media_tag: str, year: Optional[int] = None
) -> TypedFlaskResponse[list[MediaDict]]:
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

    query = (
        TeamTagMediasQuery(team_key=team_key, media_tag=tag_enum)
        if year is None
        else TeamYearTagMediasQuery(team_key=team_key, media_tag=tag_enum, year=year)
    )
    return models_query_response(query)


@api_authenticated
@cached_public
@validate_etag
def team_list_all(
    model_type: Optional[ModelType] = None,
) -> TypedFlaskResponse[list[TeamDict]]:
    """
    Returns a list of all teams.
    """
    track_call_after_response("team/list", "all", model_type)

    max_team_key = Team.query().order(-Team.team_number).fetch(1, keys_only=True)[0]
    max_team_num = int(max_team_key.id()[3:])
    max_team_page = int(max_team_num / TEAM_PAGE_SIZE)

    futures = []
    # Query up to max_team_page + 1 (i.e. range(max_team_page + 2)).
    # Page max_team_page + 1 is currently empty ([]), but querying it registers its
    # cache key in @validate_etag's accessed_keys. When a new team is created that starts
    # this next page, TeamManipulator invalidates TeamListQuery(max_team_page + 1),
    # which invalidates the ETag and ensures clients receive the new team.
    for page_num in range(max_team_page + 2):
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
@validate_etag
def team_list(
    page_num: int, year: Optional[int] = None, model_type: Optional[ModelType] = None
) -> TypedFlaskResponse[list[TeamDict]]:
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

    query = (
        TeamListQuery(page=page_num)
        if year is None
        else TeamListYearQuery(year=year, page=page_num)
    )
    return models_query_response(
        query,
        model_type=model_type,
        filter_func=filter_team_properties,
    )
