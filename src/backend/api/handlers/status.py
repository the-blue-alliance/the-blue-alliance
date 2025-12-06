from typing import cast

from flask import Response

from backend.api.handlers.decorators import api_authenticated
from backend.api.handlers.helpers.profiled_jsonify import profiled_jsonify
from backend.api.handlers.helpers.track_call import track_call_after_response
from backend.common.consts.teams import TEAM_PAGE_SIZE
from backend.common.decorators import cached_public
from backend.common.models.sitevar import Sitevar
from backend.common.models.team import Team
from backend.common.sitevars.apistatus import ApiStatus
from backend.common.sitevars.apistatus_fmsapi_down import ApiStatusFMSApiDown

from backend.common.helpers.season_helper import SeasonHelper

@api_authenticated
@cached_public
def status() -> Response:
    track_call_after_response("status", "status")

    # TODO: Remove Sitevar usage for Sitevar classes
    down_events_sitevar_future = Sitevar.get_by_id_async("apistatus.down_events")

    status = dict()
    status.update(cast(dict, ApiStatus.status()))

    down_events_sitevar = down_events_sitevar_future.get_result()
    down_events_list = down_events_sitevar.contents if down_events_sitevar else None

    status["is_datafeed_down"] = ApiStatusFMSApiDown.get()
    status["down_events"] = down_events_list if down_events_list is not None else []

    max_team_key = Team.query().order(-Team.team_number).fetch(1, keys_only=True)[0]
    max_team_num = int(max_team_key.id()[3:])
    max_team_page = int(max_team_num / TEAM_PAGE_SIZE)

    status["max_team_page"] = max_team_page

    return profiled_jsonify(status)

@api_authenticated
@cached_public
def season() -> Response:
    track_call_after_response("season", "status")

    # TODO: Remove Sitevar usage for Sitevar classes
    down_events_sitevar_future = Sitevar.get_by_id_async("apistatus.down_events")

    season = dict()
    season.update(cast(dict, ApiStatus.status()))
    season.update({"kickoff_time_utc": SeasonHelper.kickoff_datetime_utc(2023)})

    down_events_sitevar = down_events_sitevar_future.get_result()
    down_events_list = down_events_sitevar.contents if down_events_sitevar else None

    season["is_datafeed_down"] = ApiStatusFMSApiDown.get()
    season["down_events"] = down_events_list if down_events_list is not None else []

    return profiled_jsonify(season)
