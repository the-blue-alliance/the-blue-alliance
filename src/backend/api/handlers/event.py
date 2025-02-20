from typing import Optional

from flask import Response

from backend.api.handlers.decorators import api_authenticated, validate_keys
from backend.api.handlers.helpers.add_alliance_status import add_alliance_status
from backend.api.handlers.helpers.model_properties import (
    filter_event_properties,
    filter_match_properties,
    filter_team_properties,
    ModelType,
)
from backend.api.handlers.helpers.profiled_jsonify import profiled_jsonify
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.decorators import cached_public
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.playoff_advancement_helper import PlayoffAdvancementHelper
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.keys import EventKey
from backend.common.queries.award_query import EventAwardsQuery
from backend.common.queries.event_details_query import EventDetailsQuery
from backend.common.queries.event_query import (
    EventListQuery,
    EventQuery,
)
from backend.common.queries.match_query import EventMatchesQuery
from backend.common.queries.media_query import EventTeamsMediasQuery
from backend.common.queries.team_query import EventEventTeamsQuery, EventTeamsQuery


@api_authenticated
@validate_keys
@cached_public
def event(event_key: EventKey, model_type: Optional[ModelType] = None) -> Response:
    """
    Returns info about one event, specified by |event_key|.
    """
    track_call_after_response("event", event_key, model_type)

    event = EventQuery(event_key=event_key).fetch_dict(ApiMajorVersion.API_V3)
    if model_type is not None:
        event = filter_event_properties([event], model_type)[0]
    return profiled_jsonify(event)


@api_authenticated
@cached_public
def event_list_all(model_type: Optional[ModelType] = None) -> Response:
    """
    Returns a list of all events.
    """
    track_call_after_response("event/list", "all", model_type)

    futures = []
    for year in SeasonHelper.get_valid_years():
        futures.append(
            EventListQuery(year=year).fetch_dict_async(ApiMajorVersion.API_V3)
        )

    events = []
    for future in futures:
        partial_event_list = future.get_result()
        events += partial_event_list

    if model_type is not None:
        events = filter_event_properties(events, model_type)
    return profiled_jsonify(events)


@api_authenticated
@cached_public
def event_list_year(year: int, model_type: Optional[ModelType] = None) -> Response:
    """
    Returns a list of all events for a given year.
    """
    track_call_after_response("event/list", str(year), model_type)

    events = EventListQuery(year=year).fetch_dict(ApiMajorVersion.API_V3)

    if model_type is not None:
        events = filter_event_properties(events, model_type)
    return profiled_jsonify(events)


@api_authenticated
@validate_keys
@cached_public
def event_detail(event_key: EventKey, detail_type: str) -> Response:
    """
    Returns details about one event, specified by |event_key| and |detail_type|.
    """
    track_call_after_response(f"event/{detail_type}", event_key)

    event_details = EventDetailsQuery(event_key=event_key).fetch_dict(
        ApiMajorVersion.API_V3
    )
    if event_details is None:
        return profiled_jsonify(None)

    detail = event_details.get(detail_type)
    if detail_type == "alliances" and detail:
        add_alliance_status(event_key, detail)

    return profiled_jsonify(detail)


@api_authenticated
@validate_keys
@cached_public
def event_teams(
    event_key: EventKey, model_type: Optional[ModelType] = None
) -> Response:
    """
    Returns a list of teams attending a given event.
    """
    track_call_after_response("event/teams", event_key, model_type)

    teams = EventTeamsQuery(event_key=event_key).fetch_dict(ApiMajorVersion.API_V3)
    if model_type is not None:
        teams = filter_team_properties(teams, model_type)
    return profiled_jsonify(teams)


@api_authenticated
@validate_keys
@cached_public
def event_teams_statuses(event_key: EventKey) -> Response:
    """
    Returns a dict of team_key: status for teams at a given event.
    """
    track_call_after_response("event/teams/statuses", event_key)

    event_teams = EventEventTeamsQuery(event_key=event_key).fetch()
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
        statuses[event_team.team.id()] = status
    return profiled_jsonify(statuses)


@api_authenticated
@validate_keys
@cached_public
def event_teams_media(event_key: EventKey) -> Response:
    track_call_after_response("event/teams/media", event_key)

    query = EventTeamsMediasQuery(event_key=event_key).fetch_dict(
        ApiMajorVersion.API_V3
    )

    return profiled_jsonify(query)


@api_authenticated
@validate_keys
@cached_public
def event_matches(
    event_key: EventKey, model_type: Optional[ModelType] = None
) -> Response:
    """
    Returns a list of matches for a given event.
    """
    track_call_after_response("event/matches", event_key, model_type)

    matches = EventMatchesQuery(event_key=event_key).fetch_dict(ApiMajorVersion.API_V3)
    if model_type is not None:
        matches = filter_match_properties(matches, model_type)
    return profiled_jsonify(matches)


@api_authenticated
@validate_keys
@cached_public
def event_awards(event_key: EventKey) -> Response:
    """
    Returns a list of awards for a given event.
    """
    track_call_after_response("event/awards", event_key)

    awards = EventAwardsQuery(event_key=event_key).fetch_dict(ApiMajorVersion.API_V3)
    return profiled_jsonify(awards)


@api_authenticated
@validate_keys
@cached_public
def event_playoff_advancement(event_key: EventKey) -> Response:
    """
    Returns the playoff advancement for a given event.
    """
    track_call_after_response("event/playoff_advancement", event_key)

    # Fetch data
    event_future = EventQuery(event_key).fetch_async()
    matches_future = EventMatchesQuery(event_key).fetch_async()
    event = event_future.get_result()
    event.prep_details()
    matches = matches_future.get_result()

    # Clean matches
    # TODO: Unify with web handler
    cleaned_matches, _ = MatchHelper.delete_invalid_matches(matches, event)
    _, matches = MatchHelper.organized_matches(cleaned_matches)

    bracket_table = event.playoff_bracket
    playoff_advancement = event.playoff_advancement
    output = PlayoffAdvancementHelper.create_playoff_advancement_response_for_apiv3(
        event, playoff_advancement, bracket_table
    )
    return profiled_jsonify(output)
