from backend.api.handlers.decorators import api_authenticated, validate_etag
from backend.api.handlers.helpers.model_properties import (
    filter_event_properties,
    filter_team_properties,
    ModelType,
)
from backend.api.handlers.helpers.profiled_jsonify import (
    profiled_jsonify,
    TypedFlaskResponse,
)
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.decorators import cached_public
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.team import Team
from backend.common.queries.event_query import EventListQuery
from backend.common.queries.team_query import TeamListQuery


# TODO: bump cache time to 1 day after testing/dev is complete
@api_authenticated
@cached_public
@validate_etag
def search_index() -> TypedFlaskResponse[dict]:
    track_call_after_response("search_index", "search_index")

    max_team_key = Team.query().order(-Team.team_number).fetch(1, keys_only=True)[0]
    max_team_num = int(max_team_key.id()[3:])
    max_team_page = int(max_team_num / 500)

    team_futures = []
    # Query up to max_team_page + 1 (i.e. range(max_team_page + 2)).
    # Page max_team_page + 1 is currently empty ([]), but querying it registers its
    # cache key in @validate_etag's accessed_keys. When a new team is created that starts
    # this next page, TeamManipulator invalidates TeamListQuery(max_team_page + 1),
    # which invalidates the ETag and ensures clients receive the new team.
    for page_num in range(max_team_page + 2):
        team_futures.append(
            TeamListQuery(page=page_num).fetch_dict_async(ApiMajorVersion.API_V3)
        )

    event_futures = []
    for year in SeasonHelper.get_valid_years():
        event_futures.append(
            EventListQuery(year=year).fetch_dict_async(ApiMajorVersion.API_V3)
        )

    team_list = []
    for future in team_futures:
        partial_team_list = future.get_result()
        team_list += partial_team_list

    event_list = []
    for future in event_futures:
        partial_event_list = future.get_result()
        event_list += partial_event_list

    event_list = filter_event_properties(event_list, ModelType("search"))
    team_list = filter_team_properties(team_list, ModelType("search"))

    return profiled_jsonify({"events": event_list, "teams": team_list})
